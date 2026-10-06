"""Ciclo de vida e uso de disco do bundle (P11).

Duas responsabilidades, deliberadamente juntas porque compartilham a mesma
varredura e o mesmo conceito de idade:

1. **Lifecycle** — quem está pronto para esfriar (``active`` → ``cold``) e
   quem está pronto para arquivar (``cold`` → ``_archive/YYYYMM/``).
2. **Storage** — quanto o bundle ocupa, onde, e o que fazer a respeito.

Duas regras de projeto que valem a leitura antes de mexer aqui:

**``mtime`` não é fonte de idade.** Nenhuma decisão de TTL neste módulo
olha ``st_mtime``. O mtime é reescrito por ``git clone``, restore de backup
e rebuild de container — depois de qualquer deploy, todo arquivo parece
recém-criado e o lifecycle inteiro para em silêncio, reportando "0
candidatos" como se estivesse tudo em ordem. As fontes usadas são todas
versionadas: o ``id`` da nota (``YYYYMMDD-HHMMSS``), o campo ``cooled_at``
do frontmatter, e o nome do diretório ``_archive/YYYYMM/``.

**O disco é medido em blocos, não em bytes aparentes.** O que enche a VPS
é o espaço ocupado, e um repositório com milhares de objetos soltos paga
um bloco inteiro por objeto de 200 bytes. No bundle real medido em
2026-08-08, ``.git`` tinha 7,9 MB aparentes e **16 MB em disco** — a
diferença é exatamente o problema que ``repo_maintenance`` resolve.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import BundleLayout
from .schema import validate_frontmatter

# ----- Defaults de política ------------------------------------------------
#
# Todos sobrescrevíveis pelo caller; os servidores expõem via env var.
ISOLATION_TTL_DAYS_DEFAULT = 90
COLD_TTL_DAYS_DEFAULT = 180
STORAGE_WARN_BYTES_DEFAULT = 500 * 1024 * 1024
STORAGE_CRIT_BYTES_DEFAULT = 750 * 1024 * 1024

# Acima disto, ``maintenance.recommended`` liga. 500 objetos soltos já
# custam ~2 MB em blocos num repo de notas pequenas — barato de empacotar,
# e a operação é não-destrutiva, então o limiar pode ser agressivo.
LOOSE_OBJECTS_THRESHOLD = 500


# ----- Idade: só fontes duráveis -------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def age_days_from_id(note_id: str, *, now: datetime | None = None) -> int | None:
    """Idade em dias a partir do ``id`` canônico ``YYYYMMDD-HHMMSS``.

    ``None`` quando o id não é canônico (rascunhos sem id, ids sintéticos
    ``__draft__:``) — o caller decide o que fazer, mas nunca deve cair em
    ``mtime`` como plano B.

    **Fallback para a data quando a HORA é inválida.** ``validate_id`` só
    checa o padrão (``^\\d{8}-\\d{6}$``), então ids como ``20260605-006000``
    (minuto 60) ou ``20260101-250000`` (hora 25) são aceitos e gravados. O
    ``strptime`` completo falha neles, e antes desta revisão a função
    devolvia ``None`` — o que tirava a nota de ``find_aging_candidates``
    **para sempre**, sem sinal nenhum: ela nunca virava candidata a ``cold``
    nem a ``_archive/``.

    Não é hipótese: em 2026-08-09 o bundle real tinha 14 notas nesse estado,
    todas da migração do vault, onde o próximo slot de horário é calculado
    somando 1 a ``HHMMSS`` como inteiro (``100059`` + 1 = ``100060``). A
    correção da geração cabe a quem escreve o id; aqui a função só deixa de
    perder a nota por causa dela.

    O fallback não perde precisão relevante: o retorno é em DIAS, e a parte
    de hora contribui no máximo com menos de um dia.
    """
    now = now or _now()
    try:
        created = datetime.strptime(note_id[:15], "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except (ValueError, IndexError):
        try:
            created = datetime.strptime(note_id[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None
    return max(0, (now - created).days)


def age_days_from_iso(timestamp: str | None, *, now: datetime | None = None) -> int | None:
    """Idade em dias a partir de um ISO 8601 UTC (ex.: ``cooled_at``)."""
    if not timestamp:
        return None
    now = now or _now()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, (now - parsed).days)


def age_days_from_archive_month(month: str, *, now: datetime | None = None) -> int | None:
    """Idade em dias a partir do nome do diretório ``_archive/YYYYMM/``.

    O mês já está no caminho — não há motivo para consultar o filesystem.
    Conta a partir do PRIMEIRO dia do mês (conservador: superestima a
    idade em no máximo 30 dias, nunca subestima).
    """
    now = now or _now()
    try:
        start = datetime.strptime(month, "%Y%m").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return max(0, (now - start).days)


# ----- Uso de disco ---------------------------------------------------------


def _entry_disk_bytes(entry: os.DirEntry | Path) -> int:
    """Espaço ocupado em disco por um arquivo, em bytes.

    ``st_blocks`` conta blocos de 512 bytes efetivamente alocados — é o que
    o ``du`` reporta e o que a VPS cobra. Cai para ``st_size`` (tamanho
    aparente) em plataformas sem ``st_blocks``, aceitando a subestimação
    em vez de falhar.
    """
    try:
        st = entry.stat(follow_symlinks=False) if isinstance(entry, os.DirEntry) else entry.stat()
    except OSError:
        return 0
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def _tree_usage(path: Path) -> tuple[int, int]:
    """``(contagem_de_arquivos, bytes_em_disco)`` de uma árvore inteira.

    ``os.scandir`` recursivo em vez de ``rglob`` — em diretórios com
    milhares de entradas (``.git/objects``) a diferença é de uma ordem de
    grandeza, e este caminho é chamado a cada refresh da UI.
    """
    if not path.exists():
        return (0, 0)
    count = 0
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    else:
                        count += 1
                        total += _entry_disk_bytes(entry)
        except OSError:
            continue
    return (count, total)


# ----- Modelos --------------------------------------------------------------


@dataclass(frozen=True)
class MaintenanceInfo:
    """Estado do repositório git e se vale compactar.

    ``estimated_reclaimable_bytes`` é uma estimativa deliberadamente
    conservadora: assume que o empacotamento recupera o que os objetos
    soltos ocupam além do seu tamanho aparente (o desperdício de bloco),
    sem prometer o ganho de delta compression, que depende do conteúdo.
    """

    loose_objects: int
    loose_bytes: int
    packs: int
    recommended: bool
    hint: str
    estimated_reclaimable_bytes: int = 0


@dataclass(frozen=True)
class StorageSummary:
    """Snapshot read-only do bundle INTEIRO, ``.git`` incluído."""

    total_bytes: int
    status: str  # "ok" | "warning" | "critical"
    by_dir: dict[str, Any]
    maintenance: MaintenanceInfo
    thresholds: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "total_bytes": self.total_bytes,
            "status": self.status,
            "by_dir": self.by_dir,
            "maintenance": {
                "loose_objects": self.maintenance.loose_objects,
                "loose_bytes": self.maintenance.loose_bytes,
                "packs": self.maintenance.packs,
                "recommended": self.maintenance.recommended,
                "hint": self.maintenance.hint,
                "estimated_reclaimable_bytes": self.maintenance.estimated_reclaimable_bytes,
            },
            "thresholds": self.thresholds,
        }


@dataclass(frozen=True)
class AgingCandidate:
    """Nota que cruzou um TTL e está pronta para a próxima transição."""

    note_id: str
    title: str | None
    path: Path
    age_days: int
    protected: bool
    lifecycle: str
    flag_kind: str  # "isolation_90d" | "cold_age_threshold"
    target: str  # "cold" | "archive"

    def to_dict(self) -> dict:
        return {
            "note_id": self.note_id,
            "title": self.title,
            "age_days": self.age_days,
            "protected": self.protected,
            "lifecycle": self.lifecycle,
            "flag_kind": self.flag_kind,
            "target": self.target,
        }


# ----- Git: inspeção e manutenção -------------------------------------------


def _git_object_stats(root: Path) -> tuple[int, int, int]:
    """``(objetos_soltos, bytes_soltos_em_disco, packs)``.

    Lê o layout de ``.git/objects`` diretamente em vez de chamar
    ``git count-objects``: não depende do binário e é o mesmo custo.
    """
    objects = root / ".git" / "objects"
    if not objects.is_dir():
        return (0, 0, 0)
    loose = 0
    loose_bytes = 0
    try:
        with os.scandir(objects) as it:
            for entry in it:
                # Fanout de objetos soltos: 256 diretórios de 2 hex chars.
                if not entry.is_dir(follow_symlinks=False):
                    continue
                if len(entry.name) != 2:
                    continue
                try:
                    int(entry.name, 16)
                except ValueError:
                    continue
                sub_count, sub_bytes = _tree_usage(Path(entry.path))
                loose += sub_count
                loose_bytes += sub_bytes
    except OSError:
        pass
    packs = 0
    pack_dir = objects / "pack"
    if pack_dir.is_dir():
        try:
            packs = sum(1 for p in pack_dir.iterdir() if p.suffix == ".pack")
        except OSError:
            packs = 0
    return (loose, loose_bytes, packs)


def _maintenance_info(root: Path) -> MaintenanceInfo:
    loose, loose_bytes, packs = _git_object_stats(root)
    recommended = loose >= LOOSE_OBJECTS_THRESHOLD
    if recommended:
        hint = f"git gc: {loose} objetos soltos, {packs} pack(s)"
    elif loose:
        hint = f"{loose} objetos soltos — abaixo do limiar de {LOOSE_OBJECTS_THRESHOLD}"
    else:
        hint = "repositório compactado"
    # Cada objeto solto desperdiça, em média, meio bloco de 4 KiB. É o piso
    # do ganho; o real costuma ser bem maior por causa da delta compression.
    estimated = loose * 2048 if recommended else 0
    return MaintenanceInfo(
        loose_objects=loose,
        loose_bytes=loose_bytes,
        packs=packs,
        recommended=recommended,
        hint=hint,
        estimated_reclaimable_bytes=estimated,
    )


def repo_maintenance(root: Path, layout: BundleLayout, *, dry_run: bool = True) -> dict:
    """Compacta o repositório git do bundle.

    **Não reescreve histórico, não expira reflog, não remove nenhuma nota.**
    Toda nota continua recuperável exatamente como antes — o que muda é só
    como os objetos estão armazenados. É por isso que esta operação não tem
    gate humano, ao contrário do ``memory_forget``: ela não destrói nada.

    Usa o ``git`` do sistema quando disponível (delta compression bem
    melhor) e cai para ``dulwich.porcelain.gc`` quando não há binário —
    assim funciona em imagem mínima sem depender de ``git`` no PATH.

    Medido no bundle real (286 notas, 532 commits, 2945 objetos soltos):
    ``git gc`` levou ``.git`` de 16 MB para 1,6 MB; o fallback dulwich, para
    7,9 MB. Ambos preservaram os 532 commits e passaram ``git fsck``.
    """
    before = _tree_usage(root / ".git")[1]
    info = _maintenance_info(root)

    if dry_run:
        return {
            "dry_run": True,
            "before_bytes": before,
            "after_bytes": before,
            "reclaimed_bytes": 0,
            "loose_before": info.loose_objects,
            "packs_before": info.packs,
            "recommended": info.recommended,
            "estimated_reclaimable_bytes": info.estimated_reclaimable_bytes,
            "backend": None,
        }

    started = datetime.now(timezone.utc)
    backend = "git"
    if shutil.which("git"):
        try:
            subprocess.run(
                ["git", "gc", "--quiet"],
                cwd=str(root),
                check=True,
                capture_output=True,
                timeout=300,
            )
        except (subprocess.SubprocessError, OSError):
            backend = "dulwich"
    else:
        backend = "dulwich"

    if backend == "dulwich":
        from dulwich import porcelain

        porcelain.gc(str(root))

    after = _tree_usage(root / ".git")[1]
    post = _maintenance_info(root)
    return {
        "dry_run": False,
        "before_bytes": before,
        "after_bytes": after,
        # Pode ser negativo em repositório já compactado (o pack novo
        # convive com o antigo por um instante). Não mascaramos — número
        # honesto é mais útil que zero otimista.
        "reclaimed_bytes": before - after,
        "loose_before": info.loose_objects,
        "loose_after": post.loose_objects,
        "packs_before": info.packs,
        "packs_after": post.packs,
        "backend": backend,
        "elapsed_ms": int((datetime.now(timezone.utc) - started).total_seconds() * 1000),
    }


# ----- Varredura do bundle --------------------------------------------------


def _iter_notes(root: Path, layout: BundleLayout):
    """Itera ``(path, frontmatter)`` das notas de ``notes/``.

    Glob NÃO-recursivo, deliberadamente igual ao do resto do core: é o
    contrato que faz uma nota "existir" para ``notes_read``. Se algum dia
    isto virar recursivo, tem que virar em ``zettel.py`` e ``graph.py``
    juntos — foi exatamente a divergência entre ``rg`` (recursivo) e o glob
    (não) que inviabilizou o desenho de ``notes/_cold/`` na v1 da P11.
    """
    notes_dir = root / layout.notes_dir
    if not notes_dir.is_dir():
        return
    for path in sorted(notes_dir.glob(f"*{layout.notes_extension}")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            from .frontmatter import split_frontmatter

            raw_fm, _ = split_frontmatter(text)
        except Exception:
            continue
        fm, _ = validate_frontmatter(raw_fm or {})
        if fm is None:
            continue
        yield path, fm


def _archive_by_month(root: Path, layout: BundleLayout) -> list[dict]:
    archive = root / layout.archive_dir
    if not archive.is_dir():
        return []
    months: list[dict] = []
    try:
        entries = sorted(p for p in archive.iterdir() if p.is_dir())
    except OSError:
        return []
    for month_dir in entries:
        count, size = _tree_usage(month_dir)
        months.append(
            {
                "month": month_dir.name,
                "count": count,
                "bytes": size,
                "age_days": age_days_from_archive_month(month_dir.name),
            }
        )
    return months


def get_storage_summary(
    root: Path,
    layout: BundleLayout,
    *,
    cold_ttl_days: int = COLD_TTL_DAYS_DEFAULT,
    warn_bytes: int = STORAGE_WARN_BYTES_DEFAULT,
    crit_bytes: int = STORAGE_CRIT_BYTES_DEFAULT,
) -> StorageSummary:
    """Snapshot read-only do uso de disco do bundle inteiro.

    Mede ``notes/`` (separando ``active`` de ``cold``), ``_archive/`` por
    mês, os ``extra_dirs`` do layout, ``graphify-out/`` e **``.git/``**.

    Incluir ``.git`` não é detalhe: no bundle real ele é 85% do total. Uma
    medição que o ignore reporta "ok" com o disco dez vezes maior que o
    número exibido — foi o erro que a v1 da P11 cometeu ao justificar um
    caminho destrutivo com uma medida que não via o problema.
    """
    notes_count, notes_bytes = _tree_usage(root / layout.notes_dir)
    active = cold = 0
    for _, fm in _iter_notes(root, layout):
        if getattr(fm, "lifecycle", "active") == "cold":
            cold += 1
        else:
            active += 1

    archive_months = _archive_by_month(root, layout)
    archive_count = sum(m["count"] for m in archive_months)
    archive_bytes = sum(m["bytes"] for m in archive_months)

    by_dir: dict[str, Any] = {
        f"{layout.notes_dir}/": {
            "count": notes_count,
            "bytes": notes_bytes,
            "active": active,
            "cold": cold,
        },
        f"{layout.archive_dir}/": {
            "count": archive_count,
            "bytes": archive_bytes,
            "by_month": archive_months,
            "oldest_month": archive_months[0]["month"] if archive_months else None,
        },
    }
    for extra in layout.extra_dirs:
        count, size = _tree_usage(root / extra)
        by_dir[f"{extra}/"] = {"count": count, "bytes": size}

    graph_count, graph_bytes = _tree_usage(root / "graphify-out")
    by_dir["graphify-out/"] = {
        "count": graph_count,
        "bytes": graph_bytes,
        # Artefato do ``cm-graph-rebuild``: pode ser apagado a qualquer
        # momento e regenerado. A UI usa isto para oferecer a limpeza
        # sem assustar.
        "regenerable": True,
    }

    git_count, git_bytes = _tree_usage(root / ".git")
    by_dir[".git/"] = {"count": git_count, "bytes": git_bytes}

    total = sum(int(v.get("bytes", 0)) for v in by_dir.values())
    if total >= crit_bytes:
        status = "critical"
    elif total >= warn_bytes:
        status = "warning"
    else:
        status = "ok"

    return StorageSummary(
        total_bytes=total,
        status=status,
        by_dir=by_dir,
        maintenance=_maintenance_info(root),
        thresholds={
            "warn_bytes": warn_bytes,
            "crit_bytes": crit_bytes,
            "cold_ttl_days": cold_ttl_days,
        },
    )


def find_aging_candidates(
    root: Path,
    layout: BundleLayout,
    *,
    connected_ids: set[str] | None = None,
    isolation_ttl_days: int = ISOLATION_TTL_DAYS_DEFAULT,
    cold_ttl_days: int = COLD_TTL_DAYS_DEFAULT,
    now: datetime | None = None,
) -> list[AgingCandidate]:
    """Notas prontas para a próxima transição de lifecycle.

    Args:
        connected_ids: ids que têm alguma conexão no grafo (entrada OU
            saída). Calculado pelo caller — o core não conhece a política
            de "o que conta como conexão", e o CM já computa isso em
            ``memory_stats``.
        isolation_ttl_days: idade mínima (desde a criação) para uma nota
            desconectada virar candidata a ``cold``.
        cold_ttl_days: tempo mínimo em ``cold`` para virar candidata a
            ``_archive/``.

    Notas ``protected`` aparecem na lista com ``protected=True`` em vez de
    serem omitidas: quem chama precisa saber que elas cruzaram o TTL e
    foram poupadas, senão a flag vira uma decisão invisível. Cabe ao
    caller pular a ação.

    Idade vem de ``id`` e ``cooled_at`` — nunca de ``mtime``.
    """
    connected = connected_ids or set()
    now = now or _now()
    out: list[AgingCandidate] = []

    for path, fm in _iter_notes(root, layout):
        note_id = fm.id or path.stem
        lifecycle = getattr(fm, "lifecycle", "active")
        protected = bool(getattr(fm, "protected", False))

        if lifecycle == "cold":
            age = age_days_from_iso(getattr(fm, "cooled_at", None), now=now)
            if age is not None and age >= cold_ttl_days:
                out.append(
                    AgingCandidate(
                        note_id=note_id,
                        title=fm.title,
                        path=path,
                        age_days=age,
                        protected=protected,
                        lifecycle=lifecycle,
                        flag_kind="cold_age_threshold",
                        target="archive",
                    )
                )
            continue

        # active: só é candidata se estiver desconectada E velha o bastante.
        if note_id in connected:
            continue
        age = age_days_from_id(note_id, now=now)
        if age is None or age < isolation_ttl_days:
            continue
        out.append(
            AgingCandidate(
                note_id=note_id,
                title=fm.title,
                path=path,
                age_days=age,
                protected=protected,
                lifecycle=lifecycle,
                flag_kind="isolation_90d",
                target="cold",
            )
        )

    out.sort(key=lambda c: c.age_days, reverse=True)
    return out
