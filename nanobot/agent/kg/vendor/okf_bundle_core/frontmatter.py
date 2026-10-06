"""Parsing e serialização de frontmatter + extração de links do body markdown.

Fornece:

- ``split_frontmatter(text)``: separa o bloco ``---\\n...\\n---\\n`` do corpo.
- ``serialize(fm, body)``: round-trip estável com ordem canônica de chaves.
- ``extract_links(body)``: percorre o AST do markdown-it-py e devolve wikilinks
  (``[[id|label]]``) e markdown links (``[text](href)``), filtrando code fence
  e code inline.

Os wikilinks não são parte do CommonMark — detectamos via regex no token de
texto que os contém. O wikilink canônico é ``[[id]]``; ``[[id|label]]`` é a
forma com label opcional.
"""

from __future__ import annotations

import re
from typing import Any, Literal

import yaml
from markdown_it import MarkdownIt
from pydantic import BaseModel

from .schema import ZettelFrontmatter

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")

# Ordem canônica de chaves — round-trip estável. Chaves canônicas vão primeiro,
# depois extras em ordem alfabética para não gerar ruído no `git diff`.
KEY_ORDER = (
    "type",
    "id",
    "title",
    "description",
    "tags",
    "resource",
    "generated",
    "verified",
    "status",
    "stale_after",
    "sources",
    "usage_window",
    "supersedes",
    "derived_from",
    "summary",
)


class Link(BaseModel):
    """Link extraído do corpo de uma nota."""

    target: str
    kind: Literal["wiki", "markdown"]
    text: str | None = None
    is_external: bool = False
    # 1-based line number do body onde o link aparece, ou ``None`` se
    # a posição não pôde ser determinada.
    source_line: int | None = None


