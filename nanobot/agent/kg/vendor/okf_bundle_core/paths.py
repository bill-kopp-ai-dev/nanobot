"""Parametrização de layout e resolução segura de paths dentro de um bundle.

Dois layouts: ``COLLECTIVE_MEMORY`` (notes/diary/assets) e ``ACQUIRED_KNOWLEDGE``
(notes/sources). A função ``resolve_safe_path`` é a barreira contra path traversal:
bloqueia ``..``, absolutos, symlinks pra fora, nomes reservados e NUL bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Nomes que não podem aparecer como parte de um path dentro de um bundle.
# O check acontece em cada parte do path relativo (via Path.parts), então só
# listamos componentes indivisíveis:
# - ``.git``: protege estado do repositório.
# - ``.memory.lock`` / ``.knowledge.lock``: lock files dos dois layouts.
# - ``graphify-out``: diretório de derivados que ``graph.py`` reescreve —
#   bloqueamos só o diretório raiz; arquivos dentro dele (graph.json, etc.)
#   são cobertos pela checagem de prefixo no diretório pai.
RESERVED = frozenset(
    {
        ".git",
        ".memory.lock",
        ".knowledge.lock",
        "graphify-out",
    }
)


class PathEscapeError(Exception):
    """Raised when a relative path resolves outside the bundle root."""

    def __init__(self, attempted: str) -> None:
        super().__init__(f"path escapes bundle root: {attempted!r}")
        self.attempted = attempted


class ReservedPathError(Exception):
    """Raised when a path uses a reserved name (e.g. ``.git``, ``graphify-out``)."""

    def __init__(self, attempted: str) -> None:
        super().__init__(f"path uses reserved name: {attempted!r}")
        self.attempted = attempted


@dataclass(frozen=True)
class BundleLayout:
    """Parâmetros que distinguem os dois layouts suportados pelo okf-bundle-core."""

    notes_dir: str = "notes"
    extra_dirs: tuple[str, ...] = ("diary", "assets")
    # Prefixo de path components que identifica o "inbox" (arquivos brutos
    # que NÃO vão pro git — D33). Pode ter 1 nível (AK: ``sources/`` inteiro
    # é inbox) ou mais (CM: só ``assets/_inbox/`` é inbox; o resto de
    # ``assets/`` é asset processado e pode entrar no git).
    inbox_parent: tuple[str, ...] = ("assets", "_inbox")
    archive_dir: str = "_archive"
    lock_file: str = ".memory.lock"
    # ``git_tracked`` era uma lista branca usada em iterações antigas; o
    # ``GitStore.commit_paths`` agora exige paths explícitos e o campo é
    # mantido só como documentação do que tipicamente é versionado.
    git_tracked: tuple[str, ...] = ("notes", "diary", "assets", "index.md", "log.md")
    notes_extension: str = ".md"


COLLECTIVE_MEMORY = BundleLayout()

ACQUIRED_KNOWLEDGE = BundleLayout(
    extra_dirs=("sources",),
    inbox_parent=("sources",),
    lock_file=".knowledge.lock",
    git_tracked=("notes", "index.md", "log.md"),
)


def resolve_bundle_arg(value: str | Path, *, bundle_name: str, layout: BundleLayout) -> Path:
    """Normaliza um ``--bundle-root`` de CLI para o BUNDLE em si.

    Os CLIs dos dois servers nasceram com duas convenções incompatíveis para
    a mesma flag: ``cm-doctor``/``ak-doctor`` e os ``__main__`` esperavam o
    **pai** (porque escrevem ``*_ROOT``, e essa env aponta pro pai — ver
    ``paths.py`` de cada pacote), enquanto ``cm-graph-rebuild``/
    ``ak-graph-rebuild`` esperavam o **bundle** (convenção de ``build_graph``
    e do retorno de ``find_bundle_root``). Passar a forma errada não dava
    erro claro: o doctor reportava "bundle não existe" e o rebuild construía
    um grafo vazio num diretório novo.

    Este helper aceita as duas formas e sempre devolve o bundle, na ordem:

    1. ``value`` já se chama ``bundle_name`` → é o bundle.
    2. ``value/<bundle_name>/`` existe → ``value`` é o pai.
    3. ``value`` contém ``<notes_dir>/`` → é um bundle com nome fora do
       padrão (fixtures "golden", bind-mounts renomeados).
    4. Nenhuma das anteriores (path inexistente, típico de erro de digitação)
       → trata como pai e devolve ``value/<bundle_name>``, preservando as
       mensagens de erro históricas ("``X/.collective-memory`` não existe"),
       que nomeiam o que era esperado.

    Não valida existência — quem chama decide (o doctor reporta ``fail``, o
    ``find_bundle_root`` levanta ``BundleNotFoundError``).
    """
    p = Path(value).expanduser()
    p = p.resolve() if p.is_absolute() or p.exists() else p.absolute()
    if p.name == bundle_name:
        return p
    if (p / bundle_name).is_dir():
        return p / bundle_name
    if (p / layout.notes_dir).is_dir():
        return p
    return p / bundle_name


def resolve_safe_path(root: Path, rel: str, layout: BundleLayout) -> Path:
    """Resolve ``rel`` dentro de ``root`` e valida que fica dentro do bundle.

    Bloqueia:

    - NUL bytes em ``rel`` (alguns sistemas de arquivo aceitam nomes truncados)
    - paths absolutos e ``..`` que resolvem pra fora do root
    - symlinks que apontam pra fora do root
    - nomes reservados em qualquer parte do path

    O parâmetro ``layout`` é mantido na assinatura para futura extensão (ex.:
    validar que ``rel`` está dentro de um diretório permitido pelo layout).
    """
    del layout  # reservado para checagens de whitelist em P2
    if "\x00" in rel:
        raise PathEscapeError(rel)
    root_resolved = root.resolve()
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise PathEscapeError(rel)
    rel_parts = candidate.relative_to(root_resolved).parts
    for part in rel_parts:
        if part in RESERVED:
            raise ReservedPathError(rel)
    return candidate


def assert_asset_exists(path: Path, *, hint: str = "") -> None:
    """Levanta ``FileNotFoundError`` se ``path`` nao existe ou nao e arquivo.

    Helper compartilhado para ``asset_get_path`` (CM) e ``_resolve_asset_path``
    (AK). Mensagem inclui ``hint`` (ex.: ``"asset_ref=foo.png"``) para
    diagnostico.

    GAP-2 do plano CM 2026-07-29.
    """
    if not path.exists() or not path.is_file():
        suffix = f" ({hint})" if hint else ""
        raise FileNotFoundError(f"asset {path}{suffix} não existe no filesystem")
