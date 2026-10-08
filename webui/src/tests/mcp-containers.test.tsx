import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { McpContainersPage } from "@/components/McpContainersPage";
import { ApiError, fetchMcpDockerOperatorBootstrap, fetchMcpDockerSnapshot } from "@/lib/api";
import type { McpDockerSnapshot } from "@/lib/api";
import type { NanobotClient } from "@/lib/nanobot-client";
import { ClientProvider } from "@/providers/ClientProvider";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    fetchMcpDockerOperatorBootstrap: vi.fn(),
    fetchMcpDockerSnapshot: vi.fn(),
  };
});

function clientStub() {
  return {
    onStatus: vi.fn(() => () => undefined),
    requestMutation: vi.fn().mockResolvedValue({ revision: 1 }),
  } as unknown as NanobotClient;
}

function snapshot() {
  return {
    schemaVersion: 1,
    revision: 4,
    allowRemoteAdmin: false,
    servers: {
      weather: {
        serverId: "weather",
        source: { type: "local-image", reference: `sha256:${"a".repeat(64)}` },
        revision: 2,
        active: true,
        state: "running",
        tools: ["forecast"],
        toolsDisabled: [],
        dockerObservation: "running",
        mcpConnectivity: "connected",
        configuration: {
          persistent: false,
          mounts: null,
          network: "none",
          env: {},
        },
      },
    },
    history: [],
    pendingTransitions: [],
    backups: [],
  };
}

