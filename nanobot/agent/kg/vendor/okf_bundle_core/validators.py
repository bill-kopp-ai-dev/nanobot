"""Validators compartilhados entre servers — 2 formas do mesmo check.

GAP-2 do plano CM 2026-07-29:

- ``not_blank_validator``: decorator Pydantic, para campos de
  ``BaseModel`` (ex.: ``ForgetRequest.reason``).
- ``assert_not_blank``: funcao simples, para valores que nao sao campo
  de model — ex.: o parametro solto ``reason`` de ``tool_memory_link``
  (``LinkRequest`` nao tem campo ``reason``; e' passado separado).
"""

from __future__ import annotations

from pydantic import field_validator


def not_blank_validator(field_name: str):
    """Decorator que rejeita whitespace-only em um campo string de ``BaseModel``.

    Uso:
        class MyRequest(BaseModel):
            reason: str
            _not_blank_reason = not_blank_validator("reason")
    """

    def _validator(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(f"{field_name} não pode ser whitespace-only")
        return v

    return field_validator(field_name)(_validator)


def assert_not_blank(value: str, *, field_name: str = "value") -> str:
    """Levanta ``ValueError`` se ``value`` for whitespace-only.

    Para usar em parametros soltos (nao campos de model) — ex.: o
    ``reason`` de ``tool_memory_link``, que nao e' um campo de
    ``LinkRequest``. Devolve ``value`` sem alteracao (permite uso
    inline: ``reason = assert_not_blank(reason, field_name="reason")``).
    """
    if not value.strip():
        raise ValueError(f"{field_name} não pode ser whitespace-only")
    return value
