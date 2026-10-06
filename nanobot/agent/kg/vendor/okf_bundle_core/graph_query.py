"""Consultas de leitura sobre ``graph.json`` — bypass do matcher fuzzy do graphifyy.

O pacote ``graphifyy`` (upstream, v0.9.28, NÃO vendorizado — ver
``agent-docker/mcp_servers/graphify-collective/README.md`` "Why a stub directory
instead of vendored code?") tem um bug de tokenização confirmado em
``_find_node``/``_pick_scored_endpoint`` (``MCP_Docs/reports/
2026-07-30-graphify-mcp-probe.md`` Bugs 1/2, re-verificado em
``2026-07-30-graphify-mcp-recheck.md``): ids puros (``YYYYMMDD-HHMMSS``)
nunca casam contra labels hifenizados quando passados pra
``get_neighbors``/``shortest_path`` — o tokenizer separa o id em partes por
hífen e rejunta com espaço, perdendo o hífen original. O workaround "passar
o title" (documentado nos READMEs dos adapters) funciona pra notas com
título, mas falha pra notas cujo ``label`` é o próprio ``id`` (sem título —
ver ``graph.py:_build_node``: ``label = fm.title or fm.id or "(sem título)"``).

Este módulo dá aos callers (CM/AK) uma consulta EXATA por id, lendo o mesmo
``graph.json`` que ``okf_bundle_core.graph.build_graph`` já escreve — sem
depender do matcher fuzzy do graphifyy e sem vendorizar/patchear o pacote.
Read-only: nunca escreve ``graph.json``; se ele não existir, o caller deve
rodar ``build_graph`` primeiro (``cm-doctor``/``ak-doctor`` fazem isso
automaticamente).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import networkx as nx

from .errors import ZettelError


@dataclass(frozen=True)
class GraphNeighbor:
    """Um vizinho direto (1-hop) de um node, com direção e relação da aresta."""

    id: str
    label: str
    direction: Literal["in", "out"]
    relation: str


@dataclass(frozen=True)
class GraphNeighborsResult:
    """Resultado de ``neighbors()``: o node consultado + seus vizinhos diretos."""

    node_id: str
    label: str
    neighbors: list[GraphNeighbor]


@dataclass(frozen=True)
class GraphPathResult:
    """Resultado de ``shortest_path()``.

    ``found=False`` quando não há caminho algum entre os dois nodes, ou
    quando o caminho existe mas excede ``max_hops`` — nos dois casos
    ``path``/``labels`` vêm vazios (o caller não precisa distinguir "sem
    caminho" de "caminho longo demais" na maioria dos usos; ``hops`` fica
    preenchido no segundo caso para quem quiser diagnosticar).
    """

    found: bool
    source_id: str
    target_id: str
    hops: int
    path: list[str]
    labels: list[str]


def _graph_path(root: Path) -> Path:
    return Path(root) / "graphify-out" / "graph.json"


def _load_graph(root: Path) -> nx.DiGraph:
    """Carrega ``graph.json`` como ``nx.DiGraph`` — mesmo formato que
    ``build_graph`` escreve (``node_link_data(..., edges="links")``), então
    ``node_link_graph`` é o inverso exato.

    Levanta ``ZettelError`` (``code="graph_query_missing"``) se o arquivo
    não existir, ou ``code="graph_query_corrupt"`` se não for JSON válido —
    o caller decide se roda ``build_graph``/reporta erro ao usuário.
    """
    path = _graph_path(root)
    if not path.exists():
        raise ZettelError(
            f"graph.json não existe em {path} — rode build_graph (ou "
            f"cm-doctor/ak-doctor, que auto-criam) antes de consultar",
            code="graph_query_missing",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ZettelError(
            f"graph.json em {path} não é JSON válido: {exc}",
            code="graph_query_corrupt",
        ) from exc
    return nx.node_link_graph(data, edges="links")


def _label(g: nx.DiGraph, node_id: str) -> str:
    """Label de ``node_id`` com fallback pro próprio id.

    Node "fantasma" (aresta dangling — ver ``graph.GraphBuildResult.
    edges_dangling``) não tem attrs (``g.nodes[node_id] == {}``) — o
    fallback evita ``None``/string vazia no output.
    """
    return g.nodes[node_id].get("label") or node_id


def neighbors(
    root: Path,
    node_id: str,
    *,
    relation_filter: list[str] | None = None,
) -> GraphNeighborsResult:
    """Vizinhos diretos (1-hop, ambas direções) de ``node_id``, por match
    EXATO de id.

    Bypassa o Bug 1 (bug de tokenização do graphifyy) — funciona mesmo
    quando ``label == id`` (nota sem título), caso em que o workaround
    "passar o title" não tem o que oferecer.

    Levanta ``ZettelError`` (``graph_query_node_not_found``) se ``node_id``
    não existir no grafo.
    """
    g = _load_graph(root)
    if node_id not in g:
        raise ZettelError(
            f"node {node_id!r} não existe em {_graph_path(root)}",
            code="graph_query_node_not_found",
        )
    out: list[GraphNeighbor] = []
    for pred in g.predecessors(node_id):
        relation = g.edges[pred, node_id].get("relation", "related")
        if relation_filter and relation not in relation_filter:
            continue
        out.append(GraphNeighbor(id=pred, label=_label(g, pred), direction="in", relation=relation))
    for succ in g.successors(node_id):
        relation = g.edges[node_id, succ].get("relation", "related")
        if relation_filter and relation not in relation_filter:
            continue
        out.append(
            GraphNeighbor(id=succ, label=_label(g, succ), direction="out", relation=relation)
        )
    return GraphNeighborsResult(node_id=node_id, label=_label(g, node_id), neighbors=out)


def shortest_path(
    root: Path,
    source_id: str,
    target_id: str,
    *,
    max_hops: int | None = None,
) -> GraphPathResult:
    """Caminho mais curto entre ``source_id`` e ``target_id``, por match
    EXATO de id.

    Bypassa o Bug 2 do graphifyy (``_pick_scored_endpoint`` resolve ids
    distintos pro MESMO node por causa do mesmo bug de tokenização do
    Bug 1, e a mensagem de erro upstream — "Use a more specific label or
    the exact node ID" — é enganosa quando o id passado já era exato).

    Trata o grafo como não-direcionado pro cálculo do caminho — "como X e Y
    se conectam" é uma pergunta simétrica (mesma semântica observada no
    ``shortest_path`` do graphifyy, que também retorna caminho independente
    do sentido das arestas).

    Levanta ``ZettelError`` (``graph_query_node_not_found``) se algum dos
    dois ids não existir no grafo. ``found=False`` (sem levantar) se não
    houver caminho, ou se o caminho existir mas exceder ``max_hops``.
    """
    g = _load_graph(root)
    for nid in (source_id, target_id):
        if nid not in g:
            raise ZettelError(
                f"node {nid!r} não existe em {_graph_path(root)}",
                code="graph_query_node_not_found",
            )
    if source_id == target_id:
        return GraphPathResult(
            found=True,
            source_id=source_id,
            target_id=target_id,
            hops=0,
            path=[source_id],
            labels=[_label(g, source_id)],
        )
    undirected = g.to_undirected(as_view=True)
    try:
        path = nx.shortest_path(undirected, source_id, target_id)
    except nx.NetworkXNoPath:
        return GraphPathResult(
            found=False, source_id=source_id, target_id=target_id, hops=0, path=[], labels=[]
        )
    hops = len(path) - 1
    if max_hops is not None and hops > max_hops:
        return GraphPathResult(
            found=False, source_id=source_id, target_id=target_id, hops=hops, path=[], labels=[]
        )
    return GraphPathResult(
        found=True,
        source_id=source_id,
        target_id=target_id,
        hops=hops,
        path=path,
        labels=[_label(g, n) for n in path],
    )
