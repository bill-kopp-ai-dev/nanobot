import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, fetchMcpDockerOperatorBootstrap, mutateMcpDocker, type McpDockerSnapshot } from "@/lib/api";
import { useClient } from "@/providers/ClientProvider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

type Server = McpDockerSnapshot["servers"][string];
type EnvRow = { id: number; name: string; kind: "plain" | "secret" | "reference"; value: string };

const SECRET_SENTINEL = "_REDACTED_MCP_ENV_SECRET";
let nextRowId = 0;
const emptyRow = (): EnvRow => ({ id: ++nextRowId, name: "", kind: "plain", value: "" });
const validImageReference = (type: "local-image" | "pinned-image", value: string) => type === "local-image"
  ? /^sha256:[0-9a-f]{64}$/.test(value)
  : /^[a-z0-9][a-z0-9._:/-]{0,199}@sha256:[0-9a-f]{64}$/.test(value);

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input className={cn("h-10 w-full rounded-md border bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", className)} {...props} />;
}

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea className={cn("min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", className)} {...props} />;
}

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium">{children}</label>;
}

function broaderMountAccess(previous: string[] | null | undefined, next: string[] | null): boolean {
  if (!previous) return false;
  if (!next) return true;
  const withinExisting = (path: string) => previous.some((old) => path === old || path.startsWith(`${old.replace(/\/$/, "")}/`));
  return next.some((path) => !withinExisting(path));
}

function invalidHostPaths(paths: string[]): boolean {
  return paths.some((path) => !path.startsWith("/") || path === "/" || path.includes("//") || path.endsWith("/") || path.split("/").some((segment) => segment === "." || segment === ".."));
}

function toEnvRows(server?: Server): EnvRow[] {
  if (!server) return [emptyRow()];
  const rows = Object.entries(server.configuration.env).map(([name, entry]) => ({
    id: ++nextRowId,
    name,
    kind: entry.kind as EnvRow["kind"],
    value: entry.kind === "secret" ? SECRET_SENTINEL : entry.value,
  }));
  return rows.length ? rows : [emptyRow()];
}

function envErrors(rows: EnvRow[], existing?: Server): string[] {
  const seen = new Set<string>();
  return rows.flatMap((row) => {
    if (!row.name && rows.length === 1 && !row.value) return [];
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(row.name)) return [`Invalid variable name: ${row.name || "(empty)"}`];
    if (seen.has(row.name)) return [`Duplicate variable: ${row.name}`];
    seen.add(row.name);
    if (row.value.includes("\0")) return [`Invalid value: ${row.name}`];
    if (row.kind === "reference" && !/^\$\{[A-Za-z_][A-Za-z0-9_]*\}$/.test(row.value)) return [`Reference for ${row.name} must be \${VAR}`];
    if (row.kind === "secret" && row.value === SECRET_SENTINEL &&
        existing?.configuration.env[row.name]?.kind !== "secret") return [`Enter a new value for ${row.name}`];
    if (row.kind === "secret" && !row.value) return [`Enter a value for ${row.name} or remove the variable`];
    return [];
  });
}

function envObject(rows: EnvRow[]): Record<string, { kind: string; value: string }> {
  return Object.fromEntries(rows.filter((row) => row.name).map((row) => [row.name, {
    kind: row.kind,
    value: row.value,
  }]));
}

function safeConfigPreview(config: Record<string, unknown>): string {
  const env = config.env && typeof config.env === "object" ? config.env as Record<string, { kind?: string; value?: string }> : {};
  const safeEnv = Object.fromEntries(Object.entries(env).map(([name, entry]) => [name, {
    kind: entry.kind,
    value: entry.kind === "secret" ? "•••• (redacted)" : entry.value,
  }]));
  return JSON.stringify({ ...config, env: safeEnv }, null, 2);
}

