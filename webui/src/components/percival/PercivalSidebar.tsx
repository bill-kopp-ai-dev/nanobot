// PERCIVAL: wrapper da Sidebar original do upstream.
// Decisão G2-AltB (2026-08-01): composição por fora, SEM patch em Sidebar.tsx.
// Decisão B2 (revisada 2026-08-02): link KG renderizado como card elegante,
// centralizado, ACIMA do rodapé do upstream (Settings/ConnectionBadge) — sem
// patch em Sidebar.tsx, mantendo Settings visível e funcional.
// Decisão B4: ícone Lucide-react (Network).
// Extensibilidade: futuros botões no rodapé entram pelo mesmo padrão (overlay
// absoluto sobre o footer do upstream ou slot reservado no wrapper).
import { ArrowUpRight, Network } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar as UpstreamSidebar } from "@/components/Sidebar";
import { resolveKgInterfaceUrl } from "@/lib/kg-interface";
import { cn } from "@/lib/utils";

// PERCIVAL: o footer interno do UpstreamSidebar (Sidebar.tsx) tem `py-3`
// (12+12) + `h-8` do botão Settings/ConnectionBadge = ~56px quando expandido.
// Posicionamos o card KG com `bottom-[60px]` (4px acima do footer) pra ele
// flutuar visualmente sobre a área entre o fim da lista de chats e o botão
// Settings, sem cobrir o Settings.
const KG_CARD_BOTTOM_OFFSET_EXPANDED = "bottom-[60px]";

export function PercivalSidebar(
  props: React.ComponentProps<typeof UpstreamSidebar>,
) {
  const { t } = useTranslation();
  const kgUrl = resolveKgInterfaceUrl();
  // PERCIVAL: achado de revisão integrada — o link KG ignorava `props.collapsed`,
  // então no modo rail (56px, ver SIDEBAR_RAIL_WIDTH em App.tsx) o texto "Knowledge
  // Graph" não cabia e vazava para fora da sidebar. Em modo collapsed, mantemos o
  // fallback icon-only (mesmo padrão de SidebarActionButton em Sidebar.tsx):
  // ícone centrado + label recolhida via max-width/opacity, com `title` como
  // tooltip no lugar do label visível.
  const collapsed = Boolean(props.collapsed);
  const kgLabel = t("sidebar.knowledgeGraph");

  return (
    // PERCIVAL: UpstreamSidebar's own root is `h-full` — as a plain flow sibling, the
    // KG link would render *after* that 100%-height nav and get clipped by the
    // `overflow-hidden` ancestors that wrap Sidebar everywhere in App.tsx. O
    // wrapper `relative flex h-full flex-col` mantém o KG link visível: o
    // UpstreamSidebar ocupa `flex-1 min-h-0` e o card KG é posicionado de forma
    // absoluta sobre o footer do upstream (sem patch em Sidebar.tsx), flutuando
    // visualmente acima de Settings.
    <div className="relative flex h-full w-full flex-col">
      <div className="min-h-0 flex-1 overflow-hidden">
        <UpstreamSidebar {...props} />
      </div>
      {/* PERCIVAL: card KG elegante, centralizado, ACIMA do footer do upstream.
          Em modo expandido (largura 272px), o card flutua como uma pílula com
          borda/sombra/fundo gradiente, com ícone Network num quadrado, label e
          um indicador externo (ArrowUpRight) sinalizando que abre fora da app.
          Em modo collapsed (rail 56px), cai pro fallback icon-only pra não
          bloquear Settings (não há largura pro card). */}
      {!collapsed ? (
        <div
          data-testid="kg-card-slot"
          className={cn(
            "pointer-events-none absolute inset-x-0 z-10 flex justify-center px-3",
            KG_CARD_BOTTOM_OFFSET_EXPANDED,
          )}
        >
          <a
            href={kgUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={kgLabel}
            title={kgLabel}
            className={cn(
              "pointer-events-auto group relative flex w-full max-w-[15rem] items-center gap-2.5 overflow-hidden rounded-xl",
              "border border-sidebar-border/70 bg-gradient-to-br from-sidebar to-sidebar-accent/55",
              "px-3 py-2.5 text-[12.5px] font-medium text-sidebar-foreground",
              "shadow-[0_6px_18px_-8px_rgba(15,23,42,0.18),inset_0_1px_0_hsl(var(--background)/0.6)]",
              "transition-[transform,box-shadow,border-color] duration-200 ease-out",
              "hover:-translate-y-px hover:border-sidebar-border hover:shadow-[0_10px_24px_-8px_rgba(15,23,42,0.24),inset_0_1px_0_hsl(var(--background)/0.6)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40",
            )}
          >
            <span
              className={cn(
                "grid h-7 w-7 shrink-0 place-items-center rounded-lg",
                "bg-foreground/10 text-sidebar-foreground",
                "transition-colors group-hover:bg-foreground/15",
              )}
              aria-hidden
            >
              <Network className="h-3.5 w-3.5" />
            </span>
            <span className="min-w-0 flex-1 truncate">{kgLabel}</span>
            <ArrowUpRight
              className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70 transition-transform group-hover:-translate-y-px group-hover:translate-x-px group-hover:text-sidebar-foreground"
              aria-hidden
            />
          </a>
        </div>
      ) : (
        <a
          href={kgUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={kgLabel}
          title={kgLabel}
          className={cn(
            "flex shrink-0 items-center gap-2 overflow-hidden py-3 text-xs text-sidebar-foreground hover:bg-sidebar-accent/75",
            "transition-[width,padding] duration-300 ease-out",
            "w-14 justify-center px-0",
          )}
        >
          <Network className="h-4 w-4 shrink-0" aria-hidden />
          <span
            className={cn(
              "min-w-0 max-w-0 overflow-hidden truncate whitespace-nowrap opacity-0",
              "transition-[max-width,opacity] duration-200 ease-out",
            )}
          >
            {kgLabel}
          </span>
        </a>
      )}
    </div>
  );
}
