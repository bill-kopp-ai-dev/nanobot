"""Wrapper fino sobre ``dulwich.porcelain`` com políticas OKF.

O ``nanobot.utils.gitstore.GitStore`` do predecessor só expõe
``auto_commit(message)`` (que commita uma lista fixa de ``tracked_files``
do construtor — não aceita paths por chamada). Esta classe não herda
daquela: usa ``dulwich.porcelain`` diretamente com a política do nanobot
como referência de design (autor parametrizável, ``porcelain.add``
restrito a paths explícitos, nunca ``add -A``).

Políticas OKF aplicadas:

- ``commit_paths`` recusa paths sob ``layout.inbox_parent`` — no AK isso é
  ``sources/`` (D33: arquivos brutos vão pro restic, não pro git).
- ``append_log`` escreve em ``log.md`` e devolve o path pra entrar na MESMA
  lista do ``commit_paths`` (IMPL-collective §2.6: a linha de log referencia
  o commit ANTERIOR; commit + log é uma operação só, sem circularidade).
- ``log_for(path)`` itera o walker do dulwich filtrando por path —
  ``dulwich.porcelain.log(paths=[...])`` já filtra corretamente, e o walker
  programático nos dá ``CommitInfo`` estruturado para a UI.
- ``ensure_repo`` é idempotente: ``git init`` se não há ``.git``, e
  ``.gitignore`` é reescrito sempre que diverge do template (idempotência
  mantida; mudança silenciosa é responsabilidade de quem mudou o template).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dulwich import porcelain
from dulwich.repo import Repo

from .paths import BundleLayout

GITIGNORE_TEMPLATE = """\
# okf-bundle-core (P2)
graphify-out/
graphify-out/graph.json
graphify-out/graph.html
graphify-out/GRAPH_REPORT.md
.memory.lock
.knowledge.lock
*.tmp
*.partial
*.swp
.DS_Store
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
"""


@dataclass(frozen=True)
class CommitInfo:
    """Informações de um commit, estruturadas para consumo por UI / log."""

    sha: str
    author: str
    email: str
    timestamp: datetime
    message: str
    paths: list[str]


class InboxCommitError(Exception):
    """Levantada quando ``commit_paths`` recebe um path sob inbox (D33)."""


class GitStore:
    """Git puro via ``dulwich.porcelain`` com políticas do bundle OKF."""

    def __init__(
        self,
        root: Path,
        layout: BundleLayout,
        *,
        author: str = "percival",
        email: str = "percival@percival.os",
    ) -> None:
        self.root = Path(root)
        self.layout = layout
        self._author = author
        self._email = email

    def _author_line(self) -> bytes:
        # dulwich aceita ``author=<bytes>`` no formato ``Name <email>``.
        return f"{self._author} <{self._email}>".encode()

    def ensure_repo(self) -> None:
        """``git init`` idempotente + ``.gitignore`` mantido.

        Idempotente e seguro para chamadas concorrentes: usa um arquivo
        sentinel ``.git/HEAD`` para detectar init já feito e ignora
        ``FileExistsError`` no caminho raro em que dois processos
        disputam o init.

        ``.gitignore``: MERGE, não overwrite (fix 2026-07-30, probe
        graphify do Nano, "Bug 5"). ``ensure_repo`` é chamado a cada
        ``notes_write``/``notes_delete`` (todo entrypoint monta
        ``GitStore(root, layout); gitstore.ensure_repo()``) — a política
        anterior de "reescrever ``.gitignore`` inteiro sempre que diverge
        do template" destruía silenciosamente QUALQUER entrada humana
        customizada (``_archive/``, ``sources/``, ``assets/_inbox/``,
        ``.cache/``) na primeira escrita seguinte à edição manual. O
        probe confirmou o cenário real: rebuild do grafo apagou entradas
        legadas do ``.gitignore`` de produção. Agora só ANEXA as linhas
        do template que ainda não estão presentes — entradas humanas
        nunca são removidas, e o arquivo fica no-op (sem I/O) se já
        contém tudo que o template exige.

        Cria o diretório root (``self.root.mkdir(parents=True)``) antes
        do ``Repo.init`` — dulwich NÃO cria o root, apenas o ``.git/``
        dentro. Fix 2026-07-30 ocli-review-2: sem essa linha, callers
        que passavam um path novo (ex.: ``tmp_path/'bundle'``) viravam
        ``FileNotFoundError: '/tmp/.../bundle/.git'``. O teste
        ``test_ensure_repo_cria_root_se_nao_existe`` cobre.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        git_dir = self.root / ".git"
        if not git_dir.exists():
            try:
                Repo.init(str(self.root))
            except FileExistsError:
                # Outro processo inicializou entre o ``exists()`` e o
                # ``init()`` — prosseguir, é o mesmo estado final.
                pass
        self._ensure_gitignore()

    def _ensure_gitignore(self) -> None:
        gi = self.root / ".gitignore"
        if not gi.exists():
            gi.write_text(GITIGNORE_TEMPLATE, encoding="utf-8")
            return
        current = gi.read_text(encoding="utf-8")
        current_lines = set(current.splitlines())
        missing = [line for line in GITIGNORE_TEMPLATE.splitlines() if line not in current_lines]
        if not missing:
            return
        merged = current if current.endswith("\n") else current + "\n"
        merged += "\n".join(missing) + "\n"
        gi.write_text(merged, encoding="utf-8")

    def commit_paths(self, paths: list[Path], message: str) -> str:
        """Stage APENAS os paths dados (nunca ``add -A``) e commita.

        Devolve o SHA do commit (hex str).

        Recusa paths sob ``layout.inbox_parent`` (no AK: ``sources/``) —
        D33: arquivos brutos vão pro restic, não pro git.

        A separação ``add`` seguido de ``commit`` é o padrão do dulwich
        para commits não-vazios; ``porcelain.commit`` aceita ``paths``
        também, mas split em dois estágios deixa mais fácil raciocinar
        sobre o que vai entrar.

        Atomicidade no nível do index: se ``porcelain.commit`` falhar
        (disco cheio, ref quebrada, etc.) após o ``porcelain.add`` ter
        indexado os paths, ``Repo.unstage(tuple)`` é chamado para
        desfazer o staging APENAS dos paths deste commit. Sem isto, o
        próximo ``commit_paths`` bem-sucedido arrastaria o staging-
        residual — ex.: um ``add`` de ``notes/x.md`` (delete) que falhou
        no commit viraria uma deleção fantasma no próximo commit (estado
        inconsistente que não aparece no working dir). Fix
        2026-07-30 ocli-review-core.

        Por que ``unstage(paths)`` e não ``reset_index()``: o
        ``reset_index`` lê o HEAD tree — em repo unborn (sem nenhum
        commit) o HEAD não existe, e o método levanta ``KeyError``. O
        ``unstage`` é local (só os paths do commit atual) e funciona
        independente do estado do HEAD.
        """
        if not paths:
            raise ValueError("commit_paths called with empty list")

        rel_paths: list[str] = []
        inbox_parts = self.layout.inbox_parent
        for p in paths:
            rel = Path(p).relative_to(self.root)
            # ``inbox_parent`` é um prefixo de path components: em AK é
            # ``("sources",)`` (1 nível) e em CM é ``("assets", "_inbox")``
            # (2 níveis). Comparação por parts para não bloquear o
            # diretório inteiro quando só a subpasta ``_inbox`` é inbox.
            if rel.parts[: len(inbox_parts)] == inbox_parts:
                raise InboxCommitError(f"path {rel} is raw source (inbox), not for git — D33")
            rel_paths.append(os.fspath(rel))

        # Stage explícito (nunca add -A).
        porcelain.add(str(self.root), paths=rel_paths)
        author = self._author_line()
        try:
            sha = porcelain.commit(
                str(self.root),
                message=message.encode("utf-8"),
                author=author,
                committer=author,
            )
        except Exception:
            # O ``porcelain.add`` indexou os paths (additions OU deletions)
            # mas o commit falhou. Reverter o staging apenas dos paths deste
            # commit, sem isto, o index fica sujo e o próximo
            # ``commit_paths`` bem-sucedido arrasta o staging residual —
            # ex.: um ``add`` de ``notes/x.md`` (delete) que falhou no
            # commit viraria uma deleção fantasma no próximo commit
            # (estado inconsistente que não aparece no working dir).
            #
            # ``Repo.unstage`` foi removido no dulwich 1.x (era
            # ``replace_me(remove_in=0.26.0)``). ``porcelain.reset_file``
            # falha em repo unborn porque faz ``parse_tree(HEAD)``.
            # Manipulamos o ``Index`` direto — funciona em qualquer
            # estado (unborn ou pós-primeiro-commit) e remove apenas os
            # paths deste commit, sem afetar outros paths já staged por
            # callers concorrentes.
            try:
                with Repo(str(self.root)) as repo:
                    index = repo.open_index()
                    for rel in rel_paths:
                        bpath = rel.encode("utf-8") if isinstance(rel, str) else rel
                        if bpath in index:
                            del index[bpath]
                    index.write()
            except Exception:
                # Se a reversão também falhar (repo corrompido), não temos
                # como ajudar — propaga o erro original. O caller vai
                # logar e o estado vai precisar de intervenção manual.
                pass
            raise
        if isinstance(sha, bytes):
            return sha.decode("ascii")
        return sha

    def log_for(self, path: Path | str, limit: int = 20) -> list[CommitInfo]:
        """Histórico de commits que tocaram ``path`` (mais recente primeiro).

        Usa o walker do dulwich filtrando por path — equivalente a
        ``porcelain.log(paths=[rel], max_entries=limit)`` mas devolve
        objetos estruturados em vez de texto formatado.

        Repo sem nenhum commit (HEAD unborn) devolve ``[]`` — sem
        histórico, sem erro.

        Bug fix 2026-07-30 ocli-review-3: aceita ``str`` (path
        relativo) além de ``Path`` (absoluto). A versão anterior
        chamava ``Path(path).relative_to(self.root)`` direto —
        ``Path`` aceita ``str`` mas ``None`` propagava ``TypeError``
        do dulwich com mensagem confusa; ``str`` relativo propagava
        erro de ``relative_to`` com mensagem útil mas errada.
        Tratamento centralizado com ``ValueError`` para inputs
        inválidos.
        """
        if path is None:
            raise ValueError("path é obrigatório (recebido None)")
        path_obj = Path(path)
        # Aceita path absoluto ou relativo: se relativo, prefixa
        # ``self.root`` antes de calcular o relative_to.
        if not path_obj.is_absolute():
            path_obj = self.root / path_obj
        rel = path_obj.relative_to(self.root)
        rel_str = os.fspath(rel)
        # ``with`` (não ``Repo(...)`` solto) — ao contrário de
        # ``porcelain.add``/``porcelain.commit`` (que abrem/fecham via
        # ``open_repo_closing`` internamente), instanciar ``Repo`` direto
        # não fecha os pack files/mmaps sozinho (sem ``__del__``; só
        # ``__exit__`` chama ``close()``). Como ``log_for`` é chamado a
        # cada ``GET /notes/{id}/history``, sem o ``with`` cada request
        # vazava file descriptors/mmaps até o processo esgotar o ulimit.
        with Repo(str(self.root)) as repo:
            try:
                head_sha = repo.head()
            except KeyError:
                # unborn branch — sem commits, sem histórico.
                return []
            out: list[CommitInfo] = []
            for entry in repo.get_walker(
                paths=[rel_str.encode("utf-8")], max_entries=limit, include=[head_sha]
            ):
                c = entry.commit
                # ``c.author`` é bytes no formato "Name <email>"; separamos os
                # dois porque o caller provavelmente quer renderizar separados.
                raw_author = c.author.decode(errors="replace")
                author_name, author_email = _split_author(raw_author)
                out.append(
                    CommitInfo(
                        sha=c.id.decode("ascii"),
                        author=author_name,
                        email=author_email,
                        timestamp=datetime.fromtimestamp(c.commit_time, tz=timezone.utc),
                        message=c.message.decode(errors="replace"),
                        paths=[rel_str],
                    )
                )
            return out

    def append_log(self, entry: dict[str, str]) -> Path:
        """Append de uma linha em ``log.md``. Devolve o path pra commit.

        Esquema da linha (mantida estável para parsing de auditoria em P5+):
        ``| timestamp | kind | op | path | by | note |``.

        Caller deve passar o path devolvido na MESMA lista de paths do
        ``commit_paths`` (IMPL-collective §2.6) — assim a linha de log
        é commitada no mesmo commit que escreveu a nota, sem diff sujo
        permanente em ``log.md``.

        Escape de pipes (``\\|``) nas colunas variáveis: markdown tables
        usam ``|`` como delimitador de coluna — um ``|`` dentro de
        ``note`` (camada controlada pelos argumentos ``reason`` do
        ``notes_write``/``notes_delete``) ou ``path`` (criado pelo
        caller, ex.: importadores terceiros) quebraria a tabela
        silenciosamente, e na próxima auditoria a linha inteira viraria
        duas colunas deslocadas. Fix 2026-07-30 ocli-review-core.
        """
        log = self.root / "log.md"
        if not isinstance(entry, dict):
            # Caller bug — provavelmente programação defensiva em
            # adapter. Substitui por TypeError explícito em vez de
            # ``AttributeError`` confuso. Fix 2026-07-30 ocli-review-2.
            raise TypeError(f"append_log expects dict, got {type(entry).__name__}: {entry!r}")
        ts = entry.get("timestamp") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        kind = entry.get("kind", "-")
        op = entry.get("op", "-")
        path = entry.get("path", "-")
        by = entry.get("by", "-")
        note = entry.get("note", "")
        # ``\\|`` é a escape canônica de pipe em markdown tables.
        line = (
            f"| {ts} | {kind} | {op} | {_escape_pipe(path)} | "
            f"{_escape_pipe(by)} | {_escape_pipe(note)} |\n"
        )
        # Append atômico do ponto de vista do leitor: linha única num
        # arquivo que pode estar sendo lido concorrentemente. ``open(a)``
        # no Linux escreve abaixo do offset, mas para nosso caso (log.md
        # sempre sob lock do BundleLock) o ganho de atomicidade extra é
        # marginal — manter simples.
        # ``ensure_repo`` cria o root, mas o caller pode ter um path
        # diferente (testes, importer custom) — mkdir deixa append_log
        # seguro fora do happy-path de ``notes_write``.
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return log


def _split_author(raw: str) -> tuple[str, str]:
    """Separa ``"Name <email>"`` em ``(name, email)``. Tolera ausência."""
    if "<" in raw and ">" in raw:
        name, rest = raw.split("<", 1)
        email = rest.split(">", 1)[0]
        return name.strip(), email.strip()
    return raw.strip(), ""


def _escape_pipe(value: str) -> str:
    """Escapa ``|`` para ``\\|`` para preservar tabela markdown do ``log.md``.

    Ver ``append_log`` docstring. Pequeno detalhe: ``value`` pode conter
    ``\\`` (backslash) já presente — ``replace`` é seguro porque ``\\|``
    PRÉ-ESCAPADO não vira ``\\\\|`` (apenas ``|`` é alvo, não ``\\``).
    """
    return value.replace("|", "\\|")
