"""Audio/image modality smoke for the LLM provider contract.

The KG plan explicitly defers audio input: no backend currently declares
``audio`` support via ``LLMProvider.chat``. This script asserts the default
behaviour so that anyone flipping the contract without a paired release note
breaks CI rather than silently regressing capability.

Run with ``python scripts/kg_platform_modality_smoke.py`` from the repository
root. Exits 0 on success, non-zero with a diagnostic on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nanobot.providers.base import LLMProvider  # noqa: E402


class _StubProvider(LLMProvider):
    """Concrete subclass with no real backend, used only to exercise the default."""

    async def chat(self, *args, **kwargs):  # pragma: no cover - never called
        raise NotImplementedError

    def get_default_model(self):  # pragma: no cover - never called
        raise NotImplementedError


def main() -> int:
    provider = _StubProvider(provider_name="stub-modality-smoke")
    # Audio is a documented gap: every default backend must refuse it.
    if provider.supports_modality("audio", "any-model"):
        print(
            "FAIL: default LLMProvider unexpectedly claims audio support",
            file=sys.stderr,
        )
        return 1
    # The default for any unrecognised modality/model is also False.
    if provider.supports_modality("hologram", "any-model"):
        print(
            "FAIL: default LLMProvider unexpectedly claims an unknown modality",
            file=sys.stderr,
        )
        return 1
    print("modality defaults ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())