describe("MCP container observability page", () => {
  it("shows separated Docker/MCP status and redacted host metadata before operator setup", async () => {
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce({
      schemaVersion: 1,
      revision: 2,
      allowRemoteAdmin: false,
      servers: {
        weather: {
          serverId: "weather",
          source: { type: "local-image", reference: "sha256:abc" },
          revision: 1,
          active: true,
          state: "running",
          tools: ["forecast"],
          toolsDisabled: [],
          dockerObservation: "running",
          mcpConnectivity: "connected",
          configuration: {
            persistent: false,
            mounts: null,
            network: "none",
            env: { API_TOKEN: { kind: "secret", value: "_REDACTED_MCP_ENV_SECRET", maskHint: "abcd••••wxyz" } },
          },
        },
      },
      history: [{
        at: "2026-10-07T12:00:00Z",
        action: "install",
        server_id: "weather",
        phase: "committed",
        revision: 2,
        correlation_id: "corr-1",
      }],
      pendingTransitions: [],
      backups: [],
    });
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "weather" })).toBeInTheDocument();
    expect(screen.getAllByText("running")).toHaveLength(3);
    expect(screen.getAllByText("connected")).toHaveLength(2);
    expect(screen.getByText("API_TOKEN (abcd••••wxyz)")).toBeInTheDocument();
    expect(screen.queryByText("_REDACTED_MCP_ENV_SECRET")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /install and activate|save configuration|restart|back up and exclude/i })).not.toBeInTheDocument();
    expect(screen.getByText(/install/)).toBeInTheDocument();
    expect(fetchMcpDockerSnapshot).toHaveBeenCalledWith("webui-token");
  });

  it("shows a clear empty state and a retryable gateway read error", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    const client = clientStub();
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce({
      schemaVersion: 1,
      revision: 0,
      allowRemoteAdmin: false,
      servers: {},
      history: [],
      pendingTransitions: [],
      backups: [],
    });
    const empty = render(
      <ClientProvider client={client} token="token">
        <McpContainersPage />
      </ClientProvider>,
    );
    expect(await screen.findByText("No Docker MCP servers")).toBeInTheDocument();
    empty.unmount();

    vi.mocked(fetchMcpDockerSnapshot).mockRejectedValueOnce(new Error("gateway offline"));
    render(
      <ClientProvider client={client} token="token">
        <McpContainersPage />
      </ClientProvider>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load Docker MCP status");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows a common broker failure without presenting saved tools as live", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce({
      ...snapshot(),
      brokerStatus: {
        status: "unavailable", reason: "token-permissions",
        message: "Broker token owner, group or mode does not match this gateway.",
      },
      servers: {
        weather: {
          ...snapshot().servers.weather,
          dockerObservation: "unknown", mcpConnectivity: "unknown",
        },
      },
    });
    render(<ClientProvider client={clientStub()} token="token"><McpContainersPage /></ClientProvider>);
    expect(await screen.findByText("MCP Docker broker unavailable")).toBeInTheDocument();
    expect(screen.getByText(/token owner, group or mode/i)).toBeInTheDocument();
    expect(screen.getByText(/saved tools below are not proof/i)).toBeInTheDocument();
    expect(screen.getAllByText("unknown")).toHaveLength(4);
  });

  it("distinguishes 401 unauthorized from generic read errors", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    const client = clientStub();
    vi.mocked(fetchMcpDockerSnapshot).mockRejectedValueOnce(new ApiError(401, "unauthorized"));
    render(
      <ClientProvider client={client} token="token">
        <McpContainersPage />
      </ClientProvider>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("not authorized");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("sends a per-tool mutation with both WebUI transport and operator authorization", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(snapshot());
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "admin-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Unlock management" }));
    fireEvent.click(await screen.findByRole("button", { name: "Disable" }));

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.disable_tool",
      expect.objectContaining({
        operator_admin: "admin-secret",
        server_id: "weather",
        expected_revision: 4,
        expected_server_revision: 2,
        tool: "forecast",
      }),
      expect.any(Number),
    ));
  });

  it("sets up the separate operator password without requiring a prior password", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue({
      schemaVersion: 1, revision: 0, allowRemoteAdmin: false, servers: {}, history: [], pendingTransitions: [], backups: [],
    });
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Set operator password"), { target: { value: "first-admin-pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Configure password" }));

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.operator_setup",
      { operator_admin: "first-admin-pass" },
      expect.any(Number),
    ));
    expect(await screen.findByText("Operator password configured.")).toBeInTheDocument();
  });

  it("round-trips a redacted secret sentinel without displaying or replacing the value", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const value = structuredClone(snapshot());
    value.servers.weather.configuration.network = "bridge";
    value.servers.weather.configuration.env = {
      API_TOKEN: { kind: "secret", value: "_REDACTED_MCP_ENV_SECRET", maskHint: "abcd••••wxyz" },
    };
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "admin-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Unlock management" }));
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.configure",
      expect.objectContaining({
        operator_admin: "admin-secret",
        configuration: expect.objectContaining({
          network: "bridge",
          env: { API_TOKEN: { kind: "secret", value: "_REDACTED_MCP_ENV_SECRET" } },
        }),
      }),
      expect.any(Number),
    ));
    expect(screen.queryByText("same-super-secret-value")).not.toBeInTheDocument();
    expect(screen.getByText("API_TOKEN (abcd••••wxyz)")).toBeInTheDocument();
  });

  it("requires typing the server ID before widening the host mount scope", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const value = structuredClone(snapshot());
    value.servers.weather.configuration.mounts = ["/srv/data"];
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "admin-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Unlock management" }));
    const restrictedMountToggles = screen.getAllByRole("checkbox", { name: /Use reduced host paths/i });
    fireEvent.click(restrictedMountToggles[1]);
    const save = screen.getByRole("button", { name: "Save configuration" });
    expect(save).toBeDisabled();
    const scopeConfirmations = screen.getAllByLabelText(/Type the server ID to confirm/i);
    fireEvent.change(scopeConfirmations[1], { target: { value: "weather" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    fireEvent.click(save);

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.configure",
      expect.objectContaining({
        server_id: "weather",
        configuration: expect.objectContaining({ mounts: null }),
      }),
      expect.any(Number),
    ));
  });

  it("rotates the operator password through the authenticated mutation channel", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(snapshot());
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "old-admin-pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Unlock management" }));
    fireEvent.change(screen.getByLabelText("New operator password"), { target: { value: "new-admin-pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Rotate password" }));

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.operator_rotate",
      { new_password: "new-admin-pass", operator_admin: "old-admin-pass" },
      expect.any(Number),
    ));
    expect(await screen.findByText("Operator password rotated.")).toBeInTheDocument();
  });

  it("requires server ID confirmation before restoring a backup", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const value = structuredClone(snapshot()) as McpDockerSnapshot;
    value.backups = [{ backupId: "2026-10-07T18-00-00-weather-deadbeef", serverId: "weather-old", sourceRevision: 5, action: "exclude" }];
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    const client = clientStub();
    render(
      <ClientProvider client={client} token="webui-token">
        <McpContainersPage />
      </ClientProvider>,
    );

    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "admin-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Unlock management" }));
    expect(screen.getByText(/before exclude/)).toBeInTheDocument();
    const restore = screen.getByRole("button", { name: "Restore" });
    expect(restore).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Type the server ID to restore"), { target: { value: "weather-old" } });
    vi.mocked(client.requestMutation).mockResolvedValueOnce({
      server: "weather-old",
      mcp_runtime: { ok: false, requires_restart: true },
    });
    fireEvent.click(restore);

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.restore",
      {
        backup_id: "2026-10-07T18-00-00-weather-deadbeef",
        expected_revision: 4,
        expected_confirmation: "weather-old",
        operator_admin: "admin-secret",
      },
      expect.any(Number),
    ));
    expect(await screen.findByText(/Server restored from backup and reconciled\. Saved\. Restart to apply changes\./i)).toBeInTheDocument();
  });
});
