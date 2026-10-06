"""Exceções públicas do okf-bundle-core.

Módulo criado em 2026-07-30 ocli-review-2 para evitar ciclo de
import: ``frontmatter.py`` precisa lançar ``ZettelError`` quando YAML
malformado, mas é importado por ``zettel.py`` (que define
``ZettelError``). Mover a classe pra cá quebra o ciclo.
"""

from __future__ import annotations


class ZettelError(Exception):
    """Erro genérico de operação sobre nota.

    ``code`` é um identificador opcional, estável por categoria de
    erro, para que o caller (MCP layer, HTTP API) decida a forma de
    comunicação sem precisar parsear a mensagem. Convenção:
    ``snake_case`` com prefixo de módulo (ex.: ``frontmatter_yaml_invalid``).
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class CASMismatchError(ZettelError):
    """Levantada quando ``expected_*_hash`` em ``WriteRequest`` não bate
    com o estado atual da nota (D47). Always ``code="cas_mismatch"``.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="cas_mismatch")
