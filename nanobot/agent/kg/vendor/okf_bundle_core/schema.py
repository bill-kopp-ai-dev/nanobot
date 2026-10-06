"""Schema canônico do frontmatter dos bundles OKF v0.2.

Tipos: ``Note``, ``DiaryNote``, ``Structure``, ``Skill``, ``Runbook`` (Zettelkasten) +
``Source``, ``ExtractedNote`` (acquire knowledge). Auto-fill de ``id`` via timestamp;
``extra="allow"`` tolera campos legados/desconhecidos.

Validação condicional por tipo:

- ``Source``: precisa de ``source_kind``, ``file_path``, ``content_sha256`` (P1 emite
  warning; P5 vira erro hard).
- ``ExtractedNote``: precisa de ``derived_from`` não-vazio (P1 emite warning; P5 hard).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)

ZettelType = Literal[
    "Note",
    "DiaryNote",
    "Structure",
    "Skill",
    "Runbook",
    "Source",
    "ExtractedNote",
]


class SourceEntry(BaseModel):
    """OKF v0.2 §5.1: cada entrada de ``sources[]``.

    ``resource`` é texto livre — pode ser URL absoluta ou "scope descriptor"
    arbitrário (a ferramenta não força URL).
    """

    model_config = ConfigDict(extra="allow")

    resource: str
    id: str | None = None
    title: str | None = None
    author: str | None = None
    usage_count: int | None = None
    last_modified: date | None = None


class UsageWindow(BaseModel):
    """OKF v0.2 §5.1: ``usage_window`` a nível do concept."""

    model_config = ConfigDict(populate_by_name=True)

    from_: date | None = Field(default=None, alias="from")
    to: date | None = None


# ----- P11: review + lifecycle -------------------------------------------

# Sinais que a skill ``memory-maintenance`` sabe emitir. Literal (não string
# livre) por decisão de 2026-08-08: um ``kind`` com typo vira nota marcada
# que ninguém consegue filtrar. Acrescentar valor aqui exige patch no core —
# é o preço de ter a UI podendo confiar no enum.
ReviewKind = Literal[
    "isolation_90d",
    "isolation_30d_with_summary",
    "stale_after_expired",
    "status_draft_overdue",
    "invalid_output_persistent",
    "frontmatter_body_divergence",
    "needs_human_forget",
    "cold_age_threshold",
    "storage_maintenance_due",
]

ReviewAction = Literal[
    "move_to_cold",
    "set_protected_true",
    "keep_as_is",
    "forget",
    "move_to_archive",
    "run_repo_maintenance",
]

# ``active`` → nota viva. ``cold`` → aposentada, mas AINDA em ``notes/``.
#
# P11 v2: o estágio frio é uma FLAG, não um diretório. A v1 da proposta
# movia a nota para ``notes/_cold/`` e isso a tornava invisível para o
# core inteiro — todos os lookups usam glob NÃO-recursivo sobre ``notes/``
# (ver ``zettel.notes_read``/``notes_delete`` e ``graph._note_files``).
# Verificado antes da implementação: com a nota em ``notes/_cold/``,
# ``notes_read`` e ``notes_delete`` levantavam ``FileNotFoundError``,
# ``memory_stats`` reportava 0 notas, a nota sumia do grafo, e
# ``notes_search`` (que usa ``rg``, recursivo) continuava devolvendo um hit
# que ninguém conseguia abrir.
LifecycleState = Literal["active", "cold"]


class ReviewEntry(BaseModel):
    """Um sinal que o agente levantou e o humano precisa resolver.

    Cada ``kind`` é uma thread independente na mesma nota: uma nota pode
    estar simultaneamente órfã e com frontmatter divergente, e cada coisa
    se resolve em separado.

    ``flagged_at``/``reopened_at`` são **string ISO 8601 UTC**, não
    ``datetime``. Mesma convenção de ``generated.at`` — o serializador de
    frontmatter round-trippa string sem surpresa, enquanto ``datetime``
    depende do dumper YAML emitir um escalar que o Pydantic releia igual.
    """

    model_config = ConfigDict(extra="allow")

    status: Literal["pending", "acknowledged", "resolved"]
    kind: ReviewKind
    confidence: Literal["low", "medium", "high"]
    reason: str
    flagged_at: str
    flagged_by: str
    related_actions: list[ReviewAction] = Field(default_factory=list)
    # Preenchido por ``memory_resolve_review(resolution="reopen")``. Mantém
    # ``flagged_at`` original intacto para não perder a idade do sinal.
    reopened_at: str | None = None


def _auto_fill_id(v: str | None) -> str:
    """Auto-fill de ``id`` no formato ``YYYYMMDD-HHMMSS`` se ausente.

    Usa ``datetime.now(timezone.utc)`` (não naive) para consistência com
    o resto do core (e.g. ``zettel.py:notes_write`` usa UTC para
    ``generated.at``). Em servidores em TZ != UTC, o naive
    ``datetime.now()`` viraria um id com hora local, misturando IDs
    gerados em fusos diferentes — bug latente até alguém fazer
    cross-timezone build. Fix 2026-07-30 ocli-review-core.
    """
    if v:
        return v
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


class ZettelFrontmatter(BaseModel):
    """Frontmatter canônico OKF v0.2 + extensões Zettelkasten."""

    model_config = ConfigDict(extra="allow")

    type: ZettelType
    id: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    resource: str | None = None
    generated: dict[str, Any] | None = None
    # OKF v0.2 §5.2: aceita dict OU lista no YAML; o preprocessador normaliza
    # tudo para lista antes da validação final, então o tipo aqui reflete o
    # estado pós-normalização.
    verified: list[dict[str, Any]] | None = None
    status: Literal["draft", "stable", "deprecated"] | None = None
    stale_after: date | None = None
    sources: list[SourceEntry] = Field(default_factory=list)
    usage_window: UsageWindow | None = None
    supersedes: list[str] = Field(default_factory=list)
    derived_from: list[str] = Field(default_factory=list)
    summary: str | None = None
    # Extensão Zettelkasten (não-OKF, introduzida por P3): referências a assets
    # anexados a esta nota (PDF, imagem, etc.). Paths são relativos ao bundle
    # root. Não conflita com ``resource`` (singular, OKF v0.2) — ``attachments``
    # é lista e representa "arquivos físicos linkados a esta nota".
    # Pydantic com ``extra="allow"`` aceita attachments nos notes legados
    # sem migração; só os novos notes (P3+) o trazem tipado.
    attachments: list[str] = Field(default_factory=list)

    # ----- P11 -----
    # ``protected`` é o kill switch humano: bloqueia TODA transição
    # automática de lifecycle. Só humano (via ``memory_set_protected``) e o
    # script de bootstrap escrevem. A skill de manutenção lê e respeita.
    protected: bool = False
    # Estágio do ciclo de vida. Ver ``LifecycleState`` para por que isto é
    # flag e não diretório.
    lifecycle: LifecycleState = "active"
    # Quando a nota esfriou (ISO 8601 UTC). É a fonte de idade do estágio
    # frio — deliberadamente NÃO usamos ``mtime``, que é reescrito por
    # ``git clone``, restore de backup e rebuild de container: depois de
    # qualquer deploy o TTL reiniciaria em silêncio.
    cooled_at: str | None = None
    # Fila de revisão. Ausente/vazia = nada pendente.
    review: list[ReviewEntry] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _preprocess(cls, data: Any) -> Any:
        """Pré-processa o dict antes da validação: auto-fill de ``id``, split
        de ``tags`` CSV, normalização de ``verified``, default de ``status``.

        Pydantic v2 não chama ``field_validator(mode="before")`` quando o
        campo está ausente — apenas quando o input vem explicitamente. Para
        defaults que precisam ser aplicados também a entradas vazias,
        ``model_validator(mode="before")`` é o ponto certo.
        """
        if not isinstance(data, dict):
            return data
        if "id" not in data or data["id"] in (None, ""):
            data["id"] = _auto_fill_id(None)
        if isinstance(data.get("tags"), str):
            data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]
        if isinstance(data.get("verified"), dict):
            data["verified"] = [data["verified"]]
        if "status" not in data or data["status"] in (None, ""):
            data["status"] = "stable"
        # P11: ``lifecycle`` vazio (None/"") = ``active``. Notas legadas (todas
        # as 286 do bundle atual) não trazem o campo — esse é o estado correto
        # e deve permanecer *unset*, para que ``exclude_unset=True`` no
        # ``serialize`` não acrescente ``lifecycle: active`` em cada
        # round-trip (precondição do saneamento 2026-08-09).
        # A versão antiga usava ``"lifecycle" not in data or ...``, que
        # atribuía o default no dict de entrada e marcava o campo como *set*,
        # poluindo 370 diffs sem motivo. O default ainda protege o caso
        # "chave presente mas vazia" (``lifecycle:`` no YAML), que é o que
        # de fato precisa de proteção contra a falha do Literal.
        if data.get("lifecycle", "__ausente__") in (None, ""):
            data["lifecycle"] = "active"
        # ``protected`` escrito à mão como string ("yes", "true") sobrevive
        # hoje via ``extra="allow"``; ao virar campo tipado ele quebraria a
        # leitura. Normalizamos as formas YAML plausíveis em vez de rejeitar
        # a nota inteira — o custo de errar aqui é um bundle não-lido.
        if isinstance(data.get("protected"), str):
            raw = data["protected"].strip().lower()
            if raw in ("true", "yes", "y", "on", "1"):
                data["protected"] = True
            elif raw in ("false", "no", "n", "off", "0", ""):
                data["protected"] = False
        return data

    @model_validator(mode="after")
    def _validate_by_type(self) -> ZettelFrontmatter:
        """Validação condicional por tipo (P1 cobre Source/ExtractedNote; P2 amplia)."""
        extras = self.model_extra or {}
        if self.type == "Source":
            missing = [
                k for k in ("source_kind", "file_path", "content_sha256") if not extras.get(k)
            ]
            if missing:
                # Warning em P1; em P5 vira erro hard via validação completa do IMPL-acquire.
                logger.warning(
                    "type=Source sem campos obrigatórios %s em id=%r",
                    missing,
                    self.id,
                )
        if self.type == "ExtractedNote" and not self.derived_from:
            # Warning em P1; em P5 vira erro hard.
            logger.warning(
                "type=ExtractedNote sem derived_from em id=%r",
                self.id,
            )
        # P11: invariante ``cold ⇔ cooled_at``.
        #
        # Auto-corrigimos em vez de levantar. O motivo é o mesmo do
        # ``lifecycle`` default acima: este validator roda em TODA leitura de
        # nota, inclusive nas 286 legadas e em notas editadas à mão. Uma nota
        # marcada ``cold`` sem carimbo é recuperável (assumimos "esfriou
        # agora" e o TTL reinicia — conservador, nunca arquiva cedo demais);
        # levantar aqui tornaria a nota ilegível por `notes_read`, o que é
        # estritamente pior.
        if self.lifecycle == "cold" and not self.cooled_at:
            self.cooled_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            logger.warning(
                "lifecycle=cold sem cooled_at em id=%r; carimbado com now() (TTL reinicia)",
                self.id,
            )
        elif self.lifecycle == "active" and self.cooled_at:
            # Voltar para active limpa o carimbo — senão a próxima transição
            # para cold herdaria uma idade antiga e arquivaria de imediato.
            self.cooled_at = None
        return self


class FrontmatterError(BaseModel):
    """Erro de validação de frontmatter, estruturado para retorno à camada superior."""

    field: str
    message: str
    given: str | None = None
    hint: str | None = None


def validate_frontmatter(
    raw: dict[str, Any],
) -> tuple[ZettelFrontmatter | None, list[FrontmatterError]]:
    """Valida um dicionário YAML contra ``ZettelFrontmatter``.

    Nunca levanta: erros viram ``FrontmatterError`` estruturados. Pydantic v2
    expõe ``ValidationError.errors()`` com ``loc``, ``msg`` e ``input``.

    Bug fix 2026-07-30 ocli-review-2: a versão anterior só capturava
    erros via ``getattr(exc, "errors", lambda: [])()``. Quando o input
    era de tipo errado (lista, escalar, None), o construtor do
    ``ZettelFrontmatter`` levantava ``TypeError`` (não
    ``ValidationError``) — sem ``.errors()`` — e a ``getattr`` devolvia
    ``[]``. Resultado: ``validate_frontmatter([1,2,3])`` retornava
    ``(None, [])`` (silencioso). Agora, qualquer ``Exception`` cai no
    fallback explícito que inclui o tipo da exceção na mensagem.
    """
    try:
        return ZettelFrontmatter(**raw), []
    except Exception as exc:  # Pydantic ValidationError ou outro erro
        errors: list[FrontmatterError] = []
        errs_callable = getattr(exc, "errors", None)
        if callable(errs_callable):
            try:
                for err in errs_callable():
                    loc = err.get("loc", ())
                    errors.append(
                        FrontmatterError(
                            field=".".join(str(p) for p in loc),
                            message=err.get("msg", "erro"),
                            given=str(err.get("input", ""))[:200],
                            hint=None,
                        )
                    )
            except Exception:
                # ``.errors()`` falhou (raro) — cai no fallback genérico
                pass
        if not errors:
            # Garante pelo menos 1 erro estruturado para o caller
            # (``notes_read`` chama ``raise ZettelError(...)`` se a
            # lista vier vazia, antes desse fix a chamada era
            # silenciosa). Incluir o tipo da exceção para o caller
            # entender o que houve (ex.: ``TypeError`` = input não-dict).
            errors.append(
                FrontmatterError(
                    field="<root>",
                    message=f"input inválido para ZettelFrontmatter: {type(exc).__name__}: {exc}",
                    given=str(raw)[:200],
                    hint=None,
                )
            )
        return None, errors


# ----- Helpers compartilhados (GAP-2 do plano CM 2026-07-29) -------------


# Pattern canonico de id zettelkasten: ``YYYYMMDD-HHMMSS``. Single source
# of truth — CM e AK consomem daqui em vez de duplicar a regex literal.
ID_PATTERN = r"^\d{8}-\d{6}$"


def validate_id(value: str) -> str:
    """Valida que ``value`` bate o pattern canonico de id zettelkasten.

    Levanta ``ValueError`` com mensagem amigavel se nao bater.

    >>> validate_id("20260729-100000")
    '20260729-100000'
    >>> validate_id("bad-id")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: id 'bad-id' não bate o formato YYYYMMDD-HHMMSS
    """
    import re

    if not re.match(ID_PATTERN, value):
        raise ValueError(f"id {value!r} não bate o formato YYYYMMDD-HHMMSS")
    return value