export function McpDockerManagement({
  snapshot,
  selectedId,
  selected,
  refresh,
  installOpen,
  setInstallOpen,
  onInstalled,
  snapshotStale = false,
  onDraftChange,
}: {
  snapshot: McpDockerSnapshot;
  selectedId: string | null;
  selected: Server | undefined;
  refresh: (quiet?: boolean) => Promise<McpDockerSnapshot | null>;
  installOpen: boolean;
  setInstallOpen: (open: boolean) => void;
  onInstalled: (id: string) => void;
  snapshotStale?: boolean;
  onDraftChange?: (dirty: boolean) => void;
}) {
  const { t } = useTranslation();
  const { client, getToken } = useClient();
  const [operatorConfigured, setOperatorConfigured] = useState<boolean | null>(null);
  const [operatorPassword, setOperatorPassword] = useState("");
  const [setupPassword, setSetupPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [restartRequired, setRestartRequired] = useState(false);
  const [awaitingRevision, setAwaitingRevision] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [installId, setInstallId] = useState("");
  const [installType, setInstallType] = useState<"local-image" | "pinned-image">("local-image");
  const [installReference, setInstallReference] = useState("");
  const [installPersistent, setInstallPersistent] = useState(false);
  const [installNetwork, setInstallNetwork] = useState<"none" | "bridge">("none");
  const [installMountMode, setInstallMountMode] = useState<"full" | "minimum" | "customized">("full");
  const [installMountsText, setInstallMountsText] = useState("");
  const [installEnvRows, setInstallEnvRows] = useState<EnvRow[]>([emptyRow()]);
  const [mountMode, setMountMode] = useState<"full" | "minimum" | "customized">("full");
  const [mountsText, setMountsText] = useState("");
  const [network, setNetwork] = useState<"none" | "bridge">("none");
  const [envRows, setEnvRows] = useState<EnvRow[]>([emptyRow()]);
  const [draftDirty, setDraftDirty] = useState(false);
  const [draftConflict, setDraftConflict] = useState(false);
  const [updateOpen, setUpdateOpen] = useState(false);
  const selectedIdRef = useRef<string | null>(null);
  const [installConfirmId, setInstallConfirmId] = useState("");
  const [scopeConfirmId, setScopeConfirmId] = useState("");
  const [updateConfirmId, setUpdateConfirmId] = useState("");
  const [excludeConfirmId, setExcludeConfirmId] = useState("");
  const [restoreConfirmId, setRestoreConfirmId] = useState<Record<string, string>>({});
  const [installReviewed, setInstallReviewed] = useState(false);
  const [configReviewed, setConfigReviewed] = useState(false);
  const [updateReviewed, setUpdateReviewed] = useState(false);
  const [updateReference, setUpdateReference] = useState("");
  const [updateType, setUpdateType] = useState<"local-image" | "pinned-image">("local-image");

  useEffect(() => { onDraftChange?.(draftDirty); }, [draftDirty, onDraftChange]);

  const globalRevisionRef = useRef(snapshot.revision);
  useEffect(() => {
    if (globalRevisionRef.current === snapshot.revision) return;
    globalRevisionRef.current = snapshot.revision;
    setInstallReviewed(false);
    setInstallConfirmId("");
    setConfigReviewed(false);
    setScopeConfirmId("");
    setUpdateReviewed(false);
    setUpdateConfirmId("");
    setExcludeConfirmId("");
    setRestoreConfirmId({});
    setDraftDirty(false);
    setDraftConflict(false);
  }, [snapshot.revision]);

  useEffect(() => {
    let mounted = true;
    void fetchMcpDockerOperatorBootstrap(getToken()).then((result) => {
      if (mounted) setOperatorConfigured(result.configured);
    }).catch((reason: unknown) => {
      if (mounted && reason instanceof ApiError && reason.status === 403) {
        setOperatorConfigured(true);
        setError(t("mcpDocker.remoteBootstrap", { defaultValue: "Credential status is local-only. Enter the existing operator password if remote administration is enabled." }));
      } else if (mounted) {
        setError(t("mcpDocker.adminStatusError", { defaultValue: "Could not check operator credential status." }));
      }
    });
    const unsubscribe = client.onStatus((status) => {
      if (status !== "open") setOperatorPassword("");
    });
    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [client, getToken, t]);

  const selectedRevisionRef = useRef<number | undefined>(undefined);
  useEffect(() => {
    const incomingRevision = selected?.revision;
    if (selectedIdRef.current !== selectedId) {
      selectedIdRef.current = selectedId;
      selectedRevisionRef.current = incomingRevision;
      setMountMode(selected?.configuration.mounts == null ? "full" : selected.configuration.mounts.length ? "customized" : "minimum");
      setMountsText((selected?.configuration.mounts ?? []).join("\n"));
      setNetwork(selected?.configuration.network === "bridge" ? "bridge" : "none");
      setEnvRows(toEnvRows(selected));
      setDraftDirty(false);
      setDraftConflict(false);
      setUpdateOpen(false);
      setScopeConfirmId("");
      setUpdateConfirmId("");
      setExcludeConfirmId("");
      setConfigReviewed(false);
      setUpdateReviewed(false);
      setUpdateReference(selected?.source.reference ?? "");
      setUpdateType((selected?.source.type === "pinned-image" ? "pinned-image" : "local-image"));
    } else if (selectedRevisionRef.current !== incomingRevision) {
      selectedRevisionRef.current = incomingRevision;
      setConfigReviewed(false);
      setUpdateReviewed(false);
      setScopeConfirmId("");
      setUpdateConfirmId("");
      if (draftDirty) setDraftConflict(true);
      else {
        setMountMode(selected?.configuration.mounts == null ? "full" : selected.configuration.mounts.length ? "customized" : "minimum");
        setMountsText((selected?.configuration.mounts ?? []).join("\n"));
        setNetwork(selected?.configuration.network === "bridge" ? "bridge" : "none");
        setEnvRows(toEnvRows(selected));
        setUpdateReference(selected?.source.reference ?? "");
        setUpdateType(selected?.source.type === "pinned-image" ? "pinned-image" : "local-image");
      }
    }
  }, [selectedId, selected, draftDirty]);

  const enabled = operatorConfigured === true && operatorPassword.length > 0 && !busy && snapshot.pendingTransitions.length === 0 && !snapshotStale && (awaitingRevision === null || snapshot.revision >= awaitingRevision);
  const mounts = mountMode === "full" ? null : mountMode === "minimum" ? [] : mountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean);
  const needsBroaderConfirm = useMemo(() => broaderMountAccess(
    selected?.configuration.mounts,
    mounts,
  ) || (selected?.configuration.network === "none" && network === "bridge"), [mounts, network, selected?.configuration.mounts, selected?.configuration.network]);

  const failMessage = useCallback((reason: unknown) => {
    if (reason instanceof ApiError) {
      if (reason.status === 401) return t("mcpDocker.adminUnauthorized", { defaultValue: "Operator password was rejected. Re-enter it and retry." });
      if (reason.status === 403) return t("mcpDocker.adminForbidden", { defaultValue: "Remote administration is disabled or this action requires a local browser." });
      if (reason.status === 409) return t("mcpDocker.conflict", { defaultValue: "The server changed since this page was loaded. The latest state has been refreshed." });
      if (reason.status === 503) return t("mcpDocker.brokerUnavailable", { defaultValue: "Docker MCP broker is unavailable; no successful result was confirmed." });
      if (reason.status === 502) return t("mcpDocker.actionError", { defaultValue: "The MCP Docker broker rejected the operation. Review the current server state before retrying." });
    }
    return t("mcpDocker.actionError", { defaultValue: "The operation could not be completed. Review the server state before retrying." });
  }, [t]);

  const invoke = useCallback(async (
    action: string,
    payload: Record<string, unknown>,
    options: { setup?: boolean; rotate?: boolean; success?: string } = {},
  ): Promise<McpDockerSnapshot | null> => {
    const submittedSetup = options.setup;
    const submittedRotate = options.rotate;
    setBusy(true);
    setError(null);
    setMessage(null);
    setRestartRequired(false);
    try {
      const result = await mutateMcpDocker<{ revision?: number; server?: string; mcp_runtime?: { requires_restart?: boolean } }>(client, action, {
        ...payload,
        operator_admin: options.setup ? setupPassword : operatorPassword,
      });
      const needsRuntimeRestart = result.mcp_runtime?.requires_restart === true;
      if (submittedSetup) {
        setOperatorPassword(setupPassword);
        setSetupPassword("");
        setOperatorConfigured(true);
      }
      if (submittedRotate) {
        setOperatorPassword(newPassword);
        setNewPassword("");
      }
      setInstallConfirmId("");
      setScopeConfirmId("");
      setUpdateConfirmId("");
      setExcludeConfirmId("");
      setRestoreConfirmId({});
      setInstallReviewed(false);
      setConfigReviewed(false);
      setUpdateReviewed(false);
      setRestartRequired(needsRuntimeRestart);
      const read = await refresh(true);
      const revisionOk = result.revision === undefined || (read ? read.revision >= result.revision : false);
      const serverOk = result.server === undefined || action === "exclude" || Boolean(read?.servers[result.server]);
      const verified = Boolean(read) && revisionOk && serverOk;
      setAwaitingRevision(verified ? null : result.revision ?? null);
      setMessage(verified ? (needsRuntimeRestart
        ? `${options.success ?? "Operation completed."} ${t("settings.status.savedRestartApply", { defaultValue: "Restart Percival to apply the change." })}`
        : options.success ?? "Operation completed; latest snapshot loaded.")
        : "Operation accepted, but the current state could not be verified. Refresh before another mutation.");
      return verified ? read : null;
    } catch (reason) {
      const latest = reason instanceof ApiError && [409, 502, 503].includes(reason.status) ? await refresh(true) : null;
      if (submittedSetup) {
        setSetupPassword("");
        if (reason instanceof ApiError && reason.status === 409) setOperatorConfigured(true);
      }
      if (submittedRotate) {
        setNewPassword("");
      }
      if (reason instanceof ApiError && reason.status === 401) {
        setOperatorPassword("");
        setSetupPassword("");
        setNewPassword("");
      }
      setError(reason instanceof ApiError && reason.status === 409 && !latest ? "Revision conflict; refresh failed. No further change is allowed until a current snapshot is available." : failMessage(reason));
      return null;
    } finally {
      setBusy(false);
    }
  }, [client, failMessage, newPassword, operatorPassword, refresh, setupPassword, t]);

  const revisionPayload = (serverId: string, server: Server) => ({
    server_id: serverId,
    expected_revision: snapshot.revision,
    expected_server_revision: server.revision,
  });

  const submitInstall = async () => {
    const serverId = installId.trim();
    const mounts = installMountMode === "full" ? null : installMountMode === "minimum" ? [] : installMountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean);
    const configuration = { persistent: installPersistent, mounts, network: installNetwork, env: envObject(installEnvRows) };
    const succeeded = await invoke("install", {
      server_id: serverId,
      expected_revision: snapshot.revision,
      source: { type: installType, reference: installReference.trim() },
      configuration,
    }, { success: t("mcpDocker.installComplete", { defaultValue: "Server installed; its current observed state is shown below." }) });
    if (succeeded?.servers[serverId]) {
      onInstalled(serverId);
      setInstallOpen(false);
      setInstallId("");
      setInstallReference("");
      setInstallEnvRows([emptyRow()]);
      setInstallMountMode("full");
      setInstallMountsText("");
      setInstallNetwork("none");
      setInstallReviewed(false);
    } else if (succeeded) {
      setMessage(`Operation accepted, but ${serverId} was not found in the refreshed snapshot.`);
    }
  };

  const submitConfigure = async () => {
    if (!selected || !selectedId) return;
    const result = await invoke("configure", {
      ...revisionPayload(selectedId, selected),
      configuration: {
        persistent: selected.configuration.persistent,
        mounts,
        network,
        env: envObject(envRows),
      },
    }, { success: t("mcpDocker.configureComplete", { defaultValue: "Host configuration saved; the broker restarted the server when needed." }) });
    if (result) { setDraftDirty(false); setDraftConflict(false); }
  };

  const serverAction = (action: string, extra: Record<string, unknown> = {}, options: { success?: string } = {}) => {
    if (!selected || !selectedId) return;
    return invoke(action, { ...revisionPayload(selectedId, selected), ...extra }, options);
  };

  const scopeConfirmationSatisfied = !needsBroaderConfirm || scopeConfirmId === selectedId;
  const installConfirmSatisfied = installConfirmId === installId.trim();
  const configChanged = selected !== undefined && JSON.stringify({ persistent: selected.configuration.persistent, mounts: selected.configuration.mounts ?? null, network: selected.configuration.network, env: Object.fromEntries(Object.entries(selected.configuration.env).map(([key, value]) => [key, { kind: value.kind, value: value.value }])) }) !== JSON.stringify({ persistent: selected?.configuration.persistent, mounts, network, env: envObject(envRows) });
  const configErrors = envErrors(envRows, selected);
  const installErrors = envErrors(installEnvRows);
  const mountError = mountMode === "customized" && (!mounts?.length || invalidHostPaths(mounts)) ? "Customized access requires canonical absolute paths (not /)." : null;
  const installPaths = installMountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean);
  const installMountError = installMountMode === "customized" && (!installPaths.length || invalidHostPaths(installPaths)) ? "Enter canonical absolute paths (not /) for customized access." : null;
  const markDraft = () => { setDraftDirty(true); setConfigReviewed(false); setScopeConfirmId(""); };
  const installPreviewEnv = installEnvRows.map((row) => ({ ...row, value: row.kind === "secret" ? "•••• (redacted)" : row.value }));
  const installConfigPreview = safeConfigPreview({
    persistent: installPersistent,
    mounts: installMountMode === "full" ? null : installMountMode === "minimum" ? [] : installMountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean),
    network: installNetwork,
    env: envObject(installPreviewEnv),
  });

  const envEditor = (rows: EnvRow[], updateRows: React.Dispatch<React.SetStateAction<EnvRow[]>>, editing = false) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold">{t("mcpDocker.envTitle", { defaultValue: "Environment variables" })}</h4>
        <Button type="button" variant="outline" size="sm" onClick={() => { if (editing) markDraft(); else setInstallReviewed(false); updateRows((current) => [...current, emptyRow()]); }}>
          {t("mcpDocker.addEnv", { defaultValue: "Add variable" })}
        </Button>
      </div>
      {rows.map((row, index) => (
        <div key={row.id} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_8rem_1.5fr_auto]">
          <Input aria-label={`${t("mcpDocker.envName", { defaultValue: "Variable name" })} ${index + 1}`} placeholder="API_TOKEN" value={row.name} onChange={(event) => { if (editing) markDraft(); else setInstallReviewed(false); updateRows((current) => current.map((item) => item.id === row.id ? { ...item, name: event.target.value } : item)); }} />
          <select aria-label={`${t("mcpDocker.envKind", { defaultValue: "Variable kind" })} ${index + 1}`} className="h-10 rounded-md border bg-background px-2 text-sm" value={row.kind} onChange={(event) => { if (editing) markDraft(); else setInstallReviewed(false); updateRows((current) => current.map((item) => item.id === row.id ? { ...item, kind: event.target.value as EnvRow["kind"], value: "" } : item)); }}>
            <option value="plain">plain</option><option value="secret">secret</option><option value="reference">reference</option>
          </select>
          <Input aria-label={`${t("mcpDocker.envValue", { defaultValue: "Variable value" })} ${index + 1}`} type={row.kind === "secret" ? "password" : "text"} autoComplete="new-password" placeholder={row.kind === "secret" && row.value === SECRET_SENTINEL ? "Leave unchanged to keep secret" : row.kind === "reference" ? "${VARIABLE}" : ""} value={row.value === SECRET_SENTINEL ? "" : row.value} onChange={(event) => { if (editing) markDraft(); else setInstallReviewed(false); updateRows((current) => current.map((item) => item.id === row.id ? { ...item, value: event.target.value || (item.value === SECRET_SENTINEL ? SECRET_SENTINEL : "") } : item)); }} />
          <Button type="button" variant="ghost" size="sm" aria-label={`Remove variable ${row.name || index + 1}`} onClick={() => { if (editing) markDraft(); else setInstallReviewed(false); updateRows((current) => current.filter((item) => item.id !== row.id)); }}>×</Button>
          {row.kind === "secret" && row.value === SECRET_SENTINEL && <span className="text-xs text-muted-foreground sm:col-span-4">{t("mcpDocker.secretPreserved", { defaultValue: "Existing secret stays unchanged; its value is never shown." })}</span>}
          <span className="text-xs text-muted-foreground sm:col-span-4">{row.kind === "plain" ? "Literal value stored in config" : row.kind === "secret" ? "Stored in config, redacted on reads; not an external vault" : "Resolved from the broker's environment; missing reference prevents start"}</span>
        </div>
      ))}
    </div>
  );

  return (
    <section className="space-y-5" aria-label={t("mcpDocker.management", { defaultValue: "MCP Docker management" })}>
      {(error || message) && <div role={error ? "alert" : "status"} className={cn("rounded-lg border p-3 text-sm", error ? "border-destructive/40 bg-destructive/5" : restartRequired || message?.startsWith("Operation accepted") ? "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-300" : "border-emerald-500/40 bg-emerald-500/5")}>{error ?? message}</div>}
      <p className="text-xs text-muted-foreground">Operator credential: {operatorPassword ? "provided (not verified until a mutation)" : "required"}</p>

      <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-semibold">{t("mcpDocker.operatorTitle", { defaultValue: "Operator authorization" })}</h2>
        {operatorConfigured === null ? <p className="text-sm text-muted-foreground">{t("mcpDocker.checkingAdmin", { defaultValue: "Checking local operator setup…" })}</p> : operatorConfigured ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {!operatorPassword && <form className="space-y-2" onSubmit={(event) => { event.preventDefault(); setOperatorPassword(setupPassword); setSetupPassword(""); setError(null); }}>
              <Label>{t("mcpDocker.adminPassword", { defaultValue: "Operator password" })}<Input type="password" autoComplete="current-password" maxLength={1024} value={setupPassword} onChange={(event) => setSetupPassword(event.target.value)} /></Label>
              <Button type="submit" disabled={!setupPassword || busy}>Provide password</Button>
            </form>}
            {operatorPassword && <form className="space-y-2" onSubmit={(event) => { event.preventDefault(); void invoke("operator-rotate", { new_password: newPassword }, { rotate: true, success: t("mcpDocker.passwordRotated", { defaultValue: "Operator password rotated." }) }); }}>
              <Label>{t("mcpDocker.newPassword", { defaultValue: "New operator password" })}<Input type="password" autoComplete="new-password" minLength={1} maxLength={1024} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></Label>
              <Button type="submit" variant="outline" disabled={!newPassword || busy}>{t("mcpDocker.rotatePassword", { defaultValue: "Rotate password" })}</Button>
            </form>}
            {operatorPassword && <p className="self-center text-xs text-muted-foreground">{t("mcpDocker.passwordMemoryOnly", { defaultValue: "The password remains in page memory only and is cleared when the WebSocket disconnects or this page closes." })}</p>}
          </div>
        ) : (
          <form className="grid gap-3 sm:grid-cols-[1fr_auto]" onSubmit={(event) => { event.preventDefault(); void invoke("operator-setup", {}, { setup: true, success: t("mcpDocker.passwordConfigured", { defaultValue: "Operator password configured." }) }); }}>
            <Label>{t("mcpDocker.setPassword", { defaultValue: "Set operator password" })}<Input type="password" autoComplete="new-password" maxLength={1024} value={setupPassword} onChange={(event) => setSetupPassword(event.target.value)} /></Label>
            <Button type="submit" className="self-end" disabled={!setupPassword || busy}>{t("mcpDocker.setupPassword", { defaultValue: "Configure password" })}</Button>
            <p className="text-xs text-muted-foreground sm:col-span-2">{t("mcpDocker.localSetupOnly", { defaultValue: "Initial setup requires a local browser. This password is separate from WebUI sign-in." })}</p>
          </form>
        )}
        <p className="text-xs text-muted-foreground">{snapshot.allowRemoteAdmin ? t("mcpDocker.remoteAdminEnabled", { defaultValue: "Remote operator administration is enabled by host configuration." }) : t("mcpDocker.remoteAdminDisabled", { defaultValue: "Remote operator administration is disabled by default; enable it only in trusted host configuration." })}</p>
      </section>

      {snapshot.pendingTransitions.length > 0 && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm">
        <strong>Recovery is pending; management mutations are blocked until the broker can reconcile these transitions.</strong>
        <ul className="mt-2 list-disc pl-5">{snapshot.pendingTransitions.map((transition) => <li key={transition.server_id}>{transition.server_id}{transition.action ? ` — ${transition.action}` : ""}</li>)}</ul>
      </div>}

      {installOpen && <section className="rounded-xl border p-4" aria-label="Add MCP server"><div className="flex items-center justify-between gap-2"><h2 className="font-semibold">Add MCP server</h2><Button variant="outline" onClick={() => { setInstallOpen(false); setInstallReviewed(false); setInstallConfirmId(""); }}>Cancel</Button></div>
        {!enabled && <p className="mt-3 text-sm text-muted-foreground">Provide the operator password above and load a current snapshot to install a server.</p>}
      {enabled && <div className="mt-4 space-y-4">
        <p className="text-sm text-amber-700 dark:text-amber-300">Only an exact image ID or RepoDigest already available locally is accepted; no pull. Full host file access is the default with mandatory control-plane covers.</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <Label>Server ID<Input value={installId} onChange={(event) => { setInstallId(event.target.value); setInstallReviewed(false); }} pattern="[a-z][a-z0-9-]{0,39}" placeholder="weather" /></Label>
          <Label>Image identity<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={installType} onChange={(event) => { setInstallType(event.target.value as typeof installType); setInstallReviewed(false); }}><option value="local-image">local image ID</option><option value="pinned-image">RepoDigest</option></select></Label>
        </div>
        <Label>Full image ID or RepoDigest<Input value={installReference} onChange={(event) => { setInstallReference(event.target.value); setInstallReviewed(false); }} placeholder={installType === "local-image" ? "sha256:…" : "registry/image@sha256:…"} /></Label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={installPersistent} onChange={(event) => { setInstallPersistent(event.target.checked); setInstallReviewed(false); }} />Enable persistent start/stop (opt-in)</label>
        <fieldset className="space-y-2 rounded-md border p-3"><legend className="px-1 font-semibold">Host access</legend>
          <label className="flex items-center gap-2 text-sm"><input type="radio" name="install-host-access" checked={installMountMode === "full"} onChange={() => { setInstallMountMode("full"); setInstallReviewed(false); }} />Full access — default, with mandatory covers</label>
          <label className="flex items-center gap-2 text-sm"><input type="radio" name="install-host-access" checked={installMountMode === "minimum"} disabled={!snapshot.minimumMountsSupported} onChange={() => { setInstallMountMode("minimum"); setInstallReviewed(false); }} />Minimum access — no host binds{!snapshot.minimumMountsSupported && " (host support unconfirmed)"}</label>
          <label className="flex items-center gap-2 text-sm"><input type="radio" name="install-host-access" checked={installMountMode === "customized"} onChange={() => { setInstallMountMode("customized"); setInstallReviewed(false); }} />Customized — selected absolute paths</label>
          {installMountMode === "customized" && <Label>Allowed absolute host paths, one per line<Textarea value={installMountsText} onChange={(event) => { setInstallMountsText(event.target.value); setInstallReviewed(false); }} placeholder="/srv/data" /></Label>}
        </fieldset>
        <Label>Network access<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={installNetwork} onChange={(event) => { setInstallNetwork(event.target.value as typeof installNetwork); setInstallReviewed(false); }}><option value="none">none — no Docker network</option>{snapshot.supportedNetworks?.includes("bridge") && <option value="bridge">bridge — Docker default bridge; external access depends on host networking</option>}</select></Label>
        {envEditor(installEnvRows, setInstallEnvRows)}
        <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs">{installConfigPreview}</pre>
        {(installMountError || installErrors.length > 0) && <p role="alert" className="text-sm text-destructive">{[installMountError, ...installErrors].filter(Boolean).join("; ")}</p>}
        <Label>Type the server ID to confirm this installation<Input value={installConfirmId} onChange={(event) => setInstallConfirmId(event.target.value)} /></Label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={installReviewed} onChange={(event) => setInstallReviewed(event.target.checked)} />I reviewed the installation scope and configuration preview.</label>
        <Button disabled={busy || !/^[a-z][a-z0-9-]{0,39}$/.test(installId.trim()) || !validImageReference(installType, installReference.trim()) || Boolean(installMountError) || installErrors.length > 0 || !installReviewed || !installConfirmSatisfied} onClick={() => void submitInstall()}>Install and activate</Button>
      </div>}</section>}

      {enabled && (
        <>
          {snapshot.backups.length > 0 && <details className="rounded-xl border p-4"><summary className="cursor-pointer font-semibold">Restore an excluded server ({snapshot.backups.filter((backup) => !snapshot.servers[backup.serverId]).length} eligible)</summary><section className="mt-4 space-y-3">
            <h2 className="font-semibold">Restore an excluded server</h2>
            <p className="text-sm text-muted-foreground">Restore checks the backup checksum, refuses to overwrite an existing server, and reconciles Docker before committing config.</p>
            {snapshot.backups.map((backup) => <div key={backup.backupId} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
              <div><code>{backup.serverId}</code><p className="text-xs text-muted-foreground">{backup.backupId} · revision {backup.sourceRevision}{backup.action ? ` · before ${backup.action}` : " · legacy backup (origin not recorded)"}</p>{snapshot.servers[backup.serverId] && <p className="text-xs">Server exists; this backup cannot overwrite it.</p>}</div>
              <Label>Type the server ID to restore<Input value={restoreConfirmId[backup.backupId] ?? ""} onChange={(event) => setRestoreConfirmId((current) => ({ ...current, [backup.backupId]: event.target.value }))} /></Label>
              <Button variant="outline" disabled={busy || Boolean(snapshot.servers[backup.serverId]) || restoreConfirmId[backup.backupId] !== backup.serverId} onClick={() => void invoke("restore", { backup_id: backup.backupId, expected_revision: snapshot.revision, expected_confirmation: restoreConfirmId[backup.backupId] }, { success: "Server restored from backup and reconciled." })}>Restore</Button>
            </div>)}
          </section></details>}

          {selected && selectedId && <section className="space-y-4 rounded-xl border p-4">
            <h2 className="font-semibold">{t("mcpDocker.manageServer", { defaultValue: "Manage {{server}}", server: selectedId })}</h2>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled={busy || !selected.active} onClick={() => void serverAction("restart", {}, { success: t("mcpDocker.restartComplete", { defaultValue: "Server restarted; its current observed state is shown below." }) })}>{t("mcpDocker.restart", { defaultValue: "Restart" })}</Button>
              {selected.active ? <Button variant="outline" disabled={busy} onClick={() => void serverAction("deactivate", {}, { success: t("mcpDocker.deactivateComplete", { defaultValue: "Server deactivated; tools remain in the registry but are no longer exposed." }) })}>{t("mcpDocker.deactivate", { defaultValue: "Deactivate" })}</Button> : <Button variant="outline" disabled={busy} onClick={() => void serverAction("activate", {}, { success: t("mcpDocker.activateComplete", { defaultValue: "Server reactivated; tools are exposed again." }) })}>{t("mcpDocker.activate", { defaultValue: "Activate" })}</Button>}
              {selected.configuration.persistent && selected.active && (selected.dockerObservation === "stopped" ? <Button variant="outline" disabled={busy} onClick={() => void serverAction("start", {}, { success: t("mcpDocker.startComplete", { defaultValue: "Persistent container started." }) })}>{t("mcpDocker.start", { defaultValue: "Start" })}</Button> : <Button variant="outline" disabled={busy || selected.dockerObservation !== "running"} onClick={() => void serverAction("stop", {}, { success: t("mcpDocker.stopComplete", { defaultValue: "Persistent container stopped." }) })}>{t("mcpDocker.stop", { defaultValue: "Stop" })}</Button>)}
              <Button variant="outline" disabled={selected.state === "stopped-persistent"} title={selected.state === "stopped-persistent" ? "Start the persistent server before updating its image" : undefined} onClick={() => setUpdateOpen(true)}>Update image</Button>
            </div>

            <Dialog open={updateOpen} onOpenChange={(open) => { setUpdateOpen(open); if (!open) { setUpdateReviewed(false); setUpdateConfirmId(""); } }}>
              <DialogContent>
                <DialogTitle>Update image for {selectedId}</DialogTitle>
                <DialogDescription>Use an immutable identity already available locally (no pull). Configuration is preserved. Rollback attempts the old image only if it is still available locally; old layers are not archived.</DialogDescription>
                <p className="break-all font-mono text-xs">Current: {selected.source.type}: {selected.source.reference}</p>
                <Label>Image identity<select className="h-10 w-full rounded-md border bg-background px-2 text-sm" value={updateType} onChange={(event) => { setUpdateType(event.target.value as typeof updateType); setUpdateReviewed(false); }}><option value="local-image">local image ID</option><option value="pinned-image">RepoDigest</option></select></Label>
                <Label>Full image ID or RepoDigest<Input value={updateReference} onChange={(event) => { setUpdateReference(event.target.value); setUpdateReviewed(false); }} /></Label>
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={updateReviewed} onChange={(event) => setUpdateReviewed(event.target.checked)} />I reviewed the image identity and rollback behavior.</label>
                <Label>Type {selectedId} to confirm this image update<Input value={updateConfirmId} onChange={(event) => setUpdateConfirmId(event.target.value)} /></Label>
                <div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setUpdateOpen(false)}>Cancel</Button><Button disabled={busy || !updateReviewed || updateConfirmId !== selectedId || !validImageReference(updateType, updateReference.trim()) || (updateType === selected.source.type && updateReference.trim() === selected.source.reference)} onClick={() => { void serverAction("update-image", { source: { type: updateType, reference: updateReference.trim() } }, { success: "Image updated and tools redetected." })?.then((read) => { if (read?.servers[selectedId]?.source.reference === updateReference.trim()) setUpdateOpen(false); }); }}>Update image</Button></div>
              </DialogContent>
            </Dialog>

            <details className="border-t pt-4"><summary className="cursor-pointer text-sm font-semibold">Per-tool access ({(selected.savedTools ?? selected.tools).length - selected.toolsDisabled.length} enabled / {selected.toolsDisabled.length} disabled)</summary><div className="mt-3 space-y-2">
              {(selected.savedTools ?? selected.tools).map((tool) => <div key={tool} className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm"><code>{tool}</code>{selected.toolsDisabled.includes(tool) ? <Button size="sm" variant="outline" disabled={busy} onClick={() => void serverAction("enable-tool", { tool }, { success: t("mcpDocker.toolEnabled", { defaultValue: "Tool re-enabled in the registry." }) })}>{t("mcpDocker.enableTool", { defaultValue: "Enable" })}</Button> : <Button size="sm" variant="outline" disabled={busy} onClick={() => void serverAction("disable-tool", { tool }, { success: t("mcpDocker.toolDisabled", { defaultValue: "Tool disabled in the registry." }) })}>{t("mcpDocker.disableTool", { defaultValue: "Disable" })}</Button>}</div>)}
              {!(selected.savedTools ?? selected.tools).length && <p className="text-sm text-muted-foreground">{t("mcpDocker.noToolsToManage", { defaultValue: "No discovered tools are available to manage." })}</p>}
            </div></details>

            <div className="space-y-3 border-t pt-4">
              <h3 className="text-sm font-semibold">{t("mcpDocker.configureHost", { defaultValue: "Configure host" })}</h3>
              <p className="text-sm text-muted-foreground">An active server is recreated when configuration changes. Protected control-plane paths remain covered where a host bind reaches them. Host access and network access are independent.</p>
              <fieldset className="space-y-2 rounded-md border p-3"><legend className="px-1 font-semibold">Host access</legend><p className="text-sm">Configured: {selected.configuration.mounts == null ? "Full access" : selected.configuration.mounts.length ? "Customized" : "Minimum access"}; observed mounts: {selected.effectiveConfiguration ? selected.effectiveConfiguration.mounts.length : "unavailable"}</p>
                <label className="flex items-center gap-2 text-sm"><input type="radio" name="host-access" checked={mountMode === "full"} onChange={() => { markDraft(); setMountMode("full"); }} />Full access — host filesystem except mandatory covers</label>
                <label className="flex items-center gap-2 text-sm"><input type="radio" name="host-access" checked={mountMode === "minimum"} disabled={!snapshot.minimumMountsSupported} onChange={() => { markDraft(); setMountMode("minimum"); }} />Minimum access — no host binds{!snapshot.minimumMountsSupported && " (host support unconfirmed)"}</label>
                <label className="flex items-center gap-2 text-sm"><input type="radio" name="host-access" checked={mountMode === "customized"} onChange={() => { markDraft(); setMountMode("customized"); }} />Customized — selected absolute paths</label>
                {mountMode === "customized" && <Label>Allowed absolute host paths, one per line<Textarea value={mountsText} onChange={(event) => { markDraft(); setMountsText(event.target.value); }} /></Label>}
              </fieldset>
              <Label>Network access<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={network} onChange={(event) => { markDraft(); setNetwork(event.target.value as typeof network); }}><option value="none">none — no Docker network</option>{(snapshot.supportedNetworks?.includes("bridge") || selected.configuration.network === "bridge") && <option value="bridge" disabled={!snapshot.supportedNetworks?.includes("bridge") && selected.configuration.network !== "bridge"}>bridge — Docker default bridge</option>}</select></Label>
              <p className="text-xs text-muted-foreground">Observed Docker network: {selected.effectiveConfiguration?.network ?? "unavailable"}. Bridge may allow external access, depending on host networking.</p>
              {envEditor(envRows, setEnvRows, true)}
              {(mountError || configErrors.length > 0 || draftConflict) && <p role="alert" className="text-sm text-destructive">{draftConflict ? "Server revision changed while editing. Review the latest configuration before saving." : [mountError, ...configErrors].filter(Boolean).join("; ")}</p>}
              {draftConflict && <Button variant="outline" onClick={() => { setMountMode(selected.configuration.mounts == null ? "full" : selected.configuration.mounts.length ? "customized" : "minimum"); setMountsText((selected.configuration.mounts ?? []).join("\n")); setNetwork(selected.configuration.network === "bridge" ? "bridge" : "none"); setEnvRows(toEnvRows(selected)); setDraftDirty(false); setDraftConflict(false); setConfigReviewed(false); }}>Discard draft and load latest</Button>}
              <div className={cn("rounded-md border p-3", needsBroaderConfirm ? "border-destructive/40 bg-destructive/5" : "border-emerald-500/40 bg-emerald-500/5")}>
                <p className="mb-2 text-xs font-semibold">{needsBroaderConfirm ? "Host or network access increases; type the server ID to confirm." : "Review the changes before saving."}</p>
                <ul className="list-disc space-y-1 pl-5 text-xs">
                  {JSON.stringify(selected.configuration.mounts ?? null) !== JSON.stringify(mounts) && <li>Host paths: {selected.configuration.mounts == null ? "Full" : selected.configuration.mounts.length ? "Customized" : "Minimum"} → {mountMode}</li>}
                  {selected.configuration.network !== network && <li>Network: {selected.configuration.network} → {network}</li>}
                  {[...new Set([...Object.keys(selected.configuration.env), ...envRows.map((row) => row.name).filter(Boolean)])].map((name) => {
                    const before = selected.configuration.env[name]; const after = envObject(envRows)[name];
                    const changed = !before ? "added" : !after ? "removed" : before.kind !== after.kind || before.value !== after.value ? "changed" : before.kind === "secret" ? "preserved" : "unchanged";
                    return changed === "unchanged" ? null : <li key={name}>{name}: {changed}{after?.kind === "secret" ? " (value redacted)" : ""}</li>;
                  })}
                </ul>
              </div>
              {needsBroaderConfirm && <Label>Type {selectedId} to confirm increased host or network access<Input value={scopeConfirmId} onChange={(event) => setScopeConfirmId(event.target.value)} /></Label>}
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={configReviewed} onChange={(event) => setConfigReviewed(event.target.checked)} />{t("mcpDocker.reviewedDiff", { defaultValue: "I reviewed the configuration diff and secret values are redacted." })}</label>
              {selected.state === "stopped-persistent" && <p className="text-sm text-amber-700">Start the persistent server before editing its container.</p>}
              {(() => {
                const hostSupportsMinimum = snapshot.minimumMountsSupported === true;
                const currentlyMinimum = (selected.configuration.mounts?.length ?? 0) === 0 && selected.configuration.mounts !== undefined;
                const switchingToMinimumWithoutSupport = mountMode === "minimum" && !currentlyMinimum && !hostSupportsMinimum;
                const switchingToBridgeWithoutSupport = network === "bridge" && selected.configuration.network !== "bridge" && snapshot.supportedNetworks?.includes("bridge") !== true;
                return (
                  <Button disabled={busy || !configChanged || !configReviewed || !scopeConfirmationSatisfied || Boolean(mountError) || configErrors.length > 0 || draftConflict || selected.state === "stopped-persistent" || switchingToMinimumWithoutSupport || switchingToBridgeWithoutSupport} onClick={() => void submitConfigure()}>{t("mcpDocker.saveConfiguration", { defaultValue: "Save configuration" })}</Button>
                );
              })()}
            </div>

            <div className="space-y-2 border-t border-destructive/30 pt-4">
              <h3 className="text-sm font-semibold text-destructive">{t("mcpDocker.excludeServer", { defaultValue: "Exclude server" })}</h3>
              <p className="text-sm text-muted-foreground">{t("mcpDocker.excludeWarning", { defaultValue: "This creates a backup, revokes tools and removes only the managed container and registry entry. It does not delete the image or volumes." })}</p>
              <Label>{t("mcpDocker.typeToExclude", { defaultValue: "Type {{server}} to exclude this server", server: selectedId })}<Input value={excludeConfirmId} onChange={(event) => setExcludeConfirmId(event.target.value)} /></Label>
              <Button variant="destructive" disabled={busy || excludeConfirmId !== selectedId} onClick={() => void serverAction("exclude", { expected_confirmation: selectedId }, { success: t("mcpDocker.excludeComplete", { defaultValue: "Server backed up and excluded; the image and volumes remain on disk." }) })}>{t("mcpDocker.exclude", { defaultValue: "Back up and exclude" })}</Button>
            </div>
          </section>}
        </>
      )}
    </section>
  );
}
