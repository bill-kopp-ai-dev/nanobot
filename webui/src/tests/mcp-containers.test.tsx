import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  it("treats stopped intent and saved tools as unavailable rather than live", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    const value: McpDockerSnapshot = structuredClone(snapshot());
    value.servers.weather.dockerObservation = "stopped";
    value.servers.weather.mcpConnectivity = "disconnected";
    value.servers.weather.state = "stopped-persistent";
    value.servers.weather.configuration.persistent = true;
    value.servers.weather.tools = [];
    value.servers.weather.savedTools = ["forecast"];
    value.servers.weather.toolsSource = "observed";
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    render(<ClientProvider client={clientStub()} token="token"><McpContainersPage /></ClientProvider>);
    expect((await screen.findAllByText("Stopped as configured")).length).toBeGreaterThan(0);
    expect(screen.getByText(/Tools \(1\) — saved \/ not verifiable now/)).toBeInTheDocument();
  });

  it("installs a new local image with minimum mounts and bridge, then selects it after a verified read", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const first: McpDockerSnapshot = { ...snapshot(), servers: {}, minimumMountsSupported: true, supportedNetworks: ["none", "bridge"] };
    const installed: McpDockerSnapshot = { ...first, revision: 5, servers: { weather: snapshot().servers.weather } };
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce(first).mockResolvedValue(installed);
    const client = clientStub();
    vi.mocked(client.requestMutation).mockResolvedValueOnce({ revision: 5, server: "weather" });
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.click(await screen.findByRole("button", { name: "Add MCP server" }));
    expect(screen.getByText(/Provide the operator password above/)).toBeInTheDocument();
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.change(screen.getByLabelText("Server ID"), { target: { value: "weather" } });
    fireEvent.change(screen.getByLabelText("Full image ID or RepoDigest"), { target: { value: snapshot().servers.weather.source.reference } });
    fireEvent.click(screen.getByRole("radio", { name: /Minimum access/i }));
    fireEvent.change(screen.getByLabelText("Network access"), { target: { value: "bridge" } });
    fireEvent.change(screen.getByLabelText("Type the server ID to confirm this installation"), { target: { value: "weather" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the installation scope/i }));
    fireEvent.click(screen.getByRole("button", { name: "Install and activate" }));
    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith("settings.mcp_docker.install", expect.objectContaining({
      operator_admin: "pass", expected_revision: 4, server_id: "weather",
      configuration: { persistent: false, mounts: [], network: "bridge", env: {} },
    }), expect.any(Number)));
    expect(await screen.findByRole("heading", { name: "weather" })).toBeInTheDocument();
  });

  it("blocks unchanged image updates and keeps the modal confirmation contextual", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(snapshot());
    const client = clientStub();
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getByRole("button", { name: "Update image" }));
    const dialog = screen.getByRole("dialog", { name: "Update image for weather" });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the image identity/i }));
    fireEvent.change(screen.getByLabelText(/Type weather to confirm this image update/i), { target: { value: "weather" } });
    expect(within(dialog).getByRole("button", { name: "Update image" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(client.requestMutation).not.toHaveBeenCalled();
  });

  it("does not offer unsupported mount and network modes on an older host", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(snapshot());
    render(<ClientProvider client={clientStub()} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getByRole("button", { name: "Add MCP server" }));
    expect(screen.getAllByRole("radio", { name: /Minimum access/i }).every((radio) => (radio as HTMLInputElement).disabled)).toBe(true);
    expect(screen.getAllByLabelText("Network access").every((select) => !Array.from((select as HTMLSelectElement).options).some((option) => option.value === "bridge"))).toBe(true);
  });

  it("requires an ID confirmation for none to bridge without changing mounts or env", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const value: McpDockerSnapshot = { ...snapshot(), supportedNetworks: ["none", "bridge"] };
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    const client = clientStub();
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.change(screen.getByLabelText("Network access"), { target: { value: "bridge" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    expect(screen.getByRole("button", { name: "Save configuration" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Type weather to confirm increased host or network access/), { target: { value: "weather" } });
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));
    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith("settings.mcp_docker.configure", expect.objectContaining({
      configuration: { persistent: false, mounts: null, network: "bridge", env: {} },
      expected_server_revision: 2, operator_admin: "pass",
    }), expect.any(Number)));
  });

  it("keeps a configuration draft but invalidates its confirmation when a poll finds a new revision", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const before: McpDockerSnapshot = snapshot();
    const after: McpDockerSnapshot = structuredClone(before);
    after.revision = 5;
    after.servers.weather.revision = 3;
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce(before).mockResolvedValue(after);
    const client = clientStub();
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.change(screen.getByLabelText("Variable name 1"), { target: { value: "API_KEY" } });
    fireEvent.change(screen.getByLabelText("Variable value 1"), { target: { value: "draft" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText(/Server revision changed while editing/)).toBeInTheDocument();
    expect(screen.getByLabelText("Variable value 1")).toHaveValue("draft");
    expect(screen.getByRole("button", { name: "Save configuration" })).toBeDisabled();
    expect(client.requestMutation).not.toHaveBeenCalled();
  });

  it("reports intent mismatch when docker is stopped but state is starting or restarting", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: false });
    const value: McpDockerSnapshot = structuredClone(snapshot());
    value.servers.weather.dockerObservation = "stopped";
    value.servers.weather.mcpConnectivity = "disconnected";
    value.servers.weather.state = "starting";
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    render(<ClientProvider client={clientStub()} token="token"><McpContainersPage /></ClientProvider>);
    expect((await screen.findAllByText("Not running (intent mismatch)")).length).toBeGreaterThan(0);
  });

  it("allows widening a minimum server even when the host does not advertise minimum support", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const value: McpDockerSnapshot = structuredClone(snapshot());
    value.servers.weather.configuration.mounts = [];
    value.servers.weather.revision = 2;
    value.minimumMountsSupported = false;
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValue(value);
    const client = clientStub();
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    const fullRadio = screen.getByRole("radio", { name: /Full access/i });
    fireEvent.click(fullRadio);
    const scopeInput = await screen.findByLabelText(/Type weather to confirm increased host or network access/);
    fireEvent.change(scopeInput, { target: { value: "weather" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    expect(screen.getByRole("button", { name: "Save configuration" })).toBeEnabled();
  });

  it("clears hasDraft once a poll replaces the snapshot", async () => {
    vi.mocked(fetchMcpDockerOperatorBootstrap).mockResolvedValue({ configured: true });
    const before: McpDockerSnapshot = snapshot();
    const after: McpDockerSnapshot = structuredClone(before);
    after.revision = 5;
    after.servers.weather.revision = 3;
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce(before).mockResolvedValue(after);
    const client = clientStub();
    render(<ClientProvider client={client} token="token"><McpContainersPage /></ClientProvider>);
    fireEvent.change(await screen.findByLabelText("Operator password"), { target: { value: "pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.change(screen.getByLabelText("Variable name 1"), { target: { value: "API_KEY" } });
    fireEvent.change(screen.getByLabelText("Variable value 1"), { target: { value: "draft" } });
    const confirmSpy = vi.spyOn(window, "confirm");
    confirmSpy.mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText(/Server revision changed while editing/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Discard draft and load latest" }));
    const beforeServerButtons = screen.getAllByRole("button", { name: /weather/ });
    const serverItem = beforeServerButtons.find((btn) => btn.getAttribute("type") === "button");
    expect(serverItem).toBeDefined();
    confirmSpy.mockRestore();
  });

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
    expect(screen.getAllByText("MCP connected").length).toBeGreaterThan(0);
    expect(screen.queryByText(/abcd••••wxyz/)).not.toBeInTheDocument();
    expect(screen.queryByText("_REDACTED_MCP_ENV_SECRET")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /install and activate|save configuration|restart|back up and exclude/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add MCP server" })).toBeInTheDocument();
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
    expect(screen.getAllByText("unknown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not verified").length).toBeGreaterThan(0);
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
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getByText(/Per-tool access \(1 enabled/));
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
    expect(await screen.findByText(/Operation accepted, but the current state could not be verified/)).toBeInTheDocument();
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
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Add variable" })[0]);
    fireEvent.change(screen.getByLabelText("Variable name 2"), { target: { value: "COUNT" } });
    fireEvent.change(screen.getByLabelText("Variable value 2"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /reviewed the configuration diff/i }));
    expect(screen.getByRole("button", { name: "Save configuration" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));

    await waitFor(() => expect(client.requestMutation).toHaveBeenCalledWith(
      "settings.mcp_docker.configure",
      expect.objectContaining({
        operator_admin: "admin-secret",
        configuration: expect.objectContaining({
          network: "bridge",
          env: { API_TOKEN: { kind: "secret", value: "_REDACTED_MCP_ENV_SECRET" }, COUNT: { kind: "plain", value: "1" } },
        }),
      }),
      expect.any(Number),
    ));
    expect(screen.queryByText("same-super-secret-value")).not.toBeInTheDocument();
    expect(screen.queryByText(/abcd••••wxyz/)).not.toBeInTheDocument();
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
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getByRole("radio", { name: /Full access/i }));
    const save = screen.getByRole("button", { name: "Save configuration" });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Type weather to confirm increased host or network access/i), { target: { value: "weather" } });
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
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Provide password" }));
    fireEvent.click(screen.getByText(/Restore an excluded server \(1 eligible\)/));
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
    expect(await screen.findByText(/Operation accepted, but the current state could not be verified/)).toBeInTheDocument();
  });
});
