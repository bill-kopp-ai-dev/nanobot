"""Operações básicas sobre notas: ``notes_read`` / ``notes_write`` /
``notes_search`` / ``notes_delete``.

CAS duplo (D47): ``notes_write`` aceita ``expected_content_hash`` E
``expected_body_hash`` independentemente. Resolve o conflito agente↔humano:

- Agente enriquece só o frontmatter (summary, tags) durante a noite.
- Humano mexe só no body de manhã.
- Hash único do arquivo = conflito espúrio para os dois.
- ``expected_body_hash`` correto + frontmatter mudou = agente sobrescreve
  só o frontmatter sem perder a edição humana do body.
- ``expected_content_hash`` correto = humano sobrescreve tudo (mesma
  semântica do CAS clássico).

Escrita atômica (IMPL-collective §2.7): temp-file no mesmo diretório +
``fsync`` + ``os.replace`` + ``fsync`` do diretório pai. Garante que um
leitor concorrente nunca observa arquivo parcial ou
``FileNotFoundError`` transiente durante o rename — DoD de P2.

Ordem canônica de commit (IMPL-collective §2.6): ``append_log`` ANTES
de ``commit_paths``, e ``log.md`` entra na MESMA lista de paths do
commit — assim o sha da linha de log referencia o commit ANTERIOR sem
dependência circular, e ``log.md`` nunca fica como diff sujo.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .envelope import UntrustedNote
from .errors import CASMismatchError, ZettelError
from .frontmatter import extract_links, serialize, split_frontmatter
from .gitstore import GitStore
from .lock import BundleLock
from .paths import BundleLayout
from .schema import ID_PATTERN, ZettelFrontmatter, validate_frontmatter

_ID_RE = re.compile(ID_PATTERN)


def _validate_id_or_raise(id: str, *, code: str) -> None:
    """Recusa ``id`` que não bate ``YYYYMMDD-HHMMSS`` ANTES de qualquer uso
    em filesystem glob.

    ``notes_read``/``notes_delete`` constroem
    ``notes.glob(f"{id}-*{ext}")`` a partir de ``id``. ``Path.glob``
    resolve componentes ``..`` do padrão como navegação de diretório real
    (não como texto literal) — sem esta guarda, ``id="../../algo"``
    escapa de ``notes/`` e lê/apaga arquivos fora do bundle,
    contornando inteiramente a barreira ``paths.resolve_safe_path``
    (que nunca é chamada por este módulo). ``WriteRequest.id`` já é
    protegido via ``Field(pattern=...)`` no pydantic; ``notes_read`` e
    ``notes_delete`` recebem ``id`` como ``str`` solto (sem model) e
    ficavam sem a mesma proteção. Bug encontrado na revisão
    2026-07-30 (4º ciclo, okf-bundle-core).
    """
    if not _ID_RE.match(id):
        raise ZettelError(
            f"id inválido (esperado YYYYMMDD-HHMMSS): {id!r}",
            code=code,
        )


# Sentinel pra distinguir "não tentamos capturar o log.md anterior" /
# "tentamos e a leitura falhou" de "log.md não existia" (``None`` é um
# valor legítimo nesse segundo caso). Usado pelo rollback de
# ``notes_write``/``notes_delete`` — ver comentário nos respectivos
# blocos ``except``.
_UNKNOWN_LOG_STATE = object()


# Whitelist de chaves que ``WriteRequest.frontmatter_patch`` pode tocar.
# ``generated`` e ``id`` não podem ser patcheados — o primeiro é mantido
# por ``notes_write`` (auditoria de quem/quando), e o segundo é o
# identificador da nota. ``type`` também não (mover de Note para Skill
# não é "edit", é uma migração que P5+ deve tratar como operação
# separada).
_PATCHABLE_KEYS = frozenset(
    {
        "title",
        "description",
        "tags",
        "resource",
        "verified",
        "status",
        "stale_after",
        "sources",
        "usage_window",
        "supersedes",
        "derived_from",
        "summary",
        "attachments",
        # P11: os quatro campos de policy operacional. Sem eles aqui,
        # ``notes_write`` rejeita o patch e nenhuma das tools novas
        # consegue gravar (verificado antes da implementação: o patch
        # ``{"protected": True}`` levantava ``notes_write_patch_forbidden_key``).
        #
        # Nota sobre ``_ENRICH_SENSITIVE_KEYS`` (percival-collective-memory):
        # os dois sets têm propósitos distintos e interseção PARCIAL — este
        # diz o que qualquer caller pode patchar; aquele é uma asserção sobre
        # o que o enricher jamais monta. ``id``/``type``/``generated`` estão
        # naquele e não neste. Não existe relação de subconjunto entre eles,
        # apesar do que a v1 da proposta P11 afirmava.
        "protected",
        "lifecycle",
        "cooled_at",
        "review",
    }
)


def _slug_from_body(body: str) -> str:
    """Extrai primeiro slug razoável do body pra nome de arquivo.

    NOTA de arquitetura (IMPL-collective §3.3, registrada na revisão §0
    do plano): em produção, este slug deve ser gerado em ``ops.py`` (o
    consumidor), não no core. Mantido aqui P2 só pra fechar o
    happy-path de ``notes_write`` quando não há arquivo existente;
    mover para ``percival_collective_memory.tools._slug`` em P3+.
    """
    for line in body.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            slug = re.sub(r"[^a-z0-9]+", "-", line.lower())[:50].rstrip("-")
            if slug:
                return slug
    return "untitled"


def _write_atomic(path: Path, text: str) -> None:
    """Escreve ``text`` em ``path`` via temp-file + fsync + ``os.replace``.

    Garante que um leitor concorrente (``rg notes_search``, humano com
    o arquivo aberto) nunca observa arquivo truncado ou
    ``FileNotFoundError`` transiente. O ``fsync`` do diretório pai
    garante que o rename sobrevive a crash do SO — sem ele, o rename
    pode ficar apenas no page cache e se perder num reboot.

    Bug fix 2026-07-30 ocli-review-3: a versão anterior usava temp
    file de nome FIXO ``.<name>.tmp``. Dois writers concorrentes ao
    MESMO path (mesmo que normalmente impossível dentro do
    ``BundleLock``) faziam o segundo thread sobrescrever o temp do
    primeiro via ``O_TRUNC``, e o primeiro ``os.replace`` propaga
    ``FileNotFoundError``. Agora usamos ``tempfile.mkstemp`` para
    gerar nome único, mesmo em escritas concorrentes. O
    ``notes_write``/``notes_delete`` continuam sob ``BundleLock`` —
    este fix é defense-in-depth para callers fora do lock (testes,
    scripts, importers).

    Permissões: ``tempfile.mkstemp`` cria arquivos com ``0600``. Se o
    arquivo destino já existe, copiamos o modo dele antes do
    ``os.replace`` para preservar bits legíveis por outros processos
    (ex.: nginx servindo o bundle); sem isso, cada escrita regrediria
    silenciosamente para ``0600``.
    """
    fd, tmp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    if path.exists():
        try:
            shutil.copymode(path, tmp)
        except OSError:
            # Filesystem without mode bits (e.g. some Windows); skip silently.
            pass
    try:
        os.replace(tmp, path)
    except Exception:
        # Se o rename falhar (e.g. disco cheio), o temp fica órfão.
        # Limpar para não acumular lixo. O fix contra órfãos vai
        # além do escopo deste review.
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    # fsync do diretório pai — rename durável.
    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


# Alias público para outros pacotes (P5/percival-acquire-knowledge em diante)
# usarem sem depender do prefixo ``_``. ``_write_atomic`` é privado por
# convenção; reexportar mantém a regra sem expor o nome privado.
write_atomic = _write_atomic


@dataclass
class ReadResult:
    """O que ``notes_read`` devolve pro tool layer.

    Inclui ambos os hashes (D47) pra que o chamador saiba se a nota
    mudou entre o read e o write. ``backlinks`` é a lista de IDs de
    notas que apontam pra esta — útil pra UI e pra detectar impacto.
    """

    id: str
    path: Path
    frontmatter: ZettelFrontmatter
    body: str
    content_hash: str  # sha256 do frontmatter+body completo
    body_hash: str  # sha256 só do body
    backlinks: list[str]
    raw: UntrustedNote
    is_fresh: bool = True


class WriteRequest(BaseModel):
    """Args de ``notes_write``.

    ``extra='forbid'`` no Pydantic + whitelist manual no ``frontmatter_patch``
    impede que um caller malicioso (LLM injection, importer bugado) troque
    ``id``, ``type`` ou ``generated`` via patch.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^\d{8}-\d{6}$")
    body: str
    frontmatter_patch: dict | None = None  # merge sobre frontmatter atual
    expected_content_hash: str | None = None  # CAS — content
    expected_body_hash: str | None = None  # CAS — body
    reason: str = "edit"


