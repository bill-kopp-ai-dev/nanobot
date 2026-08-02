// PERCIVAL: wrapper da Sidebar original do upstream.
// Decisão G2-AltB (2026-08-01): composição por fora, SEM patch em Sidebar.tsx.
// Decisão B2 (revisada 2026-08-02): link KG renderizado como card elegante,
// centralizado, ACIMA do rodapé do upstream (Settings/ConnectionBadge) — sem
// patch em Sidebar.tsx, mantendo Settings visível e funcional.
// Decisão B2-2 (2026-08-02): adicionar 2º card externo (Positronic Bean)
// abaixo do KG, mesmo padrão visual.
// Decisão B4: ícone Lucide-react (Network para KG, Sprout para Positronic
// Bean — broto/semente combina com "Bean" + labs; distinto do Network).
// Extensibilidade: futuros botões no rodapé entram pelo mesmo padrão
// (slot com cards flex-col).
import { ArrowUpRight, type LucideIcon, Network, Sprout } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar as UpstreamSidebar } from "@/components/Sidebar";
import { resolveKgInterfaceUrl } from "@/lib/kg-interface";
import { resolvePositronicBeanUrl } from "@/lib/positronic-bean";
import { cn } from "@/lib/utils";

// PERCIVAL: o footer interno do UpstreamSidebar (Sidebar.tsx) tem `py-3`
// (12+12) + `h-8` do botão Settings/ConnectionBadge = ~56px quando expandido.
// Posicionamos o slot dos cards externos com `bottom-[60px]` (4px acima
// do footer) pra eles flutuarem visualmente sobre a área entre o fim da
// lista de chats e o botão Settings, sem cobrir Settings. O slot é flex-col
// e empilha KG (topo) + Positronic Bean (embaixo) com gap-1.5 (~6px).
const EXTERNAL_CARDS_BOTTOM_OFFSET_EXPANDED = "bottom-[60px]";

export function PercivalSidebar(
  props: React.ComponentProps<typeof UpstreamSidebar>,
) {
  const { t } = useTranslation();
  const kgUrl = resolveKgInterfaceUrl();
  const pbUrl = resolvePositronicBeanUrl();
  // PERCIVAL: achado de revisão integrada — o link KG ignorava `props.collapsed`,
  // então no modo rail (56px, ver SIDEBAR_RAIL_WIDTH em App.tsx) o texto "Knowledge
  // Graph" não cabia e vazava para fora da sidebar. Em modo collapsed, mantemos o
  // fallback icon-only (mesmo padrão de SidebarActionButton em Sidebar.tsx):
  // ícone centrado + label recolhida via max-width/opacity, com `title` como
  // tooltip no lugar do label visível. Positronic Bean só renderiza expandido.
  const collapsed = Boolean(props.collapsed);
  const kgLabel = t("sidebar.knowledgeGraph");
  const pbLabel = t("sidebar.positronicBean");

  return (
    // PERCIVAL: UpstreamSidebar's own root is `h-full` — as a plain flow sibling, the
    // KG link would render *after* that 100%-height nav and get clipped by the
    // `overflow-hidden` ancestors that wrap Sidebar everywhere in App.tsx. O
    // wrapper `relative flex h-full flex-col` mantém os cards externos visíveis: o
    // UpstreamSidebar ocupa `flex-1 min-h-0` e o slot externo é posicionado de
    // forma absoluta sobre o footer do upstream (sem patch em Sidebar.tsx),
    // flutuando visualmente acima de Settings.
    <div className="relative flex h-full w-full flex-col">
      <div className="min-h-0 flex-1 overflow-hidden">
        <UpstreamSidebar {...props} />
      </div>
      {/* PERCIVAL: cards externos (KG + Positronic Bean), centralizados, ACIMA
          do footer do upstream. Em modo expandido (largura 272px), o slot
          empilha 2 cards com estilo elegante: borda + sombra + fundo gradiente,
          ícone num quadrado tinted, label e ArrowUpRight indicando recurso
          externo. Em modo collapsed (rail 56px), cai pro fallback icon-only
          (só KG; Positronic Bean é omitido pra não poluir o rail). */}
      {!collapsed ? (
        <div
          data-testid="external-cards-slot"
          className={cn(
            "pointer-events-none absolute inset-x-0 z-10 flex flex-col items-stretch gap-1.5 px-3",
            EXTERNAL_CARDS_BOTTOM_OFFSET_EXPANDED,
          )}
        >
          <ExternalSidebarCard
            href={kgUrl}
            label={kgLabel}
            Icon={Network}
          />
          <ExternalSidebarCard
            href={pbUrl}
            label={pbLabel}
            Icon={Sprout}
          />
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

// PERCIVAL: sub-componente interno para cards externos no rodapé da sidebar.
// Mesmo padrão visual do card KG original (revisão 2026-08-02), agora
// parametrizado por href/label/Icon para suportar múltiplos destinos
// (KG, Positronic Bean, futuros). Mantém border + shadow + gradiente +
// ArrowUpRight indicador externo.
type ExternalSidebarCardProps = {
  href: string;
  label: string;
  Icon: LucideIcon;
};

function ExternalSidebarCard({ href, label, Icon }: ExternalSidebarCardProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      title={label}
      className={cn(
        "pointer-events-auto group relative flex w-full items-center gap-2.5 overflow-hidden rounded-xl",
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
        <Icon className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0 flex-1 truncate">{label}</span>
      <ArrowUpRight
        className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70 transition-transform group-hover:-translate-y-px group-hover:translate-x-px group-hover:text-sidebar-foreground"
        aria-hidden
      />
    </a>
  );
}