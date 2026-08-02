// PERCIVAL: wrapper da Sidebar original do upstream.
// Decisão G2-AltB (2026-08-01): composição por fora, SEM patch em Sidebar.tsx.
// Decisão B2 (revisada): link KG renderizado como irmão, abaixo do footer.
// Decisão B4: ícone Lucide-react (Network ou Share2).
// Decisão B2: Settings continua visível e funcional (esconder está em suspenso).
// Extensibilidade: futuros botões no rodapé (mesmo padrão) entram como
// irmãos do <a> KG abaixo — sem patch em Sidebar.tsx.
import { Network } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar as UpstreamSidebar } from "@/components/Sidebar";
import { resolveKgInterfaceUrl } from "@/lib/kg-interface";
import { cn } from "@/lib/utils";

export function PercivalSidebar(
  props: React.ComponentProps<typeof UpstreamSidebar>,
) {
  const { t } = useTranslation();
  const kgUrl = resolveKgInterfaceUrl();
  // PERCIVAL: achado de revisão integrada — o link KG ignorava `props.collapsed`,
  // então no modo rail (56px, ver SIDEBAR_RAIL_WIDTH em App.tsx) o texto "Knowledge
  // Graph" não cabia e vazava para fora da sidebar (confirmado renderizando o CSS
  // real compilado num browser headless). Espelha o mesmo padrão de
  // SidebarActionButton (Sidebar.tsx): ícone centrado + label recolhida via
  // max-width/opacity, com `title` como tooltip no lugar do label visível.
  const collapsed = Boolean(props.collapsed);
  const kgLabel = t("sidebar.knowledgeGraph");

  return (
    // PERCIVAL: UpstreamSidebar's own root is `h-full` — as a plain flow sibling, the
    // KG link would render *after* that 100%-height nav and get clipped by the
    // `overflow-hidden` ancestors that wrap Sidebar everywhere in App.tsx (invisible,
    // 0 visible pixels; confirmed by rendering the real compiled CSS in a headless
    // browser). `flex-1 min-h-0` on the Sidebar's wrapper makes it share height with
    // the KG row instead of claiming all of it, so Sidebar's own footer
    // (Settings/ConnectionBadge) stays fully visible and the KG link gets a real row
    // below it, with no clipping and no overlap.
    <div className="relative flex h-full w-full flex-col">
      <div className="min-h-0 flex-1 overflow-hidden">
        <UpstreamSidebar {...props} />
      </div>
      {/* PERCIVAL: link Knowledge Graph no rodapé (B2 revisada, G2-AltB). */}
      <a
        href={kgUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={kgLabel}
        title={collapsed ? kgLabel : undefined}
        className={cn(
          "flex shrink-0 items-center gap-2 overflow-hidden py-3 text-xs text-sidebar-foreground hover:bg-sidebar-accent/75",
          "transition-[width,padding] duration-300 ease-out",
          collapsed ? "w-14 justify-center px-0" : "w-full justify-start px-2.5",
        )}
      >
        <Network className="h-4 w-4 shrink-0" aria-hidden />
        <span
          className={cn(
            "min-w-0 overflow-hidden truncate whitespace-nowrap transition-[max-width,opacity] duration-200 ease-out",
            collapsed ? "max-w-0 opacity-0" : "max-w-[12rem] opacity-100",
          )}
        >
          {kgLabel}
        </span>
      </a>
    </div>
  );
}
