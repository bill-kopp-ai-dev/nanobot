import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Box, CircleAlert, Clock3, Plus, RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useClient } from "@/providers/ClientProvider";
import { ApiError, fetchMcpDockerSnapshot, type McpDockerSnapshot } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { McpDockerManagement } from "@/components/McpDockerManagement";

const POLL_INTERVAL_MS = 30_000;

function statusTone(value: string): string {
  if (["running", "connected"].includes(value)) return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
  if (["unknown", "image-missing", "container-missing"].includes(value)) return "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-300";
  return "border-border bg-muted/50 text-muted-foreground";
}

function Status({ label, value, reliable = true }: { label: string; value: string; reliable?: boolean }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("w-fit max-w-full rounded-full border px-2.5 py-1 text-xs font-medium", statusTone(reliable ? value : "unknown"))}>
        {value}
      </span>
    </div>
  );
}

type Server = McpDockerSnapshot["servers"][string];

function operationalStatus(server: Server, stale: boolean, brokerUnavailable: boolean): string {
  if (stale) return "Data outdated; refresh failed";
  if (brokerUnavailable || server.dockerObservation === "unknown" || server.observationError) return "Not verified";
  if (server.dockerObservation === "image-missing") return "Image missing";
  if (server.dockerObservation === "stopped" && server.state === "stopped-persistent" && server.active && server.configuration.persistent) return "Stopped as configured";
  const intentStates = ["running", "starting", "restarting", "updating"];
  if (["stopped", "container-missing"].includes(server.dockerObservation) && intentStates.includes(server.state)) return "Not running (intent mismatch)";
  if (server.dockerObservation === "running" && server.mcpConnectivity === "disconnected") return "Container running; MCP disconnected";
  if (server.dockerObservation === "running" && server.mcpConnectivity === "connected" && server.active && server.state === "running") return "MCP connected";
  return "Unclassified / divergent state";
}

