"""Constrói o ``graph.json`` (NetworkX node-link) a partir de um bundle.

Pipeline:

1. Varrer ``<root>/<layout.notes_dir>/*.md``
2. Para cada nota: ``split_frontmatter`` → ``ZettelFrontmatter`` → ``extract_links``
3. Coletar arestas candidatas via 4 fontes (em ordem de precedência):
   - ``frontmatter.supersedes`` (frontmatter)
   - ``frontmatter.derived_from`` (frontmatter)
   - seção ``## Links`` com ``relation ::`` (corpo)
   - wikilinks / markdown links do corpo (viram ``related``)
4. Aplicar precedência D65 (``supersedes`` > ``contradicts`` > ``derived_from`` >
   ``related``) agrupando por par **não-ordenado** de nós: só a aresta de maior
   precedência sobrevive. Tie-break determinístico pela posição na lista de
   observação.
5. Em ``<root>/graphify-out/graph.json`` no formato NetworkX node-link +
   extensão ``hyperedges``.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

from .errors import ZettelError
from .frontmatter import Link, extract_links, split_frontmatter
from .paths import BundleLayout
from .schema import ZettelFrontmatter

logger = logging.getLogger(__name__)

# Precedência D65 — relações direcionais pesam mais que ``related``.
# Maior número = mais forte. Empate vai pro primeiro observado.
RELATION_PRECEDENCE = {
    "supersedes": 4,
    "contradicts": 3,
    "derived_from": 2,
    "related": 1,
}

# Regex para a forma canônica `## Links`:
#   `- related :: [[id]]` ou `- related :: [[id|label]]` ou
#   `- supersedes :: [text](id)` — extraímos o id do alvo.
#
# IMPORTANTE — convenção que este módulo NÃO valida, apenas repassa: o alvo
# (tanto `[[alvo]]` quanto `(alvo)`) tem de ser o id PURO (YYYYMMDD-HHMMSS) da
# nota referenciada, nunca o nome de arquivo com slug (ex.:
# `20260724-100300-decisao-cas` ou `.md`). Nós no graph.json são identificados
# por `fm.id` (ver `_build_node`); um alvo com slug nunca bate com um id real,
# vira aresta "dangling" e é descartado em silêncio pelo consumidor (graphify).
# graph.py é deliberadamente burro/determinístico — emite o que vê, não
# resolve nem valida alvos (ver `test_link_para_nota_inexistente_gera_aresta_
# mas_sem_no`). A correção fica em quem escreve a nota (agente/humano), não
# aqui. O golden bundle já segue essa convenção (commit 358c7ea) para a forma
# `[[...]]`; a forma `[text](href)` está sujeita ao mesmo risco e não tem
# teste dedicado hoje — cuidado ao introduzir notas que usem `## Links` com
# a forma markdown-link e um href com slug/`.md`.
LINKS_SECTION_RE = re.compile(
    r"""
    ^\s*-\s*                  # "- "
    (supersedes|contradicts|  # relation
     derived_from|related)
    \s*::\s*                  # " :: "
    (?:
        \[\[(?P<wiki>[^\]|]+)(?:\|[^\]]+)?\]\]   # [[id]] ou [[id|label]]
        |
        \[(?P<mdtext>[^\]]*)\]\((?P<mdhref>[^)]+)\)  # [text](href)
    )
    \s*$
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class GraphBuildResult:
    """Resultado do build_graph: contadores e path de saída.

    ``edges_dangling``/``dangling_edges`` (fix 2026-07-30, probe graphify
    do Nano "Bug 3"): contagem + pares ``(source, target)`` de arestas
    cujo ``source`` ou ``target`` NÃO corresponde a nenhum node presente
    em ``nodes[]`` do JSON. Por padrão (``drop_dangling=False``) NÃO é
    filtrado/rejeitado — ``graph.py`` é deliberadamente burro e emite o
    que vê (ver docstring de ``LINKS_SECTION_RE`` acima e
    ``test_link_para_nota_inexistente_gera_aresta_mas_sem_no``); a
    correção do link fica com quem escreveu a nota. Os campos existem só
    para dar VISIBILIDADE ao caller (``cm-doctor``/``ak-doctor``) — quando
    o ``graphify.serve`` (NetworkX) carrega o JSON, arestas dangling viram
    "phantom nodes" com label vazio, confundindo ``graph_stats``/
    ``query_graph``. ``edges`` já reflete o efeito de ``drop_dangling``
    quando ativado (ver ``build_graph``) — mas ``edges_collapsed`` NÃO:
    é calculado por ``_apply_precedence`` ANTES do filtro de dangling, e
    conta só duplicatas de D65 (par não-ordenado com >1 aresta), sem
    relação com dangling. ``edges_dangling``/``dangling_edges`` sempre
    reportam o que foi ENCONTRADO, filtrado ou não.
    """

    nodes: int
    edges: int
    edges_collapsed: int
    edges_dangling: int
    dangling_edges: list[tuple[str, str]]
    output_path: Path