@dataclass
class WriteResult:
    id: str
    path: Path
    content_hash: str
    body_hash: str
    new_frontmatter: ZettelFrontmatter
    revision_diff: list[str] = field(default_factory=list)


# -------------------- read --------------------


def note_content_hash(root: Path, layout: BundleLayout, id: str) -> str:
    """``content_hash`` de uma nota sem pagar o custo de ``notes_read``.

    ``notes_read`` gasta a maior parte do tempo em ``_find_backlinks``, que
    varre o bundle inteiro (~1,2s em 286 notas). Quem só precisa saber "este
    arquivo mudou?" — comparação de CAS, detecção de no-op em lote — paga
    varredura que não usa.

    Aqui é glob + ``sha256`` do texto, o mesmo valor que
    ``ReadResult.content_hash`` carrega. Sem validação de frontmatter: quem
    quiser a nota tipada continua chamando ``notes_read``.

    **Lê em modo TEXTO, não em bytes.** ``notes_read`` hasheia
    ``UntrustedNote.raw_text``, que vem de ``path.read_text(encoding="utf-8")``
    — e o modo texto do Python aplica *universal newlines*, traduzindo
    ``\\r\\n`` para ``\\n`` antes do hash. Ler bytes aqui daria um digest
    diferente para qualquer arquivo com CRLF (nota vinda de editor Windows,
    de migração de vault, de patch mal aplicado), e os dois hashes deixariam
    de ser comparáveis exatamente nos arquivos em que a comparação importa.
    Bug encontrado na revisão de 2026-08-09, coberto por
    ``test_note_content_hash_bate_com_notes_read_em_arquivo_crlf``.

    Levanta os mesmos erros de resolução de id que ``notes_read``
    (``FileNotFoundError``, ``ZettelError`` para id ambíguo ou malformado).
    """
    _validate_id_or_raise(id, code="notes_read_invalid_id")
    notes = root / layout.notes_dir
    matches = list(notes.glob(f"{id}-*{layout.notes_extension}"))
    if not matches:
        raise FileNotFoundError(f"no note with id {id} in {notes}")
    if len(matches) > 1:
        raise ZettelError(
            f"multiple notes with id {id}: {[m.name for m in matches]}",
            code="notes_read_duplicate_id",
        )
    raw = matches[0].read_text(encoding="utf-8")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def notes_read(
    root: Path,
    layout: BundleLayout,
    id: str,
    *,
    gitstore: GitStore | None = None,
) -> ReadResult:
    """Lê nota pelo id. Retorna ``ReadResult`` com hashes + backlinks.

    Lança ``FileNotFoundError`` se id não existe, ``ZettelError`` se
    frontmatter está inválido ou múltiplos arquivos batem o id
    (id ambíguo é sintoma de bug upstream — duplicação no ``## Links``
    ou dois imports) ou se ``id`` não bate o formato canônico
    (``notes_read_invalid_id`` — ver ``_validate_id_or_raise``).

    Também rejeita o caso em que o id do NOME DO ARQUIVO diverge do
    ``frontmatter.id`` (``notes_read_id_mismatch``). Os dois são chaves da
    mesma nota em camadas diferentes: o arquivo é encontrado pelo glob do
    nome, mas ``build_graph`` monta o nó a partir de ``fm.id``. Divergindo,
    a nota vira um nó inalcançável — todo wikilink para o id do arquivo
    aponta para um alvo que não existe no grafo, e o sintoma chega como
    "aresta dangling", que atribui a culpa a quem escreveu o link em vez de
    à nota corrompida. Nenhuma escrita pelo core produz esse estado
    (``id`` não é patchável e é preservado no merge de frontmatter); ele só
    aparece em nota criada por fora — import, migração, edição manual.
    Verificado em 2026-08-09: 0 ocorrências nos dois bundles reais.
    """
    _validate_id_or_raise(id, code="notes_read_invalid_id")
    if gitstore is None:
        gitstore = GitStore(root, layout)
        gitstore.ensure_repo()

    notes = root / layout.notes_dir
    matches = list(notes.glob(f"{id}-*{layout.notes_extension}"))
    if not matches:
        raise FileNotFoundError(f"no note with id {id} in {notes}")
    if len(matches) > 1:
        raise ZettelError(
            f"multiple notes with id {id}: {[m.name for m in matches]}",
            code="notes_read_duplicate_id",
        )
    path = matches[0]
    envelope = UntrustedNote.from_file(path)
    fm, errors = validate_frontmatter(envelope.frontmatter.raw)
    if fm is None:
        raise ZettelError(
            f"frontmatter inválido em {path.name}: {[e.message for e in errors]}",
            code="notes_read_invalid_frontmatter",
        )
    if fm.id and fm.id != id:
        raise ZettelError(
            f"id divergente em {path.name}: nome do arquivo diz {id!r}, "
            f"frontmatter diz {fm.id!r} — a nota seria um nó inalcançável no grafo",
            code="notes_read_id_mismatch",
        )

    backlinks = _find_backlinks(root, layout, id)
    content_hash = hashlib.sha256(envelope.raw_text.encode("utf-8")).hexdigest()
    body_hash = hashlib.sha256(envelope.body.encode("utf-8")).hexdigest()

    return ReadResult(
        id=id,
        path=path,
        frontmatter=fm,
        body=envelope.body,
        content_hash=content_hash,
        body_hash=body_hash,
        backlinks=backlinks,
        raw=envelope,
    )