_md = MarkdownIt("commonmark", {"html": False})


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Separa o bloco ``---...---`` do corpo.

    Tolera arquivo sem frontmatter (devolve ``({}, body inteiro)``). Aceita
    trailing newline opcional antes do ``---``. BOM UTF-8 (``\ufeff`` no
    início, comum em arquivos editados no Notepad do Windows ou salvos
    via ``echo > file`` no PowerShell) é descartado — sem esse strip,
    o YAML safe_load retornaria ``{\ufefftype: 'Note', ...}`` e a chave
    ``type`` viraria ``\ufefftype`` (não casaria com o schema), fazendo
    ``graph.py`` descartar a nota silenciosamente e ``notes_read``
    retornar erro genérico.

    Quando o bloco YAML é válido mas não é mapping (ex.: lista, escalar),
    o ``frontmatter`` é descartado (``{}``) e o ``body`` devolvido é
    APENAS o conteúdo após o segundo ``---`` — devolver o ``text`` inteiro
    faria o ``body`` vir com o frontmatter YAML concatenado, corrompendo
    o ``body_sha256`` (D47) e fazendo ``extract_links`` interpretar
    ``[[id]]`` no YAML como wikilink do body. Bug fix
    2026-07-30 ocli-review-core.

    Bug fix 2026-07-30 ocli-review-2: YAML malformado (ex.: ``:yaml sem
    valor``) propagava ``yaml.scanner.ScannerError`` (subclasse de
    ``yaml.YAMLError``) — sem captura. ``graph.py:build_graph`` lia
    várias notas em sequência; UMA nota quebrada derrubava o build
    inteiro. Agora a função levanta ``ZettelError`` (com a classe da
    exceção + linha na mensagem) para que o caller decida se pula a
    nota ou aborta.
    """
    if text.startswith("\ufeff"):
        text = text[1:]
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        raw_fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        # YAML malformado — levantar erro estruturado para o caller
        # ``graph.py``/``notes_read`` distinguir do "sem frontmatter".
        # Import local para evitar ciclo ``frontmatter → zettel``.
        from .errors import ZettelError

        line = exc.problem_mark.line + 1 if getattr(exc, "problem_mark", None) else "?"
        raise ZettelError(
            f"frontmatter YAML inválido (linha {line}): {type(exc).__name__}: {exc}",
            code="frontmatter_yaml_invalid",
        ) from exc
    raw_fm = raw_fm or {}
    if not isinstance(raw_fm, dict):
        # YAML válido mas não-mapping (ex.: lista no topo) — devolve vazio
        # para que schema.py rejeite mais à frente com erro claro. Body é
        # só o trecho APÓS o ``---`` final — ver docstring.
        return {}, m.group(2)
    return raw_fm, m.group(2)


def serialize(fm: ZettelFrontmatter, body: str) -> str:
    """Round-trip estável: ordem de chaves fixa + extras em ordem alfabética.

    Usa ``exclude_unset=True`` para emitir apenas os campos que foram
    explicitamente fornecidos (ou preenchidos pelo preprocessador do schema).
    Listas vazias via ``default_factory=list`` são tratadas como unset pelo
    pydantic v2, então ``tags=[]``, ``supersedes=[]`` etc. não poluem o YAML.
    ``by_alias=True`` é usado para que campos com alias (``from_`` → ``from``
    no ``UsageWindow``) sejam serializados pelo nome canônico YAML.
    """
    raw = fm.model_dump(by_alias=True, exclude_unset=True, mode="json")
    ordered: dict[str, Any] = {}
    for k in KEY_ORDER:
        if k in raw:
            ordered[k] = raw[k]
    for k in sorted(set(raw) - set(KEY_ORDER)):
        ordered[k] = raw[k]
    yaml_text = yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    return f"---\n{yaml_text}---\n{body}"


def _is_external(href: str) -> bool:
    return href.startswith(("http://", "https://"))


def extract_links(body: str) -> list[Link]:
    """Extrai wikilinks (``[[id|label]]``) e markdown links do body.

    Ignora links dentro de code fence (```...```) e code inline (``...``).
    Links externos (``http://...``, ``https://...``) são marcados com
    ``is_external=True`` para que ``graph.py`` não vire aresta interna.

    Cada link recebe ``source_line`` (1-based) com a linha do body onde foi
    encontrado — usado por ``graph.py`` para deduplicar wikilinks que
    aparecem dentro de linhas canônicas ``- relation :: [[id]]``. O valor
    é correto mesmo para wikilinks/markdown-links após softbreaks dentro
    do mesmo parágrafo (offset de linhas é contado a partir do início do
    token ``inline``).
    """
    tokens = _md.parse(body)
    links: list[Link] = []
    for tok in tokens:
        # ``fence``/``code_block`` são tokens ÚNICOS e auto-contidos no
        # markdown-it (o bloco inteiro, sem par abre/fecha) — ao contrário
        # de containers como blockquote/list, que usam ``*_open``/``*_close``.
        # Um toggle (``in_code = not in_code``) aqui trata o PRIMEIRO fence
        # do documento como "abertura" e nunca encontra o "fechamento"
        # correspondente — todo conteúdo depois do primeiro code fence
        # ficava permanentemente marcado como "dentro de código" e perdia
        # TODOS os links (wiki e markdown) do resto da nota. Bug crítico:
        # afetava _find_backlinks (zettel.py) e build_graph (graph.py) — não
        # coberto por test_wikilink_dentro_de_code_fence_e_ignorado porque
        # aquele teste só tem link DENTRO do fence, nenhum DEPOIS dele.
        if tok.type in {"code_block", "fence"}:
            continue
        if tok.type != "inline":
            continue
        # map = [start_line, end_line] em 0-based — base para source_line.
        base_line = tok.map[0] if tok.map else 0  # 0-based
        # Construímos text_buf para detecção de wikilinks. O número de
        # ``\n`` em text_buf até qualquer posição é o offset de linha dentro
        # do bloco inline (softbreaks/hardbreaks adicionam \n); usado lá
        # embaixo para ``source_line`` correto de wikilinks em multiline.
        text_buf = ""
        cur_line_offset = 0
        # marca linha de início para os próximos childs
        for child in tok.children or []:
            if child.type == "code_inline":
                # Code inline: descarta wikilinks internos (substitui por
                # espaços do mesmo tamanho para manter alinhamento).
                content = child.content or ""
                text_buf += " " * len(content)
                continue
            if child.type == "link_open":
                href = child.attrs.get("href", "")
                # Para markdown links, source_line = linha atual do buffer
                # (= base_line + cur_line_offset, depois convertida pra 1-based)
                md_line = base_line + cur_line_offset + 1
                links.append(
                    Link(
                        target=href,
                        kind="markdown",
                        text=None,
                        is_external=_is_external(href),
                        source_line=md_line,
                    )
                )
                text_buf += " "
                continue
            if child.type in {"softbreak", "hardbreak"}:
                # Quebra visual do parágrafo: \n no buffer, avança linha.
                text_buf += "\n"
                cur_line_offset += 1
                continue
            # text/qualquer outro: detecta wikilinks via regex.
            content = child.content or ""
            text_buf += content
        # Processa wikilinks com base no text_buf e nos offsets acumulados.
        for m in WIKILINK_RE.finditer(text_buf):
            raw = m.group(1)
            if "|" in raw:
                target, label = raw.split("|", 1)
                target, label = target.strip(), label.strip()
            else:
                target, label = raw.strip(), None
            # Conta quebras de linha no text_buf até a posição do match.
            offset = text_buf[: m.start()].count("\n")
            wiki_line = base_line + offset + 1
            links.append(
                Link(
                    target=target,
                    kind="wiki",
                    text=label,
                    is_external=False,
                    source_line=wiki_line,
                )
            )
    return links