def _notes_paths(root: Path, layout: BundleLayout) -> list[Path]:
    notes = root / layout.notes_dir
    if not notes.exists():
        return []
    return sorted(notes.glob(f"*{layout.notes_extension}"))


def _parse_note(path: Path) -> tuple[ZettelFrontmatter, str, list[Link]] | None:
    """Lê nota, separa frontmatter, valida, extrai links.

    Devolve ``None`` se o frontmatter não parseia ou falta ``type``. Notas
    inválidas são silenciosamente descartadas — graph.py é leitura pura.

    Bug fix 2026-07-30 ocli-review-2: ``split_frontmatter`` agora
    levanta ``ZettelError`` (YAML malformado) em vez de propagar
    ``yaml.scanner.ScannerError``. Capturamos aqui para manter a
    semântica de "nota ruim pula, build continua".
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return None
    try:
        raw_fm, body = split_frontmatter(text)
    except ZettelError as exc:
        logger.warning(
            "frontmatter YAML inválido em %s — pulando (%s, code=%s)",
            path,
            exc,
            exc.code,
        )
        return None
    if not raw_fm or "type" not in raw_fm:
        return None
    try:
        fm = ZettelFrontmatter(**raw_fm)
    except Exception:  # noqa: BLE001 — schema.py já estruturou erros; aqui só pulamos
        logger.warning("frontmatter inválido em %s — pulando", path)
        return None
    return fm, body, extract_links(body)


def _build_node(fm: ZettelFrontmatter, source_file: str) -> dict:
    return {
        "id": fm.id,
        "label": fm.title or fm.id or "(sem título)",
        "file_type": "zettel",
        "source_file": source_file,
        "source_location": "L1",
        "_origin": "okf",
        "type": fm.type,
        "tags": list(fm.tags),
    }


def _edges_from_note(
    fm: ZettelFrontmatter, body: str, links: list[Link], source_file: str
) -> list[dict]:
    """Coleta todas as arestas candidatas a partir de uma nota.

    Fontes (em ordem de observação):

    1. ``frontmatter.supersedes``
    2. ``frontmatter.derived_from``
    3. corpo: seção ``## Links`` com ``relation ::`` (linha capturada por
       ``LINKS_SECTION_RE`` é ``marcada`` para evitar duplicação com wikilinks)
    4. corpo: wikilinks (``[[...]]``) e markdown links viram ``related`` —
       exceto os que vivem numa linha já capturada pela forma canônica
       ``- relation :: [[id]]``
    """
    edges: list[dict] = []
    src = fm.id
    if not src:
        return edges

    for tgt in fm.supersedes or []:
        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": "supersedes",
                "source_file": source_file,
                "source_location": "fm:supersedes",
            }
        )
    for tgt in fm.derived_from or []:
        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": "derived_from",
                "source_file": source_file,
                "source_location": "fm:derived_from",
            }
        )

    # Marca linhas do body (1-based, como `extract_links.source_line`)
    # capturadas pela forma canônica `- relation :: [[id]]` para que
    # wikilinks dessa linha não sejam reemitidos como aresta related.
    body_lines = body.splitlines()
    canonical_lines: set[int] = set()
    for idx, line in enumerate(body_lines, start=1):  # 1-based
        if LINKS_SECTION_RE.match(line):
            canonical_lines.add(idx)

    # corpo: seção ## Links
    for line_no, line in enumerate(body_lines, start=1):
        if line_no not in canonical_lines:
            continue
        m = LINKS_SECTION_RE.match(line)
        if not m:
            continue
        relation = m.group(1)
        tgt = (m.group("wiki") or m.group("mdhref") or "").strip()
        if not tgt:
            continue
        edges.append(
            {
                "source": src,
                "target": tgt,
                "relation": relation,
                "source_file": source_file,
                "source_location": f"L{line_no}",
            }
        )

    # corpo: wikilinks + markdown links internos → related.
    # Não reemite wikilinks que vivem em linhas já capturadas pelo LINKS_SECTION_RE
    # (mesma relação, evita duplicação antes da colapsação).
    for link in links:
        if link.is_external:
            continue
        line_no = link.source_line
        if line_no is not None and line_no in canonical_lines:
            # Linha já foi capturada por LINKS_SECTION_RE; não duplicar.
            continue
        if link.kind == "wiki":
            edges.append(
                {
                    "source": src,
                    "target": link.target,
                    "relation": "related",
                    "source_file": source_file,
                    "source_location": "body:wikilink",
                }
            )
        elif link.kind == "markdown":
            edges.append(
                {
                    "source": src,
                    "target": link.target,
                    "relation": "related",
                    "source_file": source_file,
                    "source_location": "body:markdown",
                }
            )

    return edges


def _apply_precedence(edges: list[dict]) -> tuple[list[dict], int]:
    """Agrupa por par não-ordenado {u,v} e mantém a aresta de maior precedência.

    Importante (revisão do plano, §0): o par canônico ordenado é usado SÓ
    para agrupar. A aresta emitida preserva o ``source``/``target`` ORIGINAIS
    do vencedor — caso contrário relações direcionais como ``supersedes``
    poderiam ter o sentido invertido.
    """
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in edges:
        pair = tuple(sorted([e["source"], e["target"]]))
        grouped[pair].append(e)

    consolidated: list[dict] = []
    collapsed = 0
    for _pair, group in grouped.items():
        if len(group) == 1:
            consolidated.append(dict(group[0]))
            continue
        # (precedência, -idx_observação) — primeiro observado vence em empate
        _, winner = max(
            enumerate(group),
            key=lambda ie: (RELATION_PRECEDENCE.get(ie[1]["relation"], 0), -ie[0]),
        )
        consolidated.append(dict(winner))
        collapsed += len(group) - 1
    return consolidated, collapsed


def build_graph(
    root: Path,
    layout: BundleLayout,
    *,
    output: Path | None = None,
    drop_dangling: bool = False,
) -> GraphBuildResult:
    """Varre ``notes/``, extrai arestas, aplica D65, emite ``graph.json``.

    - Se ``output`` for ``None``, escreve em ``<root>/graphify-out/graph.json``.
    - Bundle vazio (sem ``notes/``) emite grafo vazio válido.
    - Notas inválidas (frontmatter quebrado, sem type) são silenciosamente puladas.
    - ``drop_dangling`` (default ``False``, backlog do recheck 2026-07-30
      §7 item 2): quando ``True``, arestas cujo ``source``/``target`` não
      tem node correspondente são OMITIDAS do ``graph.json`` emitido — útil
      pra callers que precisam de um grafo canônico sem phantom nodes
      (ex.: export). O warning de log e ``edges_dangling``/``dangling_edges``
      no retorno continuam reportando o que foi encontrado, filtrado ou
      não — ``drop_dangling`` NÃO silencia a visibilidade, só decide se o
      link quebrado entra no arquivo.
    """
    root = Path(root)
    notes = _notes_paths(root, layout)
    nodes: list[dict] = []
    edges_raw: list[dict] = []
    for note_path in notes:
        parsed = _parse_note(note_path)
        if parsed is None:
            continue
        fm, body, links = parsed
        rel = str(note_path.relative_to(root))
        nodes.append(_build_node(fm, rel))
        edges_raw.extend(_edges_from_note(fm, body, links, rel))

    edges, collapsed = _apply_precedence(edges_raw)

    # Visibilidade de arestas dangling (Bug 3 do probe graphify — ver
    # docstring de ``GraphBuildResult.edges_dangling``). Por padrão NÃO
    # filtra: só conta + loga, mantendo o contrato "graph.py emite o que
    # vê". ``drop_dangling=True`` opta por omitir do JSON (ver abaixo).
    node_ids = {n["id"] for n in nodes}
    dangling_edges = [
        e for e in edges if e["source"] not in node_ids or e["target"] not in node_ids
    ]
    if dangling_edges:
        sample = ", ".join(f"{e['source']}->{e['target']}" for e in dangling_edges[:5])
        more = f" (+{len(dangling_edges) - 5} mais)" if len(dangling_edges) > 5 else ""
        logger.warning(
            "build_graph: %d aresta(s) apontam para node inexistente — %s%s",
            len(dangling_edges),
            sample,
            more,
        )
    if drop_dangling and dangling_edges:
        # (source, target) é único por aresta pós-``_apply_precedence``
        # (colapsa por par não-ordenado — só 1 aresta sobrevive por par).
        dangling_pairs = {(e["source"], e["target"]) for e in dangling_edges}
        edges = [e for e in edges if (e["source"], e["target"]) not in dangling_pairs]

    for e in edges:
        e.update(
            {
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "weight": 1.0,
                "_origin": "okf",
            }
        )

    # node_link_data com edges="links" produz o schema canônico do NetworkX
    # para DiGraph (directed=true, multigraph=false, graph={}). Adicionamos
    # ``hyperedges`` como extensão OKF.
    graph = nx.node_link_data(nx.DiGraph(), edges="links")
    graph["nodes"] = nodes
    graph["links"] = edges
    graph["hyperedges"] = []

    out = Path(output) if output else root / "graphify-out" / "graph.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    return GraphBuildResult(
        nodes=len(nodes),
        edges=len(edges),
        edges_collapsed=collapsed,
        edges_dangling=len(dangling_edges),
        dangling_edges=[(e["source"], e["target"]) for e in dangling_edges],
        output_path=out,
    )


def count_graph_artifact(graph_json: Path) -> tuple[int, int]:
    """Conta ``(nodes, edges)`` do ``graph.json`` COMO ELE ESTÁ EM DISCO.

    Existe porque ``GraphBuildResult.edges`` descreve o que ``build_graph``
    acabou de escrever, e o pipeline de rebuild NÃO para aí: o
    ``graphify cluster-only`` roda depois e REESCREVE o mesmo arquivo,
    descartando arestas dangling no caminho. Com ``drop_dangling=False``
    (o default), ``build_graph`` emite a aresta dangling de propósito — mas
    ela não sobrevive ao ``cluster-only``, então o número do build fica
    acima do que o artefato final contém.

    Quem consome o grafo (``graphify.serve`` via MCP, o ``GraphView`` da
    SPA) lê o arquivo final. Comparar o número do build contra o que o MCP
    serve produz uma divergência de exatamente ``edges_dangling`` e parece
    cache stale — foi o que motivou a issue
    ``2026-08-09-collective-memory-graphify-mcp-stale-after-rebuild.md``,
    onde ``build_graph`` reportou 201 e o MCP (corretamente) 200.

    Levanta ``OSError``/``ValueError`` se o arquivo sumiu ou está corrompido
    — o caller decide se isso é fatal.
    """
    data = json.loads(Path(graph_json).read_text(encoding="utf-8"))
    return len(data.get("nodes", [])), len(data.get("links", []))
