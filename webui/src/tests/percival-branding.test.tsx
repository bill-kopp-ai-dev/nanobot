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
    vi.stubEnv("VITE_KG_INTERFACE_URL", "http://localhost:5173");
  });

  afterEach(() => {
    if (ORIGINAL_ENV === undefined) {
      vi.unstubAllEnvs();
    } else {
      vi.stubEnv("VITE_KG_INTERFACE_URL", ORIGINAL_ENV);
    }
  });

  it("o link KG é irmão direto do root do wrapper, não descendente da Sidebar (regressão de clipping)", () => {
    // PERCIVAL: jsdom não calcula layout real, então nenhum outro teste aqui pega
    // regressões de CSS. UpstreamSidebar tem `h-full` na raiz — se o link KG fosse
    // irmão de fragment (implementação anterior), ele renderizaria depois desse nav
    // 100%-de-altura e seria cortado pelos ancestrais `overflow-hidden` que envolvem
    // a Sidebar em todo o App.tsx (confirmado renderizando o CSS real compilado num
    // browser headless: 0 pixels visíveis). A correção envolve `<UpstreamSidebar>`
    // num wrapper `flex-1 min-h-0 overflow-hidden` para que ela ceda espaço ao link.
    // Este teste garante estruturalmente que o link é filho direto do root do
    // PercivalSidebar (fora da região que a Sidebar upstream controla), não um
    // descendente dela — Sidebar.tsx tem sua própria div interna com classes
    // "flex-1 overflow-hidden" (o wrapper do ChatList), então checar apenas a
    // presença dessas classes no container não diferencia os dois casos.
    const wrapper = renderWithClient();
    const { container } = render(<PercivalSidebar {...buildSidebarProps()} />, {
      wrapper,
    });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link?.parentElement).toBe(container.firstElementChild);
    expect(link?.parentElement?.className ?? "").not.toMatch(/overflow-hidden/);
  });

  it("no modo collapsed (rail), o label do KG fica recolhido e o link vira icon-only (regressão de overflow)", () => {
    // PERCIVAL: achado de revisão integrada — a implementação original ignorava
    // `props.collapsed`, então no rail de 56px (SIDEBAR_RAIL_WIDTH em App.tsx) o
    // texto "Knowledge Graph" vazava para fora da sidebar (confirmado renderizando
    // o CSS real compilado num browser headless). jsdom não calcula layout, então
    // este teste checa a mesma classe de recolhimento (`max-w-0`/`opacity-0`) que
    // SidebarActionButton já usa para os outros botões da Sidebar, em vez de medir
    // pixels — a ausência dela é exatamente o que causava o overflow.
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps({ collapsed: true })} />, {
      wrapper,
    });
    const link = screen.getByLabelText("Knowledge Graph");
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("title", "Knowledge Graph");
    const label = link.querySelector("span");
    expect(label?.className ?? "").toMatch(/max-w-0/);
  });

  it("expandido (collapsed=false), o label do KG fica visível e sem atributo title redundante", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps({ collapsed: false })} />, {
      wrapper,
    });
    const link = screen.getByLabelText("Knowledge Graph");
    expect(link).not.toHaveAttribute("title");
    const label = link.querySelector("span");
    expect(label?.className ?? "").not.toMatch(/max-w-0/);
  });

  it("renderiza o link Knowledge Graph com a URL resolvida", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link).not.toBeNull();
    expect(link).toHaveAttribute("href", "http://localhost:5173");
  });

  it("o link KG abre em nova aba (target=_blank, rel=noopener noreferrer)", () => {
    const wrapper = renderWithClient();
    render(<PercivalSidebar {...buildSidebarProps()} />, { wrapper });
    const link = screen.getByText("Knowledge Graph").closest("a");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
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

  it("Knowledge Graph fica no rodapé em diferentes props (consistente)", () => {
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
      // KG é sempre o último elemento da ordem do DOM (depois de toda a Sidebar).
      expect(i("Knowledge Graph")).toBe(ordered.length - 1);
      expect(i("Automations")).toBeLessThan(i("Knowledge Graph"));
      expect(i("Settings")).toBeLessThan(i("Knowledge Graph"));
    }
  });
});
