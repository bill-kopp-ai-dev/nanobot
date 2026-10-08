import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { McpContainersPage } from "@/components/McpContainersPage";
import { ApiError, fetchMcpDockerSnapshot } from "@/lib/api";
import type { NanobotClient } from "@/lib/nanobot-client";
import { ClientProvider } from "@/providers/ClientProvider";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, fetchMcpDockerSnapshot: vi.fn() };
});

describe("MCP container observability page", () => {
  it("shows separated Docker/MCP status and redacted host metadata without management controls", async () => {
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
    });
    const client = {} as NanobotClient;
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
    expect(screen.queryByRole("button", { name: /install|configure|restart|exclude/i })).not.toBeInTheDocument();
    expect(screen.getByText(/install/)).toBeInTheDocument();
    expect(fetchMcpDockerSnapshot).toHaveBeenCalledWith("webui-token");
  });

  it("shows a clear empty state and a retryable gateway read error", async () => {
    const client = {} as NanobotClient;
    vi.mocked(fetchMcpDockerSnapshot).mockResolvedValueOnce({
      schemaVersion: 1,
      revision: 0,
      allowRemoteAdmin: false,
      servers: {},
      history: [],
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

  it("distinguishes 401 unauthorized from generic read errors", async () => {
    const client = {} as NanobotClient;
    vi.mocked(fetchMcpDockerSnapshot).mockRejectedValueOnce(new ApiError(401, "unauthorized"));
    render(
      <ClientProvider client={client} token="token">
        <McpContainersPage />
      </ClientProvider>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("not authorized");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