def _find_backlinks(root: Path, layout: BundleLayout, target_id: str) -> list[str]:
    """Varre ``notes/`` e devolve os IDs de notas que linkam pra ``target_id``.

    Aceita como link: ``[[id]]``, ``[[id|label]]``, ``[t](id)``, ``[t](id.md)``.
    Wikilinks em code fence / code inline são ignorados por
    ``extract_links`` (P1).
    """
    notes = root / layout.notes_dir
    if not notes.exists():
        return []
    out: list[str] = []
    for p in sorted(notes.glob(f"*{layout.notes_extension}")):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            _, body = split_frontmatter(text)
        except ZettelError:
            # YAML malformado — pular nota individualmente (mesma
            # política do ``graph.py``). Fix 2026-07-30 ocli-review-2.
            continue
        for link in extract_links(body):
            t = link.target.split("|", 1)[0].strip()
            t = re.sub(r"\.md$", "", t)
            if t == target_id:
                # extrai o id desta nota (YYYYMMDD-HHMMSS) do nome de arquivo
                from_id = p.stem.split("-", 2)
                out.append("-".join(from_id[:2]))
                break
    return sorted(set(out))


# -------------------- write (CAS duplo) --------------------


def notes_write(
    root: Path | str,
    layout: BundleLayout,
    req: WriteRequest,
    *,
    gitstore: GitStore | None = None,
) -> WriteResult:
    """Escreve nota com CAS duplo (D47).

    Semântica:

    - Se ``expected_content_hash`` foi passado e o conteúdo atual do
      arquivo não bate → ``CASMismatchError``.
    - Se ``expected_body_hash`` foi passado e o body atual não bate →
      ``CASMismatchError`` — MESMO se o frontmatter mudou.
    - Se ambos ausentes, write é incondicional.

    Fluxo (sob lock exclusivo):

    1. Lock (``BundleLock``)
    2. Lê estado atual (se existe)
    3. Verifica CAS (se algum hash esperado foi passado)
    4. Merge frontmatter (``current + patch`` + ``generated.at`` novo)
    5. Serializa + escreve atomicamente
    6. ``append_log`` (path devolvido entra no MESMO commit)
    7. ``commit_paths([nota, log.md], ...)``
    8. Re-lê para devolver novos hashes

    Aceita ``Path`` ou ``str`` para ``root``. Fix 2026-07-30
    ocli-review-2: a versão anterior declarava ``root: Path`` mas
    operações como ``BundleLock(root, ...)`` (internamente) e
    ``root / layout.notes_dir`` falhavam se o caller passasse ``str``.
    Inconsistência de assinatura da camada core — todos os demais
    entrypoints do CM/AK/HTTP passam string.
    """
    root = Path(root)
    if gitstore is None:
        gitstore = GitStore(root, layout)
        gitstore.ensure_repo()

    with BundleLock(root, layout, exclusive=True, timeout=30.0):
        # 2) Read current state
        try:
            current = notes_read(root, layout, req.id, gitstore=gitstore)
            current_path = current.path
        except FileNotFoundError:
            current = None
            current_path = root / layout.notes_dir / f"{req.id}-{_slug_from_body(req.body)}.md"

        # 3) CAS check
        if current is not None:
            if req.expected_content_hash and current.content_hash != req.expected_content_hash:
                raise CASMismatchError(
                    f"content_hash mismatch: "
                    f"expected={req.expected_content_hash[:12]}..., "
                    f"actual={current.content_hash[:12]}..."
                )
            if req.expected_body_hash and current.body_hash != req.expected_body_hash:
                raise CASMismatchError(
                    f"body_hash mismatch: "
                    f"expected={req.expected_body_hash[:12]}..., "
                    f"actual={current.body_hash[:12]}..."
                )

        # 4) Merge frontmatter. ``exclude_unset=True`` (e não ``False``)
        # é essencial aqui: ``current.frontmatter`` tem defaults via
        # ``default_factory=list`` em tags/sources/supersedes/derived_from/
        # attachments. Sem o filtro, o ``model_dump`` retorna essas listas
        # vazias, e elas viram campos "set" ao reconstruir o model no
        # construtor abaixo — vazando no YAML durante updates e poluindo
        # o diff do git com lixo (``sources: []``, ``supersedes: []`` etc.).
        if current is not None:
            new_fm_data = dict(
                current.frontmatter.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
            )
        else:
            new_fm_data = {"type": "Note", "id": req.id}
        if req.frontmatter_patch:
            for k, v in req.frontmatter_patch.items():
                if k not in _PATCHABLE_KEYS:
                    raise ZettelError(
                        f"frontmatter_patch não pode alterar {k!r} "
                        f"(whitelist: {sorted(_PATCHABLE_KEYS)})",
                        code="notes_write_patch_forbidden_key",
                    )
                new_fm_data[k] = v
        # ``generated`` é sempre reescrito — auditoria de quem/quando
        # (IMPL-collective §2.4).
        new_fm_data["generated"] = {
            "by": "agent:percival" if current is None else "agent:percival:edit",
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        # Valida antes de serializar — falha aqui vira ZettelError legível.
        new_fm = ZettelFrontmatter(**new_fm_data)

        # 5) Resolve path & serialize & write atomicamente
        # Lemos o conteúdo atual ANTES do _write_atomic — vai ser o alvo
        # do rollback se append_log/commit_paths falharem. Sem isso, ler
        # o arquivo DEPOIS do _write_atomic daria o novo conteúdo, e o
        # rollback seria um no-op silencioso (nota fica atualizada,
        # estado inconsistente).
        current_path.parent.mkdir(parents=True, exist_ok=True)
        previous_text: str | None = (
            current_path.read_text(encoding="utf-8") if current_path.exists() else None
        )
        new_text = serialize(new_fm, req.body)
        _write_atomic(current_path, new_text)

        # 6) append_log + commit_paths. Se QUALQUER um falhar (disco cheio,
        # permissão negada no log.md, git corrompido), revertemos a escrita
        # atômica — sem isso, ficaríamos com nota atualizada no disco e git
        # fora de sync (estado inconsistente que vira diff sujo permanente).
        # ``_write_atomic`` é atômico, então o caminho todo é "nota antiga
        # OU nota nova", nunca intermediário.
        log_file = root / "log.md"
        previous_log_text: object = _UNKNOWN_LOG_STATE
        try:
            # Captura o conteúdo anterior de log.md AQUI DENTRO do try (não
            # antes do ``_write_atomic`` acima) — ``append_log`` escreve
            # antes de sabermos se ``commit_paths`` vai dar certo, então
            # precisamos do estado anterior pra reverter. Colocar essa
            # leitura ANTES do try (bug de uma revisão anterior desta mesma
            # correção) significava que, se a leitura em SI falhasse (ex.:
            # log.md sem permissão — exatamente o cenário que
            # ``test_notes_write_rollback_se_append_log_falha`` simula), a
            # exceção escapava do try/except inteiro e o rollback da NOTA
            # (```_write_atomic`` acima) nunca acontecia — a nota ficava
            # com o corpo novo gravado mesmo a operação inteira tendo
            # "falhado" do ponto de vista do caller.
            previous_log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else None
            log_path = gitstore.append_log(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "kind": new_fm.type,
                    "op": "write",
                    "path": str(current_path.relative_to(root)),
                    "by": "agent:percival",
                    "note": req.reason,
                }
            )
            commit_msg = (
                f"mem(percival): write {req.id} — {req.reason}\n"
                f"\nPath: {current_path.relative_to(root)}"
            )
            gitstore.commit_paths([current_path, log_path], commit_msg)
        except Exception:
            # Rollback da escrita atômica: se a nota existia, restaura o
            # conteúdo anterior; se era nova, remove o arquivo. Re-raise
            # para o caller saber que falhou — o estado é consistente.
            if previous_text is None:
                try:
                    current_path.unlink()
                except FileNotFoundError:
                    pass
            else:
                _write_atomic(current_path, previous_text)
            # Rollback de log.md — só se conseguimos capturar o estado
            # anterior (ver comentário acima). Se a própria leitura falhou,
            # não sabemos o que havia lá antes e não há como reverter com
            # segurança (a nota já foi revertida acima, que é o que importa
            # pro caller — log.md nesse caso raro fica como está).
            if previous_log_text is not _UNKNOWN_LOG_STATE:
                if previous_log_text is None:
                    try:
                        log_file.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    _write_atomic(log_file, previous_log_text)
            raise

        # 7) Re-read (sem lock — re-read é só pra devolver os hashes novos)
        new = notes_read(root, layout, req.id, gitstore=gitstore)

    return WriteResult(
        id=req.id,
        path=new.path,
        content_hash=new.content_hash,
        body_hash=new.body_hash,
        new_frontmatter=new.frontmatter,
        revision_diff=[],
    )