export function McpContainersPage() {
  const { t } = useTranslation();
  const { getToken } = useClient();
  const [snapshot, setSnapshot] = useState<McpDockerSnapshot | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [installOpen, setInstallOpen] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const mountedRef = useRef(true);
  const refreshRequestRef = useRef(0);
  const lastRevisionRef = useRef<number | null>(null);
  useEffect(() => {
    if (snapshot && lastRevisionRef.current !== null && lastRevisionRef.current !== snapshot.revision) {
      setHasDraft(false);
    }
    lastRevisionRef.current = snapshot?.revision ?? null;
  }, [snapshot?.revision]);

  const refresh = useCallback(async (quiet = false): Promise<McpDockerSnapshot | null> => {
    if (!mountedRef.current) return null;
    const request = ++refreshRequestRef.current;
    if (quiet) setRefreshing(true);
    else setLoading(true);
    try {
      const result = await fetchMcpDockerSnapshot(getToken());
      if (!mountedRef.current || request !== refreshRequestRef.current) return null;
      setSnapshot(result);
      setSelectedId((current) => current && result.servers[current] ? current : Object.keys(result.servers)[0] ?? null);
      setError(null);
      return result;
    } catch (caught) {
      if (!mountedRef.current || request !== refreshRequestRef.current) return null;
      if (caught instanceof ApiError && caught.status === 401) {
        setError(t("mcpDocker.unauthorized", { defaultValue: "You are not authorized to view Docker MCP status." }));
      } else {
        setError(t("mcpDocker.loadError", { defaultValue: "Could not load Docker MCP status. Try again." }));
      }
      return null;
    } finally {
      if (mountedRef.current && request === refreshRequestRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [getToken, t]);

  useEffect(() => {
    mountedRef.current = true;
    void refresh();
    const timer = window.setInterval(() => void refresh(true), POLL_INTERVAL_MS);
    return () => {
      mountedRef.current = false;
      refreshRequestRef.current += 1;
      window.clearInterval(timer);
    };
  }, [refresh]);

  const entries = Object.entries(snapshot?.servers ?? {});
  const selected = selectedId ? snapshot?.servers[selectedId] : undefined;
  const selectedHistory = useMemo(
    () => (snapshot?.history ?? []).filter((event) => event.server_id === selectedId),
    [snapshot?.history, selectedId],
  );

  return (
    <main className="flex h-full min-h-0 flex-col overflow-y-auto">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-7 sm:px-8 lg:px-12">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Box aria-hidden="true" className="mt-1 h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                {t("mcpDocker.title", { defaultValue: "MCP containers" })}
              </h1>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                {t("mcpDocker.description", { defaultValue: "Read-only status for Docker-managed MCP servers." })}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2"><Button onClick={() => setInstallOpen(true)}><Plus aria-hidden="true" className="mr-2 h-4 w-4" />Add MCP server</Button><Button variant="outline" onClick={() => void refresh(true)} disabled={refreshing}>
            <RefreshCw aria-hidden="true" className={cn("mr-2 h-4 w-4", refreshing && "animate-spin motion-reduce:animate-none")} />
            {t("mcpDocker.refresh", { defaultValue: "Refresh" })}
          </Button></div>
        </header>

        {error && (
          <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm">
            <span className="flex items-center gap-2"><CircleAlert aria-hidden="true" className="h-4 w-4" />{error}</span>
            <Button variant="outline" size="sm" onClick={() => void refresh()}>{t("mcpDocker.retry", { defaultValue: "Retry" })}</Button>
          </div>
        )}

        {snapshot?.brokerStatus?.status === "unavailable" && !error && (
          <div role="status" className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-800 dark:text-amber-300">
            <CircleAlert aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
            <div><strong>{t("mcpDocker.brokerUnavailableTitle", { defaultValue: "MCP Docker broker unavailable" })}</strong><p className="mt-1">{snapshot.brokerStatus.message}</p><p className="mt-1">{t("mcpDocker.savedIntentOnly", { defaultValue: "Server intent and saved tools below are not proof that containers are running. Check the gateway–broker deployment before reconciling servers." })}</p></div>
          </div>
        )}

        {loading && !snapshot ? (
          <div role="status" aria-busy="true" className="space-y-3">
            <span className="sr-only">{t("settings.status.loading", { defaultValue: "Loading" })}</span>
            <div className="h-20 animate-pulse rounded-lg bg-muted/60 motion-reduce:animate-none" />
            <div className="h-36 animate-pulse rounded-lg bg-muted/40 motion-reduce:animate-none" />
          </div>
        ) : snapshot && entries.length === 0 ? (
          <div className="space-y-6"><section className="rounded-xl border border-dashed p-8 text-center">
            <Box aria-hidden="true" className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
            <h2 className="font-medium">{t("mcpDocker.emptyTitle", { defaultValue: "No Docker MCP servers" })}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("mcpDocker.emptyDescription", { defaultValue: "Installed Docker MCP servers will appear here." })}
            </p>
          </section><McpDockerManagement snapshot={snapshot} selectedId={null} selected={undefined} refresh={refresh} installOpen={installOpen} setInstallOpen={setInstallOpen} onInstalled={setSelectedId} /></div>
        ) : snapshot ? (
          <div className="space-y-6">
          {entries.length > 0 && <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(15rem,0.8fr)_minmax(0,1.5fr)]">
            <section aria-labelledby="mcp-server-list-title" className="min-w-0 rounded-xl border">
              <h2 id="mcp-server-list-title" className="border-b px-4 py-3 text-sm font-semibold">
                {t("mcpDocker.servers", { defaultValue: "Servers" })} <span className="text-muted-foreground">({entries.length})</span>
              </h2>
              <ul className="divide-y">
                {entries.map(([id, server]) => (
                  <li key={id}>
                    <button
                      type="button"
                      aria-current={selectedId === id ? "true" : undefined}
                       onClick={() => { if (id !== selectedId && (!hasDraft || window.confirm("Discard the unsaved server configuration draft?"))) setSelectedId(id); }}
                      className={cn("w-full px-4 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring", selectedId === id && "bg-muted/60")}
                    >
                      <span className="block truncate font-medium">{id}</span>
                       <span className="mt-1 block truncate text-xs text-muted-foreground" title={server.source.reference}>{server.source.reference}</span>
                       <span className="mt-1 block text-xs">{operationalStatus(server, Boolean(error), snapshot.brokerStatus?.status === "unavailable")}</span>
                      <span className="mt-2 flex flex-wrap gap-1.5">
                         <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", statusTone(error ? "unknown" : server.dockerObservation))}>{server.dockerObservation}</span>
                         <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", statusTone(error ? "unknown" : server.mcpConnectivity))}>{server.mcpConnectivity}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            {selected && selectedId && (
              <section aria-labelledby="mcp-server-detail-title" className="min-w-0 space-y-5">
                <div className="rounded-xl border p-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h2 id="mcp-server-detail-title" className="text-lg font-semibold">{selectedId}</h2>
                      <p className="mt-1 truncate font-mono text-xs text-muted-foreground" title={selected.source.reference}>{selected.source.type}: {selected.source.reference}</p>
                      <Button variant="ghost" size="sm" onClick={() => void navigator.clipboard.writeText(selected.source.reference)} aria-label="Copy full image identity">Copy image identity</Button>
                    </div>
                    <span className={cn("rounded-full border px-2.5 py-1 text-xs", operationalStatus(selected, Boolean(error), snapshot.brokerStatus?.status === "unavailable") === "MCP connected" ? statusTone("connected") : statusTone("unknown"))}>{operationalStatus(selected, Boolean(error), snapshot.brokerStatus?.status === "unavailable")}</span>
                  </div>
                  <div className="mt-5 grid gap-4 sm:grid-cols-2">
                    <Status label={t("mcpDocker.dockerState", { defaultValue: "Docker state" })} value={selected.dockerObservation} reliable={!error && !selected.observationError && snapshot.brokerStatus?.status !== "unavailable"} />
                    <Status label={t("mcpDocker.mcpState", { defaultValue: "MCP connectivity" })} value={selected.mcpConnectivity} reliable={!error && !selected.observationError && snapshot.brokerStatus?.status !== "unavailable"} />
                    <Status label={t("mcpDocker.intentState", { defaultValue: "Gateway intent" })} value={selected.state} />
                    <Status label="Enabled in gateway" value={selected.active ? "yes" : "no"} />
                  </div>
                  {selected.observationError && <p role="status" className="mt-4 text-sm text-amber-700 dark:text-amber-300">{selected.observationError}</p>}
                  <p className="mt-4 text-xs text-muted-foreground">Configured: {selected.configuration.network} network · {selected.configuration.mounts === null || selected.configuration.mounts === undefined ? "Full host access" : selected.configuration.mounts.length ? `Customized (${selected.configuration.mounts.length} paths)` : "Minimum host access"} · {Object.keys(selected.configuration.env).length} environment variables</p>
                  <details className="mt-5 border-t pt-4"><summary className="cursor-pointer text-sm font-semibold">Configuration and observed Docker details</summary>
                    <h3 className="text-sm font-semibold">{t("mcpDocker.hostMetadata", { defaultValue: "Host configuration metadata" })}</h3>
                    <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                      <div><dt className="text-xs text-muted-foreground">{t("mcpDocker.network", { defaultValue: "Network" })}</dt><dd>{selected.configuration.network}</dd></div>
                      <div><dt className="text-xs text-muted-foreground">{t("mcpDocker.persistence", { defaultValue: "Persistent container" })}</dt><dd>{selected.configuration.persistent ? t("common.yes", { defaultValue: "Yes" }) : t("common.no", { defaultValue: "No" })}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs text-muted-foreground">{t("mcpDocker.mounts", { defaultValue: "Mount reductions" })}</dt><dd className="break-words">{selected.configuration.mounts === null || selected.configuration.mounts === undefined ? "Full access with mandatory covers" : selected.configuration.mounts.length ? selected.configuration.mounts.join(", ") : "Minimum access — no host binds"}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs text-muted-foreground">{t("mcpDocker.environment", { defaultValue: "Environment metadata" })}</dt><dd>{Object.entries(selected.configuration.env).length === 0 ? "None" : Object.entries(selected.configuration.env).map(([name, entry]) => `${name} (${entry.kind})`).join(", ")}</dd></div>
                    </dl>
                    <div className="mt-4 border-t pt-3">
                      <h4 className="text-xs font-semibold">{t("mcpDocker.effectiveConfiguration", { defaultValue: "Observed effective Docker configuration" })}</h4>
                      {selected.effectiveConfiguration ? <dl className="mt-2 grid gap-2 text-xs sm:grid-cols-2"><div><dt className="text-muted-foreground">{t("mcpDocker.network", { defaultValue: "Network" })}</dt><dd>{selected.effectiveConfiguration.network}</dd></div><div className="sm:col-span-2"><dt className="text-muted-foreground">{t("mcpDocker.effectiveMounts", { defaultValue: "Actual mounts (target, type, access)" })}</dt><dd className="break-words">{selected.effectiveConfiguration.mounts.length ? selected.effectiveConfiguration.mounts.map((mount) => `${mount.destination} (${mount.type}, ${mount.readWrite ? "R/W" : "RO"})`).join(", ") : t("mcpDocker.none", { defaultValue: "None" })}</dd></div></dl> : <p className="mt-2 text-xs text-muted-foreground">{t("mcpDocker.effectiveUnknown", { defaultValue: "Effective Docker settings are unavailable until the broker can inspect the container." })}</p>}
                    </div>
                  </details>
                  <details className="mt-5 border-t pt-4"><summary className="cursor-pointer text-sm font-semibold">Tools ({selected.mcpConnectivity === "connected" && !error ? selected.tools.length : (selected.savedTools ?? selected.tools).length}) — {selected.mcpConnectivity === "connected" && selected.toolsSource === "observed" && !error ? "observed" : "saved / not verifiable now"}</summary>
                    {(selected.mcpConnectivity === "connected" && !error ? selected.tools : selected.savedTools ?? selected.tools).length ? <ul className="mt-2 flex flex-wrap gap-2">{(selected.mcpConnectivity === "connected" && !error ? selected.tools : selected.savedTools ?? selected.tools).map((tool) => <li key={tool} className={cn("rounded-md border px-2 py-1 font-mono text-xs", selected.toolsDisabled.includes(tool) && "text-muted-foreground line-through")}>{tool}</li>)}</ul> : <p className="mt-2 text-sm text-muted-foreground">No saved tools available to display.</p>}
                  </details>
                </div>

                <details className="rounded-xl border"><summary className="cursor-pointer px-4 py-3 text-sm font-semibold"><Clock3 aria-hidden="true" className="mr-2 inline h-4 w-4" />Recent activity</summary><section aria-labelledby="mcp-history-title">
                  <h2 id="mcp-history-title" className="flex items-center gap-2 border-b px-4 py-3 text-sm font-semibold"><Clock3 aria-hidden="true" className="h-4 w-4" />{t("mcpDocker.history", { defaultValue: "Recent activity" })}</h2>
                  {selectedHistory.length ? (
                    <ol className="divide-y">
                      {selectedHistory.map((event, index) => (
                        <li key={`${event.correlation_id}-${event.phase}-${index}`} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3 text-sm">
                          <span className="font-medium">{event.action} <span className="text-muted-foreground">· {event.phase}</span></span>
                          <time className="text-xs text-muted-foreground" dateTime={event.at}>{new Date(event.at).toLocaleString()}</time>
                        </li>
                      ))}
                    </ol>
                  ) : <p className="px-4 py-5 text-sm text-muted-foreground">{t("mcpDocker.noHistory", { defaultValue: "No activity recorded for this server." })}</p>}
                </section></details>
              </section>
            )}
          </div>}
          <McpDockerManagement snapshot={snapshot} selectedId={selectedId} selected={selected} refresh={refresh} installOpen={installOpen} setInstallOpen={setInstallOpen} onInstalled={setSelectedId} snapshotStale={Boolean(error)} onDraftChange={setHasDraft} />
          </div>
        ) : null}
      </div>
    </main>
  );
}
