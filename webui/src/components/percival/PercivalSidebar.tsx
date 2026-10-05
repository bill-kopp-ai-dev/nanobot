// PERCIVAL: wrapper da Sidebar original do upstream.
// Decisão G2-AltB (2026-08-01): composição por fora, SEM patch em Sidebar.tsx.
// Decisão B2 (revisada 2026-08-02): link KG renderizado como card elegante,
// centralizado, ACIMA do rodapé do upstream (Settings/ConnectionBadge) — sem
// patch em Sidebar.tsx, mantendo Settings visível e funcional.
// Decisão B2-2 (2026-08-02): adicionar 2º card externo (Positronic Bean)
// abaixo do KG, mesmo padrão visual.
// Decisão B2-3 (2026-08-02 — revisão visual da barra contraída):
// adicionar Positronic Bean também no rail (56px) preservando a ordem
// KG → Positronic Bean → Settings → ConnectionBadge. Slot externo usa
// DOIS layouts distintos: absolute com bottom-[60px] no expandido (cards
// flutuam sobre o fundo da sidebar) e flow normal no rail (cards ficam
// entre o body do upstream e o footer, com gap-1.5 explícito).
// Decisão B4: ícone Lucide-react (Network para KG, Sprout para Positronic
// Bean — broto/semente combina com "Bean" + labs; distinto do Network).

import { ArrowUpRight, type LucideIcon, Brain, Sprout } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar as UpstreamSidebar } from "@/components/Sidebar";
import { resolveKgInterfaceUrl } from "@/lib/kg-interface";
import { resolvePositronicBeanUrl } from "@/lib/positronic-bean";
import { cn } from "@/lib/utils";

// PERCIVAL: offset vertical do slot ABSOLUTO no modo expandido. O footer
// do upstream tem ~60px quando expandido (py-3 24px + Settings h-8 32px
// + ConnectionBadge ~4px = 60px). 4px acima dele em absolute os cards
// ficam visualmente sobre a área entre o fim da lista de chats e o
// rodapé, sem cobrir Settings. No rail o layout muda pra flow normal
// (ver ``renderExternalCardsSlot`` mais abaixo).
const EXTERNAL_CARDS_BOTTOM_OFFSET_EXPANDED = "bottom-[60px]";

// PERCIVAL: tamanho do quadrado de ícone 32×32 no rail. Foi decidido que
// tanto KG quanto PB card ficam ``h-8 w-8`` no rail (mesma dimensão do
// action button do upstream ``SidebarActionButton``, que também usa h-8
// no rail) — uniformidade visual entre os ícones do rail, sem
// destacar um botão como "principal".
const RAIL_ICON_BOX = "h-8 w-8";

export function PercivalSidebar(
  props: React.ComponentProps<typeof UpstreamSidebar>,
) {
  const { t } = useTranslation();
  const kgUrl = resolveKgInterfaceUrl();
  const pbUrl = resolvePositronicBeanUrl();
  // PERCIVAL: achado de revisão integrada — o link KG ignorava `props.collapsed`,
  // então no modo rail (56px, ver SIDEBAR_RAIL_WIDTH em App.tsx) o texto "Knowledge
  // Graph" não cabia e vazava para fora da sidebar. Em modo collapsed, mantemos o
  // fallback icon-only: ícone centrado, com `title` como tooltip.
  const collapsed = Boolean(props.collapsed);
  const kgLabel = t("sidebar.knowledgeGraph");
  const pbLabel = t("sidebar.positronicBean");

  return (
    // PERCIVAL: UpstreamSidebar's own root is `h-full` — as a plain flow sibling, the
    // KG link would render *after* that 100%-height nav and get clipped by the
    // `overflow-hidden` ancestors that wrap Sidebar everywhere in App.tsx. O
    // wrapper `relative flex h-full flex-col` mantém os cards externos visíveis.
    //
    // No modo expandido: o slot externo é ``absolute bottom-[60px]`` flutuando
    // sobre o fundo, com os cards de 256-ish px de largura.
    //
    // No modo rail (56px): SEM absolute. Aqui, absolute causava dois bugs:
    //   1. Positronic Bean icon-only (32×32) tem que caber visualmente,
    //   então entra no flow normal — após o body e antes do footer do upstream.
    //   2. ``bottom-[60px]`` é computado relativo ao wrapper externo, e o
    //   footer do upstream no rail cresce mais que 60px
    //   (``py-3 24px + h-8 32px + gap-1 4px + h-8 32px = 92px``) ⇒ os
    //   ícones acabavam renderizando DENTRO do footer, visualmente
    //   sobrepostos aos controles. Usando flow normal com ``gap-1.5``
    //   e ``pb-2`` o espaçamento fica explícito em CSS, e o alinhamento
    //   visual segue a ordenação KG → PB → Settings → Badge de cima
    //   pra baixo, idêntica à expandida.
    <div className={cn("relative flex h-full w-full flex-col", collapsed && "min-h-0")}>
      <div className="min-h-0 flex-1 overflow-hidden">
        <UpstreamSidebar {...props} />
      </div>
      {renderExternalCardsSlot({ collapsed, kgUrl, pbUrl, kgLabel, pbLabel })}
    </div>
  );
}