# -------------------- search --------------------


def notes_search(
    root: Path,
    layout: BundleLayout,
    query: str,
    *,
    limit: int = 20,
    kind: str | None = None,
) -> list[dict]:
    """Busca case-insensitive em ``notes/*.md`` via ``rg``.

    Sem índice — escala OK até ~10k notas. P4+ pode adicionar índice se
    a busca virar gargalo. ``rg`` é dep de runtime; se não estiver
    instalado, levanta ``FileNotFoundError`` (fail-fast — não silenciar).

    ``kind`` filtra o filetype do rg (``"md"`` é o caso comum; ``None``
    desabilita). Com o layout OKF atual, todas as notas são ``.md`` então
    o filtro é redundante — mas a flag existe para paridade com o plano
    §3.4 e para evolução futura (e.g., quando ``diary/`` tiver ``.org``).
    """
    if not query:
        return []
    notes = root / layout.notes_dir
    if not notes.exists():
        return []
    # CM-UX-W1-rev2 (2026-07-30): clamp defensivo de ``limit``. O core
    # NAO barra valores invalidos -- ``limit<=0`` resulta em early-stop
    # silencioso (caller nao recebe erro, recebe 0 hits) e
    # ``limit=999999`` aloca a lista de hits inteira antes do rg
    # terminar, pagando latencia. Clamp em 1..200 antes de chamar rg.
    if limit < 1:
        limit = 1
    elif limit > 200:
        limit = 200
    # Guard explícito: ``rg`` (ripgrep) é dep externa de runtime. Sem ele o
    # subprocesso POSIX devolve ``[Errno 2] ENOENT`` — falha que chega cru ao
    # usuário. Levantamos um erro auto-explicativo em vez disso, com a instrução
    # de install por plataforma. Ver issue
    # ``2026-07-29-collective-memory-and-acquire-knowledge-probe.md`` §2.6.
    rg_bin = shutil.which("rg")
    if rg_bin is None:
        raise ZettelError(
            "notes_search requer o binário 'rg' (ripgrep) no PATH. "
            "Instale via 'apt-get install ripgrep' (Debian/Ubuntu), "
            "'brew install ripgrep' (macOS), ou inclua-o no Dockerfile "
            "do nanobot (linha apt-get install).",
            code="notes_search_ripgrep_missing",
        )
    args = [
        rg_bin,
        "--no-heading",
        "--line-number",
        "-i",
        # ``--fixed-strings`` faz a query ser tratada como literal, não
        # regex. Sem isso, buscar ``foo|bar`` casa "foo OU bar" (regex
        # alternation), e ``(a)`` casa o grupo "a" — confuso para
        # usuários que esperam busca textual. Quem quiser regex pode usar
        # ``rg`` direto; a API de notas aqui é busca por substring.
        "--fixed-strings",
    ]
    if kind is not None:
        # rg ``--type`` aceita aliases (``md``, ``markdown``, etc.). O
        # ``--`` garante que mesmo se ``kind`` começar com ``-`` (input
        # hostil), não vai ser interpretado como flag.
        args.extend(["--type", kind])
    args.extend(["--", query, str(notes)])
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        # rg não instalado — propaga pra UI decidir.
        raise
    except subprocess.TimeoutExpired as exc:
        # ``rg`` travou (>10s). Em vez de morrer com traceback, devolve
        # o que temos até o momento — caller pode retry com query
        # mais específica. Aqui devolvemos lista vazia + stderr no log.
        raise ZettelError(
            f"rg timeout em {notes} (query={query!r}, partial={exc.output!r})",
            code="notes_search_ripgrep_timeout",
        ) from exc
    # ``rg`` retorna rc 0 (matches), 1 (no matches), ou >=2 (erro: regex
    # inválida, permission denied, type desconhecido). Sem o check, um erro
    # do rg seria silenciosamente tratado como "sem matches" e o caller
    # não saberia que algo falhou. ``kind`` inválido é o caso mais comum:
    # o usuário passou ``kind="--help"`` por engano, ou um caller passou
    # ``"markdownz"`` esperando filtro. Antes desse check, ``test_notes_
    # search_kind_input_hostil`` aceitava lista vazia como "sem match" —
    # mas o que aconteceu foi rg reclamando de filetype inválido (rc=2),
    # não ausência de matches.
    if res.returncode >= 2:
        raise ZettelError(
            f"rg falhou (rc={res.returncode}) em {notes}: stderr={res.stderr.strip()[:500]!r}",
            code="notes_search_ripgrep_failed",
        )
    out: list[dict] = []
    for line in res.stdout.splitlines():
        if not line:
            continue
        # rg com path absoluto emite "<path>:<lineno>:<texto>". O ``:`` do
        # texto é problema se o match contém dois-pontos, mas rg escapa
        # com ``rstrip`` e nosso split com ``maxsplit=2`` preserva o resto.
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path_str, ln, text = parts
        path = Path(path_str)
        if not path.is_relative_to(notes):
            # Match em path que não é nota (ex.: ``log.md`` no mesmo dir) —
            # filtra. ``notes_search`` é só pra notas.
            continue
        # Filtra por extensão — ``notes/`` pode conter ``.txt``, ``.swp`` ou
        # outros artefatos (em backups via VIM, downloads) que não são notas.
        if path.suffix != layout.notes_extension:
            continue
        # Parse defensivo do line number: rg deve emitir inteiro decimal, mas
        # um rg malformado/binário corrompido emitiria algo que levantaria
        # ``ValueError`` em ``int()`` e mataria o search inteiro. Pular a linha
        # malformada é mais seguro — o caller recebe os resultados válidos.
        try:
            line_no = int(ln)
        except ValueError:
            continue
        from_id = path.stem.split("-", 2)
        out.append(
            {
                "id": "-".join(from_id[:2]),
                "path": str(path.relative_to(root)),
                "line": line_no,
                "snippet": text[:200],
            }
        )
        if len(out) >= limit:
            break
    return out


