// PERCIVAL: helpers reutilizáveis para testes da UI do percival (P8 etapa 5).
// Decisão D2: base reutilizável. Builder de props (buildSidebarProps) +
// renderWithClient wrapper que provê o ClientProvider exigido pela
// ConnectionBadge (que o upstream renderiza dentro da Sidebar).
import type { ComponentProps, ReactNode } from "react";
import { vi } from "vitest";
import { Sidebar } from "@/components/Sidebar";
import { ClientProvider } from "@/providers/ClientProvider";
import type { NanobotClient } from "@/lib/nanobot-client";
import type { ConnectionStatus } from "@/lib/types";

type SidebarComponentProps = ComponentProps<typeof Sidebar>;

/**
 * Constrói props mínimas válidas para renderizar <Sidebar> ou <PercivalSidebar>.
 * Todos os callbacks são vi.fn() para permitir asserções em testes futuros.
 */
export function buildSidebarProps(
  overrides: Partial<SidebarComponentProps> = {},
): SidebarComponentProps {
  const base: SidebarComponentProps = {
    sessions: [],
    activeKey: null,
    loading: false,
    onNewChat: vi.fn(),
    onSelect: vi.fn(),
    onRequestDelete: vi.fn(),
    onTogglePin: vi.fn(),
    onRequestRename: vi.fn(),
    onToggleArchive: vi.fn(),
    onToggleGroup: vi.fn(),
    onRequestRenameProject: vi.fn(),
    onNewChatInProject: vi.fn(),
    onOpenSettings: vi.fn(),
    onOpenApps: vi.fn(),
    onOpenSkills: vi.fn(),
    onOpenAutomations: vi.fn(),
    onOpenSearch: vi.fn(),
    onToggleArchived: vi.fn(),
    onCollapse: vi.fn(),
    ...overrides,
  };
  return base;
}

/**
 * Cria um NanobotClient mínimo-mock para satisfazer o ClientProvider usado
 * pela ConnectionBadge dentro da Sidebar. Apenas os campos consumidos pelos
 * componentes da Sidebar estão implementados.
 */
function buildFakeClient(): NanobotClient {
  const noop = () => {};
  return {
    status: "open" as ConnectionStatus,
    onStatus: (_handler: (s: ConnectionStatus) => void) => noop,
  } as unknown as NanobotClient;
}

/**
 * Wrapper de render que provê ClientProvider (exigido pela ConnectionBadge
 * dentro da Sidebar upstream). Uso com `render(<X />, { wrapper: renderWithClient() })`
 * da testing-library.
 */
export function renderWithClient() {
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <ClientProvider client={buildFakeClient()} token="test">
      {children}
    </ClientProvider>
  );
  return Wrapper;
}