// PERCIVAL: helper que retorna o slot externo no layout certo pro modo
// (expandido = absolute bottom-[60px]; rail = flow + gap explícito).
// Extraído pra manter o ``PercivalSidebar`` legível: cada ramo é curto
// e os comentários explicam o "porquê" do posicionamento escolhido.
function renderExternalCardsSlot(args: {
  collapsed: boolean;
  kgUrl: string;
  pbUrl: string;
  kgLabel: string;
  pbLabel: string;
}) {
  const { collapsed, kgUrl, pbUrl, kgLabel, pbLabel } = args;

  if (collapsed) {
    // Modo rail: flow normal. A ``<div>`` externa é irmã do wrapper do
    // UpstreamSidebar (que é o primeiro filho do wrapper PercivalSidebar).
    // Aqui ela entra NO FLOW entre o body do upstream e o footer (que é
    // o terceiro e último filho do <nav> interno do upstream — embora
    // pareça "depois", o flex column do nosso wrapper reorganiza: footer
    // do upstream vai pro fim naturalmente, mas como o upstream ocupa
    // flex-1, o slot fica visualmente entre o body e a borda inferior
    // do rail).
    //
    // ATENÇÃO: no rail o UpstreamSidebar renderiza o footer com altura
    // ~92px (py-3 + h-8 + gap + h-8). Se o slot externo for empilhado
    // DEPOIS do upstream, fica depois do footer, certo? Mas queremos
    // ENTRE body e footer — pra isso usamos ``absolute`` de novo, mas
    // dessa vez com offset calculado pelo tamanho do footer.
    //
    // Decisão final unificada (revisão 2026-08-02): no rail, o slot é
    // ``absolute bottom-[96px]`` (footer ~92px + 4px de respiro). Mesmo
    // padrão do expandido, mas o offset é diferente. Simplifica o layout
    // e garante que os ícones ficam ACIMA do footer visualmente, com
    // espaçamento consistente.
    return (
      <div
        data-testid="external-cards-slot"
        className={cn(
          "pointer-events-none absolute inset-x-0 z-10 flex flex-col items-center gap-2 px-0",
          "bottom-[96px]",
        )}
      >
        <RailIconLink href={kgUrl} label={kgLabel} Icon={Brain} />
        <RailIconLink href={pbUrl} label={pbLabel} Icon={Sprout} />
      </div>
    );
  }

  // Modo expandido: absolute bottom-[60px], cards elegantes centrados,
  // flutuando sobre o fundo da sidebar entre o body e o footer. KG
  // primeiro (Network), Positronic Bean abaixo (Sprout). Cada card tem
  // ~40px de altura; gap-1.5 (~6px) entre eles; width ``flex-1`` via
  // ``items-stretch`` centraliza o conjunto dentro do slot com
  // ``px-3`` de respiro lateral.
  return (
    <div
      data-testid="external-cards-slot"
      className={cn(
        "pointer-events-none absolute inset-x-0 z-10 flex flex-col items-stretch gap-1.5 px-3",
        EXTERNAL_CARDS_BOTTOM_OFFSET_EXPANDED,
      )}
    >
      <ExternalSidebarCard href={kgUrl} label={kgLabel} Icon={Brain} />
      <ExternalSidebarCard
        href={pbUrl}
        label={pbLabel}
        Icon={Sprout}
      />
    </div>
  );
}

// PERCIVAL: link externo no estilo icon-only, específico do rail. Quadrado
// 32×32 (``h-8 w-8``), ícone Lucide 16×16 centralizado, hover estilo
// SidebarActionButton (rounded-lg + bg-accent/75). ``title`` para
// tooltip, ``aria-label`` para a11y.
function RailIconLink({
  href,
  label,
  Icon,
}: {
  href: string;
  label: string;
  Icon: LucideIcon;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      title={label}
      data-testid="rail-icon-link"
      className={cn(
        "pointer-events-auto grid place-items-center rounded-lg",
        RAIL_ICON_BOX,
        "text-sidebar-foreground hover:bg-sidebar-accent/75",
        "transition-colors duration-200 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40",
      )}
    >
      <Icon className="h-4 w-4" aria-hidden />
    </a>
  );
}

// PERCIVAL: sub-componente interno para cards externos no rodapé da
// sidebar no modo EXPANDIDO. Mesmo padrão visual do card KG original
// (revisão 2026-08-02), agora parametrizado por href/label/Icon para
// suportar múltiplos destinos (KG, Positronic Bean, futuros). Mantém
// border + shadow + gradiente + ArrowUpRight indicador externo.
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