# -------------------- delete --------------------


def notes_delete(
    root: Path,
    layout: BundleLayout,
    id: str,
    *,
    gitstore: GitStore | None = None,
    reason: str = "delete",
) -> Path:
    """Remove nota do bundle (com lock + commit + log).

    Devolve o path do arquivo removido. Não há CAS — delete é
    idempotente (``FileNotFoundError`` se já não existe). Lança
    ``ZettelError`` (``notes_delete_invalid_id``) se ``id`` não bate o
    formato canônico — ver ``_validate_id_or_raise``.
    """
    _validate_id_or_raise(id, code="notes_delete_invalid_id")
    if gitstore is None:
        gitstore = GitStore(root, layout)
        gitstore.ensure_repo()

    with BundleLock(root, layout, exclusive=True, timeout=30.0):
        notes = root / layout.notes_dir
        matches = list(notes.glob(f"{id}-*{layout.notes_extension}"))
        if not matches:
            raise FileNotFoundError(f"no note with id {id} in {notes}")
        if len(matches) > 1:
            raise ZettelError(
                f"multiple notes with id {id}: {[m.name for m in matches]}",
                code="notes_delete_duplicate_id",
            )
        path = matches[0]
        # Lê o type ANTES de apagar — precisamos dele pra coluna ``kind``
        # do log.md, e depois de ``unlink()`` o arquivo já era.
        try:
            raw_fm, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except ZettelError:
            # YAML quebrado — pula o kind, usa default. Não propaga:
            # o delete é legítimo mesmo em nota malformada, e o
            # ``validate_frontmatter`` no read-write deixou passar.
            # Fix 2026-07-30 ocli-review-2.
            raw_fm = {}
        kind = raw_fm.get("type", "note") if raw_fm else "note"
        # Guardamos o conteúdo ANTES do unlink — se append_log/commit_paths
        # falhar (log.md read-only, disco cheio, git corrompido), restauramos
        # o arquivo. Sem rollback, ficaríamos com nota deletada + log/git
        # desatualizado: o caller (e o git log) não saberia que houve
        # tentativa de delete — diff silencioso permanente.
        previous_text = path.read_text(encoding="utf-8")
        log_file = root / "log.md"
        path.unlink()

        previous_log_text: object = _UNKNOWN_LOG_STATE
        try:
            # Mesmo raciocínio de ``notes_write``: captura o conteúdo
            # anterior de ``log.md`` AQUI DENTRO do try, imediatamente antes
            # do ``append_log`` — se ``commit_paths`` falhar depois, o
            # rollback precisa desfazer os dois (arquivo E log), senão a
            # linha de log de um delete revertido fica pendurada sem commit
            # e é arrastada pro próximo write bem-sucedido (auditoria
            # mentirosa). Capturar isso ANTES do try (bug de uma revisão
            # anterior) significava que, se a própria leitura falhasse
            # (log.md sem permissão), a exceção escapava do try/except e o
            # ``except`` que restaura ``path`` (via ``_write_atomic``) nunca
            # rodava — a nota ficava deletada de verdade apesar do caller
            # ver uma exceção "de falha".
            previous_log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else None
            log_path = gitstore.append_log(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "kind": kind,
                    "op": "delete",
                    "path": str(path.relative_to(root)),
                    "by": "agent:percival",
                    "note": reason,
                }
            )
            # Commit só o log.md se a nota já não estava no git — não é o caso
            # comum, mas defensivo. Aqui sempre commitamos os dois.
            gitstore.commit_paths(
                [path, log_path],
                f"mem(percival): delete {id} — {reason}\n\nPath: {path.relative_to(root)}",
            )
        except Exception:
            # Rollback: restaura o arquivo. Re-raise pro caller — estado
            # consistente após a falha.
            _write_atomic(path, previous_text)
            # Rollback de log.md — só se conseguimos capturar o estado
            # anterior (ver comentário acima de ``previous_log_text``).
            if previous_log_text is not _UNKNOWN_LOG_STATE:
                if previous_log_text is None:
                    try:
                        log_file.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    _write_atomic(log_file, previous_log_text)
            raise
        return path
