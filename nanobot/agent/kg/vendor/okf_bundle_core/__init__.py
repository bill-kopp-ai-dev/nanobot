"""okf-bundle-core: núcleo determinístico compartilhado dos bundles OKF."""

__version__ = "0.1.0"

# Re-exports dos helpers compartilhados (GAP-2 do plano CM 2026-07-29).
# Tudo o mais continua sendo importado via submodulo direto
# (``okf_bundle_core.zettel``, ``okf_bundle_core.frontmatter``, etc).
from .paths import assert_asset_exists
from .schema import ID_PATTERN, validate_id
from .validators import assert_not_blank, not_blank_validator

__all__ = [
    "ID_PATTERN",
    "assert_asset_exists",
    "assert_not_blank",
    "not_blank_validator",
    "validate_id",
]
