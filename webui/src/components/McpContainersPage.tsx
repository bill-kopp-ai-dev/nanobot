import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Box, CircleAlert, Clock3, RefreshCw } from "lucide-react";
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

function Status({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("w-fit max-w-full rounded-full border px-2.5 py-1 text-xs font-medium", statusTone(value))}>
        {value}
      </span>
    </div>
  );
}

export function McpContainersPage() {
  const { t } = useTranslation();
  const { getToken } = useClient();
  const [snapshot, setSnapshot] = useState<McpDockerSnapshot | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const refresh = useCallback(async (quiet = false) => {
    if (!mountedRef.current) return;
    if (quiet) setRefreshing(true);
    else setLoading(true);
    try {
      const result = await fetchMcpDockerSnapshot(getToken());
      if (!mountedRef.current) return;
      setSnapshot(result);
      setSelectedId((current) => current && result.servers[current] ? current : Object.keys(result.servers)[0] ?? null);
      setError(null);
    } catch (caught) {
      if (!mountedRef.current) return;
      if (caught instanceof ApiError && caught.status === 401) {
        setError(t("mcpDocker.unauthorized", { defaultValue: "You are not authorized to view Docker MCP status." }));
      } else {
        setError(t("mcpDocker.loadError", { defaultValue: "Could not load Docker MCP status. Try again." }));
      }
    } finally {
      if (mountedRef.current) {
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
          <Button variant="outline" onClick={() => void refresh(true)} disabled={refreshing}>
            <RefreshCw aria-hidden="true" className={cn("mr-2 h-4 w-4", refreshing && "animate-spin motion-reduce:animate-none")} />
            {t("mcpDocker.refresh", { defaultValue: "Refresh" })}
          </Button>
        </header>

        {error && (
          <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm">
            <span className="flex items-center gap-2"><CircleAlert aria-hidden="true" className="h-4 w-4" />{error}</span>
            <Button variant="outline" size="sm" onClick={() => void refresh()}>{t("mcpDocker.retry", { defaultValue: "Retry" })}</Button>
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
          </section><McpDockerManagement snapshot={snapshot} selectedId={null} selected={undefined} refresh={refresh} /></div>
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
                      onClick={() => setSelectedId(id)}
                      className={cn("w-full px-4 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring", selectedId === id && "bg-muted/60")}
                    >
                      <span className="block truncate font-medium">{id}</span>
                      <span className="mt-1 block truncate text-xs text-muted-foreground">{server.source.reference}</span>
                      <span className="mt-2 flex flex-wrap gap-1.5">
                        <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", statusTone(server.dockerObservation))}>{server.dockerObservation}</span>
                        <span className={cn("rounded-full border px-2 py-0.5 text-[11px]", statusTone(server.mcpConnectivity))}>{server.mcpConnectivity}</span>
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
                      <h2 id="mcp-server-detail-title" className="break-all text-lg font-semibold">{selectedId}</h2>
                      <p className="mt-1 break-all font-mono text-xs text-muted-foreground">{selected.source.type}: {selected.source.reference}</p>
                    </div>
                    <span className={cn("rounded-full border px-2.5 py-1 text-xs", selected.active ? statusTone("running") : statusTone("inactive"))}>
                      {selected.active ? t("mcpDocker.active", { defaultValue: "active" }) : t("mcpDocker.inactive", { defaultValue: "inactive" })}
                    </span>
                  </div>
                  <div className="mt-5 grid gap-4 sm:grid-cols-2">
                    <Status label={t("mcpDocker.dockerState", { defaultValue: "Docker state" })} value={selected.dockerObservation} />
                    <Status label={t("mcpDocker.mcpState", { defaultValue: "MCP connectivity" })} value={selected.mcpConnectivity} />
                    <Status label={t("mcpDocker.intentState", { defaultValue: "Gateway intent" })} value={selected.state} />
                    <Status label={t("mcpDocker.image", { defaultValue: "Image" })} value={selected.source.type} />
                  </div>
                  {selected.observationError && <p role="status" className="mt-4 text-sm text-amber-700 dark:text-amber-300">{selected.observationError}</p>}
                  <div className="mt-5 border-t pt-4">
                    <h3 className="text-sm font-semibold">{t("mcpDocker.hostMetadata", { defaultValue: "Host configuration metadata" })}</h3>
                    <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                      <div><dt className="text-xs text-muted-foreground">{t("mcpDocker.network", { defaultValue: "Network" })}</dt><dd>{selected.configuration.network}</dd></div>
                      <div><dt className="text-xs text-muted-foreground">{t("mcpDocker.persistence", { defaultValue: "Persistent container" })}</dt><dd>{selected.configuration.persistent ? t("common.yes", { defaultValue: "Yes" }) : t("common.no", { defaultValue: "No" })}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs text-muted-foreground">{t("mcpDocker.mounts", { defaultValue: "Mount reductions" })}</dt><dd className="break-words">{selected.configuration.mounts?.length ? selected.configuration.mounts.join(", ") : t("mcpDocker.defaultHostAccess", { defaultValue: "Default host file access with mandatory control-plane covers" })}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs text-muted-foreground">{t("mcpDocker.environment", { defaultValue: "Environment metadata" })}</dt><dd>{Object.entries(selected.configuration.env).length === 0 ? t("mcpDocker.none", { defaultValue: "None" }) : Object.entries(selected.configuration.env).map(([name, entry]) => `${name} (${entry.kind === "secret" ? entry.maskHint ?? "••••" : entry.kind})`).join(", ")}</dd></div>
                    </dl>
                    <div className="mt-4 border-t pt-3">
                      <h4 className="text-xs font-semibold">{t("mcpDocker.effectiveConfiguration", { defaultValue: "Observed effective Docker configuration" })}</h4>
                      {selected.effectiveConfiguration ? <dl className="mt-2 grid gap-2 text-xs sm:grid-cols-2"><div><dt className="text-muted-foreground">{t("mcpDocker.network", { defaultValue: "Network" })}</dt><dd>{selected.effectiveConfiguration.network}</dd></div><div className="sm:col-span-2"><dt className="text-muted-foreground">{t("mcpDocker.effectiveMounts", { defaultValue: "Actual mounts (target, type, access)" })}</dt><dd className="break-words">{selected.effectiveConfiguration.mounts.length ? selected.effectiveConfiguration.mounts.map((mount) => `${mount.destination} (${mount.type}, ${mount.readWrite ? "R/W" : "RO"})`).join(", ") : t("mcpDocker.none", { defaultValue: "None" })}</dd></div></dl> : <p className="mt-2 text-xs text-muted-foreground">{t("mcpDocker.effectiveUnknown", { defaultValue: "Effective Docker settings are unavailable until the broker can inspect the container." })}</p>}
                    </div>
                  </div>
                  <div className="mt-5 border-t pt-4">
                    <h3 className="text-sm font-semibold">{t("mcpDocker.tools", { defaultValue: "Discovered tools" })}</h3>
                    {selected.tools.length ? <ul className="mt-2 flex flex-wrap gap-2">{selected.tools.map((tool) => <li key={tool} className={cn("rounded-md border px-2 py-1 font-mono text-xs", selected.toolsDisabled.includes(tool) && "text-muted-foreground line-through")}>{tool}</li>)}</ul> : <p className="mt-2 text-sm text-muted-foreground">{t("mcpDocker.noTools", { defaultValue: "No tools currently observed." })}</p>}
                  </div>
                </div>

                <section aria-labelledby="mcp-history-title" className="rounded-xl border">
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
                </section>
              </section>
            )}
          </div>}
          <McpDockerManagement snapshot={snapshot} selectedId={selectedId} selected={selected} refresh={refresh} />
          </div>
        ) : null}
      </div>
    </main>
  );
}
