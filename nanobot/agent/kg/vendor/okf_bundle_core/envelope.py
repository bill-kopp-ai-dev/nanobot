"""Envelope untrusted — o que ENTROU no core, antes de ser interpretado.

O predecessor (``percival-notes-mcp``) misturava "o frontmatter que veio"
com "o frontmatter que vale" — ``validate_frontmatter`` rodava direto no
receipt, e qualquer divergência corrompia o estado sem trilha de auditoria.

Aqui separamos:

- ``UntrustedFrontmatter``: dict cru (com ``extra='allow'``), mais
  ``raw_yaml`` opcional pra auditoria. NÃO passa por validação OKF.
- ``UntrustedNote``: ``raw_text``, ``frontmatter`` (cru) e ``body``. É o
  "recibo imutável" — ``content_sha256`` e ``body_sha256`` são derivados
  dele.

Validação OKF (``validate_frontmatter``) é responsabilidade do chamador
(``zettel.py``) — separar os dois estádios permite auditar discrepâncias
("o que entrou vs. o que ficou salvo") e isolar tentativas de injection.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .frontmatter import serialize, split_frontmatter
from .schema import ZettelFrontmatter

logger = logging.getLogger(__name__)

UntrustedSource = Literal["mcp", "file", "importer"]


class UntrustedFrontmatter(BaseModel):
    """Frontmatter como veio do cliente, sem validação OKF.

    ``extra='allow'`` captura campos legados/desconhecidos sem levantar
    — a validação estrutural fica para ``validate_frontmatter``.
    """

    model_config = ConfigDict(extra="allow")

    raw: dict[str, Any] = Field(default_factory=dict)
    raw_yaml: str | None = None  # string original, para auditoria


class UntrustedNote(BaseModel):
    """Conteúdo bruto que chegou — de tool MCP, de leitura de arquivo ou
    de um importer externo.

    Imutável do ponto de vista do envelope: o que entra, entra. A
    transformação para ``ZettelFrontmatter`` (a "interpretação validada")
    acontece em ``zettel.py``.
    """

    model_config = ConfigDict(extra="forbid")

    source: UntrustedSource
    raw_text: str
    frontmatter: UntrustedFrontmatter
    body: str

    @classmethod
    def from_file(cls, path: Path) -> UntrustedNote:
        """Lê um arquivo do bundle e devolve o envelope.

        ``split_frontmatter`` (P1) já tolera arquivo sem frontmatter
        (devolve ``({}, body inteiro)``) e YAML não-dict (devolve ``({}, ...)``
        para que ``schema.py`` rejeite adiante).
        """
        raw = path.read_text(encoding="utf-8")
        raw_fm, body = split_frontmatter(raw)
        return cls(
            source="file",
            raw_text=raw,
            frontmatter=UntrustedFrontmatter(raw=raw_fm, raw_yaml=None),
            body=body,
        )

    @classmethod
    def from_mcp(
        cls,
        body: str,
        frontmatter: dict[str, Any] | None = None,
    ) -> UntrustedNote:
        """Constrói a partir de args de uma tool MCP.

        Tenta serializar via ``ZettelFrontmatter`` (``serialize`` da P1)
        para manter a ordem canônica de chaves. Se o frontmatter não
        parseia como OKF — é o caso de payload malformado/injection —
        cai num YAML genérico; o envelope NÃO levanta, a validação fica
        para ``zettel.py``.

        Bug fix 2026-07-30 ocli-review-2: ``UntrustedFrontmatter`` é
        ``dict[str, Any]`` no Pydantic — keys não-string
        (ex.: ``{42: 'numeric'}``) faziam ``UntrustedFrontmatter(raw=fm)``
        levantar ``ValidationError`` em vez de cair no fallback
        genérico. Filtramos keys não-string para o YAML genérico e
        para o frontmatter final. Caller malicioso recebe o envelope
        com as keys inválidas descartadas (logger.warning).
        """
        raw_fm = dict(frontmatter or {})
        # Filtra keys não-string: o envelope é ``dict[str, Any]`` e o
        # ``yaml.safe_dump`` precisa de string keys. Sem o filtro,
        # ``TypeError: keywords must be strings`` no construtor do
        # pydantic ou no yaml.dump.
        fm: dict[str, Any] = {k: v for k, v in raw_fm.items() if isinstance(k, str)}
        if len(fm) != len(raw_fm):
            logger.warning(
                "from_mcp: %d keys não-string descartadas do frontmatter",
                len(raw_fm) - len(fm),
            )
        try:
            fm_obj = ZettelFrontmatter(**fm)
            raw_text = serialize(fm_obj, body)
        except Exception:  # noqa: BLE001 — envelope é untrusted; erros viram auditoria
            # ``default_flow_style=False`` força block-style mesmo para
            # listas curtas que ``safe_dump`` por padrão emitiria em flow
            # (``[a, b]`` em vez de ``- a\n- b``). Consistente com a
            # serialização canônica de ``serialize``. Fix
            # 2026-07-30 ocli-review-core.
            raw_text = f"---\n{yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)}---\n{body}"
        return cls(
            source="mcp",
            raw_text=raw_text,
            frontmatter=UntrustedFrontmatter(raw=fm, raw_yaml=None),
            body=body,
        )

    def content_sha256(self) -> str:
        """SHA-256 do arquivo inteiro (frontmatter + body) — usado pelo CAS
        ``content_hash`` em ``zettel.notes_write`` (D47)."""
        return hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest()

    def body_sha256(self) -> str:
        """SHA-256 só do body — usado pelo CAS ``body_hash`` (D47).

        Permite que o agente sobrescreva só o frontmatter (enrich do
        summary) sem disparar conflito espúrio quando o humano mexeu
        só no body.
        """
        return hashlib.sha256(self.body.encode("utf-8")).hexdigest()
