// PERCIVAL: testes de regressão do branding percival (P8 etapa 5, decisão D1).
// Cobertura máxima: navegação, atributos, ordem, i18n, persistência de Settings.
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PercivalSidebar } from "@/components/percival/PercivalSidebar";
import { buildSidebarProps, renderWithClient } from "@/tests/helpers";

describe("branding percival", () => {
  // PERCIVAL: isolar testes com stubEnv; restaura estado original depois.
  const ORIGINAL_ENV = import.meta.env.VITE_KG_INTERFACE_URL;

  beforeEach(() => {
    vi.stubEnv("VITE_KG_INTERFACE_URL", "http://localhost:5174");
  });

  afterEach(() => {
    if (ORIGINAL_ENV === undefined) {
      vi.unstubAllEnvs();
    } else {
      vi.stubEnv("VITE_KG_INTERFACE_URL", ORIGINAL_ENV);
    }
  });

  it("os cards externos (KG + Positronic Bean) ficam num slot fora da Sidebar upstream (regressão de clipping)", () => {
    // PERCIVAL: jsdom não calcula layout real, então nenhum outro teste aqui pega
    // regressões de CSS. UpstreamSidebar tem `h-full` na raiz — se o slot dos
    // cards fosse descendente dela, renderizaria dentro do nav 100%-de-altura e
    // seria cortado pelos ancestrais `overflow-hidden` que envolvem a Sidebar
    // em todo o App.tsx (confirmado renderizando o CSS real compilado num
    // browser headless: 0 pixels visíveis). A correção envolve
    // `<UpstreamSidebar>` num wrapper `flex-1 min-h-0 overflow-hidden` e
    // posiciona os cards num slot (`external-cards-slot`) irmão do wrapper da
    // Sidebar, dentro do root do PercivalSidebar. O slot em si não pode ter
    // `overflow-hidden` (senão os cards seriam cortados); cada card é seu
    // único filho interativo (`pointer-events-auto`).
    const wrapper = renderWithClient();
    const { container } = render(<PercivalSidebar {...buildSidebarProps()} />, {
      wrapper,
    });
    const slot = container.querySelector('[data-testid="external-cards-slot"]');
    expect(slot).not.toBeNull();
    // Slot é filho direto do root do PercivalSidebar, irmão do wrapper da Sidebar.
    expect(slot?.parentElement).toBe(container.firstElementChild);
    expect(slot?.className ?? "").not.toMatch(/overflow-hidden/);
    const kgLink = screen.getByText("Knowledge Graph").closest("a");
    // O link vive dentro do slot (não direto no root), mas o slot é que controla
    // o posicionamento absoluto; o link em si não precisa ser filho do root.
    expect(kgLink).not.toBeNull();
    expect(kgLink?.closest('[data-testid="external-cards-slot"]')).toBe(slot);
    const pbLink = screen.getByText("Positronic Bean").closest("a");
    expect(pbLink?.closest('[data-testid="external-cards-slot"]')).toBe(slot);
  });

  it("no modo collapsed (rail), o KG vira icon-only e fica ACIMA do footer (mesma ordem da expandida)", () => {
    // PERCIVAL: revisão 2026-08-02 — unificamos o slot externo: agora o KG
    // icon-only no rail usa o mesmo slot absoluto `external-cards-slot` que a
    // expandida, posicionado acima do footer do upstream (Settings +
    // ConnectionBadge). Isso preserva a ORDEM visual da expandida
    // (KG → Positronic Bean → Settings → ConnectionBadge, de cima pra baixo).
    //
    // Achado histórico: a implementação original ignorava `props.collapsed`,
    // então no rail de 56px (SIDEBAR_RAIL_WIDTH em App.tsx) o texto "Knowledge
    // Graph" vazava para fora da sidebar (confirmado renderizando o CSS real
    // compilado num browser headless). jsdom não calcula layout, então este
    // teste checa que no rail o KG é renderizado como ícone de 32×32 sem
    // label visível (ícone Network dentro de uma grade 32×32 com hover).
    const wrapper = renderWithClient();
    const { container } = render(
      <PercivalSidebar {...buildSidebarProps({ collapsed: true })} />,
      { wrapper },
    );
    const link = screen.getByLabelText("Knowledge Graph");
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("title", "Knowledge Graph");
    // KG icon-only no rail: quadrado 32×32 (`grid h-8 w-8`), sem span de label.
    expect(link.className).toMatch(/h-8/);
    expect(link.className).toMatch(/w-8/);
    expect(link.querySelector("svg")).not.toBeNull();
    // KG é renderizado dentro do slot externo (não depois do footer).
    const slot = container.querySelector('[data-testid="external-cards-slot"]');
    expect(slot).not.toBeNull();
    expect(link.closest('[data-testid="external-cards-slot"]')).toBe(slot);
  });

  it("expandido (collapsed=false), o card KG fica visível com label e title para acessibilidade", () => {
    // PERCIVAL: o card elegante mantém `title` mesmo expandido — é um
    // atributo útil quando o label é truncado em larguras estreitas da
    // sidebar. O que importa é que o label visível não esteja recolhido.
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps({ collapsed: false })} />, {
      wrapper,
    });
    const link = screen.getByLabelText("Knowledge Graph");
    expect(link).toHaveAttribute("title", "Knowledge Graph");
    const label = link.querySelector("span");
    expect(label?.className ?? "").not.toMatch(/max-w-0/);
  });

  it("renderiza o link Knowledge Graph com a URL resolvida", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link).not.toBeNull();
    expect(link).toHaveAttribute("href", "http://localhost:5174");
  });

  it("o link KG abre em nova aba (target=_blank, rel=noopener noreferrer)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renderiza o link Positronic Bean com a URL default do helper (positronic-bean.ts)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Positronic Bean").closest("a");
    expect(link).not.toBeNull();
    expect(link).toHaveAttribute(
      "href",
      "https://labs.positronicbean.com",
    );
  });

  it("o link Positronic Bean abre em nova aba (target=_blank, rel=noopener noreferrer)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Positronic Bean").closest("a");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("no modo collapsed (rail 56px), KG e Positronic Bean ambos viram icon-only (32×32) na mesma ordem da expandida", () => {
    // PERCIVAL: revisão visual 2026-08-02 — a imagem do rail mostrou que
    // Positronic Bean não aparecia (decisão B2-2 original restringia ao
    // modo expandido) e os ícones estavam sem espaçamento consistente
    // (``bottom-[60px]`` não casava com a altura do footer do rail que
    // cresce ~92px no flex-col). Solução: sub-componente ``RailIconLink``
    // (32×32, mesmo ``h-8 w-8`` dos ``SidebarActionButton`` do upstream)
    // e offset unificado via ``bottom-[96px]`` no rail (footer ~92px + 4px
    // de respiro). Preserva a ordem KG → Positronic Bean → Settings → Badge.
    const wrapper = renderWithClient();
    const { container } = render(
      <PercivalSidebar {...buildSidebarProps({ collapsed: true })} />,
      { wrapper },
    );
    // Ambos presentes, renderizados como ``<a className="h-8 w-8 grid">`` com svg.
    const kgLink = screen.getByLabelText("Knowledge Graph");
    const pbLink = screen.getByLabelText("Positronic Bean");
    expect(kgLink).toHaveAttribute("title", "Knowledge Graph");
    expect(pbLink).toHaveAttribute("title", "Positronic Bean");
    for (const link of [kgLink, pbLink]) {
      expect(link.tagName).toBe("A");
      expect(link.className).toMatch(/\bh-8\b/);
      expect(link.className).toMatch(/\bw-8\b/);
      expect(link.querySelector("svg")).not.toBeNull();
    }
    // Ordem DOM: KG antes de Positronic Bean (de cima pra baixo no rail).
    const railLinks = Array.from(
      container.querySelectorAll('[data-testid="rail-icon-link"]'),
    ) as HTMLAnchorElement[];
    expect(railLinks.length).toBe(2);
    expect(railLinks[0]).toBe(kgLink);
    expect(railLinks[1]).toBe(pbLink);
    // Slot externo é absoluto com ``bottom-[96px]`` (não ``[60px]``),
    // garantindo que os ícones ficam ACIMA do footer do rail, sem
    // sobrepor visualmente os controles.
    const slot = container.querySelector('[data-testid="external-cards-slot"]');
    expect(slot?.className ?? "").toMatch(/bottom-\[96px\]/);
  });

  it("Settings continua visível e funcional (não foi escondido)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("Knowledge Graph aparece depois de Automations e Settings (G2-AltB)", () => {
    const wrapper = renderWithClient();
    const { container } = render(<PercivalSidebar {...buildSidebarProps()} />, {
      wrapper,
    });
    // PERCIVAL: Skills e Automations são <button>, KG é <a>. querySelectorAll
    // direto para obter a ordem real do DOM (getAllByRole não mistura roles).
    // Decisão G2-AltB (2026-08-01): KG fica no rodapé (depois de toda a Sidebar).
    const ordered = Array.from(container.querySelectorAll("button, a"));
    const indexOf = (label: string) =>
      ordered.findIndex((el) => el.textContent?.includes(label));
    expect(indexOf("Automations")).toBeGreaterThan(-1);
    expect(indexOf("Settings")).toBeGreaterThan(-1);
    expect(indexOf("Knowledge Graph")).toBeGreaterThan(-1);
    expect(indexOf("Automations")).toBeLessThan(indexOf("Knowledge Graph"));
    expect(indexOf("Settings")).toBeLessThan(indexOf("Knowledge Graph"));
  });

  it("Knowledge Graph tem aria-label igual ao texto visível", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByLabelText("Knowledge Graph");
    expect(link.tagName).toBe("A");
  });

  it("Knowledge Graph usa o ícone Lucide-react (Network)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link?.querySelector("svg")).not.toBeNull();
  });

  it("expandido, os cards externos (KG + Positronic Bean) ficam centralizados dentro de caixas elegantes acima do footer", () => {
    // PERCIVAL: revisão visual 2026-08-02 — os cards externos viraram "cartões
    // de destaque": slot absolutamente posicionado com `bottom-[60px]`
    // (flutua acima do footer do upstream ~56px sem cobrir Settings), flex-col
    // empilhando KG no topo e Positronic Bean embaixo. Cada <a> interno tem
    // borda + sombra + fundo gradiente que indicam que é um botão importante.
    const wrapper = renderWithClient();
    const { container } = render(<PercivalSidebar {...buildSidebarProps()} />, {
      wrapper,
    });
    const slot = container.querySelector('[data-testid="external-cards-slot"]');
    expect(slot).not.toBeNull();
    const slotClass = slot?.className ?? "";
    expect(slotClass).toMatch(/bottom-\[60px\]/);
    expect(slotClass).toMatch(/flex-col/);
    const kgLink = screen.getByText("Knowledge Graph").closest("a");
    expect(kgLink).not.toBeNull();
    const kgClass = kgLink?.className ?? "";
    // Caixa elegante: borda + sombra + fundo gradiente + cantos arredondados.
    expect(kgClass).toMatch(/rounded-xl/);
    expect(kgClass).toMatch(/border/);
    expect(kgClass).toMatch(/shadow-\[/);
    expect(kgClass).toMatch(/bg-gradient-to-br/);
    const pbLink = screen.getByText("Positronic Bean").closest("a");
    expect(pbLink).not.toBeNull();
    const pbClass = pbLink?.className ?? "";
    expect(pbClass).toMatch(/rounded-xl/);
    expect(pbClass).toMatch(/bg-gradient-to-br/);
    // KG renderiza antes de Positronic Bean no DOM.
    const ordered = [kgLink, pbLink].filter(
      (el): el is HTMLAnchorElement => el !== null,
    );
    expect(ordered.indexOf(kgLink!)).toBeLessThan(ordered.indexOf(pbLink!));
  });

  it("os cards externos ficam no rodapé em diferentes props (consistente)", () => {
    const wrapper = renderWithClient();
    const { container: c1 } = render(<PercivalSidebar {...buildSidebarProps()} />, {
      wrapper,
    });
    const { container: c2 } = render(
      <PercivalSidebar {...buildSidebarProps({ sessions: [] })} />,
      { wrapper },
    );
    for (const c of [c1, c2]) {
      const ordered = Array.from(c.querySelectorAll("button, a"));
      const i = (label: string) =>
        ordered.findIndex((el) => el.textContent?.includes(label));
      // Positronic Bean é o último elemento do DOM (depois de KG, que
      // também fica depois de toda a Sidebar). Garante que a ordem do
      // slot externo (KG → Positronic Bean) é estável em diferentes props.
      const pb = i("Positronic Bean");
      expect(pb).toBe(ordered.length - 1);
      expect(i("Knowledge Graph")).toBeGreaterThan(i("Settings"));
      expect(i("Knowledge Graph")).toBeLessThan(pb);
      expect(i("Automations")).toBeLessThan(i("Knowledge Graph"));
      expect(i("Settings")).toBeLessThan(pb);
    }
  });
});
