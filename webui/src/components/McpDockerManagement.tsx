import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, fetchMcpDockerOperatorBootstrap, mutateMcpDocker, type McpDockerSnapshot } from "@/lib/api";
import { useClient } from "@/providers/ClientProvider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Server = McpDockerSnapshot["servers"][string];
type EnvRow = { name: string; kind: "plain" | "secret" | "reference"; value: string };

const SECRET_SENTINEL = "_REDACTED_MCP_ENV_SECRET";

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

function toEnvRows(server?: Server): EnvRow[] {
  if (!server) return [{ name: "", kind: "plain", value: "" }];
  const rows = Object.entries(server.configuration.env).map(([name, entry]) => ({
    name,
    kind: entry.kind as EnvRow["kind"],
    value: entry.kind === "secret" ? SECRET_SENTINEL : entry.value,
  }));
  return rows.length ? rows : [{ name: "", kind: "plain", value: "" }];
}

function envObject(rows: EnvRow[]): Record<string, { kind: string; value: string }> {
  return Object.fromEntries(rows.filter((row) => row.name.trim()).map((row) => [row.name.trim(), {
    kind: row.kind,
    value: row.kind === "secret" && !row.value ? "" : row.value,
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
}: {
  snapshot: McpDockerSnapshot;
  selectedId: string | null;
  selected: Server | undefined;
  refresh: (quiet?: boolean) => Promise<void>;
}) {
  const { t } = useTranslation();
  const { client, getToken } = useClient();
  const [operatorConfigured, setOperatorConfigured] = useState<boolean | null>(null);
  const [operatorPassword, setOperatorPassword] = useState("");
  const [setupPassword, setSetupPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [installId, setInstallId] = useState("");
  const [installType, setInstallType] = useState<"local-image" | "pinned-image">("local-image");
  const [installReference, setInstallReference] = useState("");
  const [installPersistent, setInstallPersistent] = useState(false);
  const [installMountsRestricted, setInstallMountsRestricted] = useState(false);
  const [installMountsText, setInstallMountsText] = useState("");
  const [installEnvRows, setInstallEnvRows] = useState<EnvRow[]>([{ name: "", kind: "plain", value: "" }]);
  const [mountsRestricted, setMountsRestricted] = useState(false);
  const [mountsText, setMountsText] = useState("");
  const [envRows, setEnvRows] = useState<EnvRow[]>([{ name: "", kind: "plain", value: "" }]);
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
      setMountsRestricted(selected?.configuration.mounts != null);
      setMountsText((selected?.configuration.mounts ?? []).join("\n"));
      setEnvRows(toEnvRows(selected));
      setScopeConfirmId("");
      setUpdateConfirmId("");
      setExcludeConfirmId("");
      setConfigReviewed(false);
      setUpdateReviewed(false);
      setUpdateReference(selected?.source.reference ?? "");
      setUpdateType((selected?.source.type === "pinned-image" ? "pinned-image" : "local-image"));
    } else if (selectedRevisionRef.current !== incomingRevision) {
      selectedRevisionRef.current = incomingRevision;
      // Server config changed in the background (poll/admin mutex or concurrent edit).
      // Refresh derived UI state without touching user-confirmation flags.
      setMountsRestricted(selected?.configuration.mounts != null);
      setMountsText((selected?.configuration.mounts ?? []).join("\n"));
      setEnvRows(toEnvRows(selected));
      setUpdateReference(selected?.source.reference ?? "");
      setUpdateType((selected?.source.type === "pinned-image" ? "pinned-image" : "local-image"));
    }
  }, [selectedId, selected]);

  const enabled = operatorConfigured === true && operatorPassword.length > 0 && !busy && snapshot.pendingTransitions.length === 0;
  const needsBroaderConfirm = useMemo(() => broaderMountAccess(
    selected?.configuration.mounts,
    mountsRestricted ? mountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean) : null,
  ), [mountsRestricted, mountsText, selected?.configuration.mounts]);

  const failMessage = useCallback((reason: unknown) => {
    if (reason instanceof ApiError) {
      if (reason.status === 401) return t("mcpDocker.adminUnauthorized", { defaultValue: "Operator password was rejected. Re-enter it and retry." });
      if (reason.status === 403) return t("mcpDocker.adminForbidden", { defaultValue: "Remote administration is disabled or this action requires a local browser." });
      if (reason.status === 409) return t("mcpDocker.conflict", { defaultValue: "The server changed since this page was loaded. The latest state has been refreshed." });
      if (reason.status === 503) return t("mcpDocker.brokerUnavailable", { defaultValue: "Docker MCP broker is unavailable; no successful result was confirmed." });
    }
    return t("mcpDocker.actionError", { defaultValue: "The operation could not be completed. Review the server state before retrying." });
  }, [t]);

  const invoke = useCallback(async (
    action: string,
    payload: Record<string, unknown>,
    options: { setup?: boolean; rotate?: boolean; success?: string } = {},
  ) => {
    const submittedSetup = options.setup;
    const submittedRotate = options.rotate;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await mutateMcpDocker(client, action, {
        ...payload,
        operator_admin: options.setup ? setupPassword : operatorPassword,
      });
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
      setMessage(options.success ?? t("mcpDocker.operationComplete", { defaultValue: "Operation completed. Showing the verified server state." }));
      await refresh(true);
      return true;
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) await refresh(true);
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
      setError(failMessage(reason));
      return false;
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
    const mounts = installMountsRestricted ? installMountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean) : null;
    const configuration = { persistent: installPersistent, mounts, network: "none", env: envObject(installEnvRows) };
    const succeeded = await invoke("install", {
      server_id: serverId,
      expected_revision: snapshot.revision,
      source: { type: installType, reference: installReference.trim() },
      configuration,
    }, { success: t("mcpDocker.installComplete", { defaultValue: "Server installed; its current observed state is shown below." }) });
    if (succeeded) {
      setInstallId("");
      setInstallReference("");
      setInstallEnvRows([{ name: "", kind: "plain", value: "" }]);
      setInstallMountsRestricted(false);
      setInstallMountsText("");
      setInstallReviewed(false);
    }
  };

  const submitConfigure = async () => {
    if (!selected || !selectedId) return;
    const mounts = mountsRestricted ? mountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean) : null;
    await invoke("configure", {
      ...revisionPayload(selectedId, selected),
      configuration: {
        persistent: selected.configuration.persistent,
        mounts,
        network: "none",
        env: envObject(envRows),
      },
    }, { success: t("mcpDocker.configureComplete", { defaultValue: "Host configuration saved; the broker restarted the server when needed." }) });
  };

  const serverAction = (action: string, extra: Record<string, unknown> = {}, options: { success?: string } = {}) => {
    if (!selected || !selectedId) return;
    return invoke(action, { ...revisionPayload(selectedId, selected), ...extra }, options);
  };

  const scopeConfirmationSatisfied = !needsBroaderConfirm || scopeConfirmId === selectedId;
  const installConfirmSatisfied = installConfirmId === installId.trim();
  const displayedEnv = envRows.map((row) => ({ ...row, value: row.kind === "secret" ? "•••• (redacted)" : row.value }));
  const configPreview = safeConfigPreview({
    persistent: selected?.configuration.persistent ?? false,
    mounts: mountsRestricted ? mountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean) : null,
    network: "none",
    env: envObject(displayedEnv),
  });
  const installPreviewEnv = installEnvRows.map((row) => ({ ...row, value: row.kind === "secret" ? "•••• (redacted)" : row.value }));
  const installConfigPreview = safeConfigPreview({
    persistent: installPersistent,
    mounts: installMountsRestricted ? installMountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean) : null,
    network: "none",
    env: envObject(installPreviewEnv),
  });

  const envEditor = (rows: EnvRow[], updateRows: React.Dispatch<React.SetStateAction<EnvRow[]>>) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold">{t("mcpDocker.envTitle", { defaultValue: "Environment variables" })}</h4>
        <Button type="button" variant="outline" size="sm" onClick={() => updateRows((current) => [...current, { name: "", kind: "plain", value: "" }])}>
          {t("mcpDocker.addEnv", { defaultValue: "Add variable" })}
        </Button>
      </div>
      {rows.map((row, index) => (
        <div key={`${row.name}-${index}`} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_8rem_1.5fr_auto]">
          <Input aria-label={t("mcpDocker.envName", { defaultValue: "Variable name" })} placeholder="API_TOKEN" value={row.name} onChange={(event) => updateRows((current) => current.map((item, i) => i === index ? { ...item, name: event.target.value } : item))} />
          <select aria-label={t("mcpDocker.envKind", { defaultValue: "Variable kind" })} className="h-10 rounded-md border bg-background px-2 text-sm" value={row.kind} onChange={(event) => updateRows((current) => current.map((item, i) => i === index ? { ...item, kind: event.target.value as EnvRow["kind"], value: "" } : item))}>
            <option value="plain">plain</option><option value="secret">secret</option><option value="reference">reference</option>
          </select>
          <Input aria-label={t("mcpDocker.envValue", { defaultValue: "Variable value" })} type={row.kind === "secret" ? "password" : "text"} autoComplete="new-password" placeholder={row.kind === "secret" && row.value === SECRET_SENTINEL ? t("mcpDocker.keepSecret", { defaultValue: "Leave unchanged to keep secret" }) : row.kind === "reference" ? "${VARIABLE}" : ""} value={row.value === SECRET_SENTINEL ? "" : row.value} onChange={(event) => updateRows((current) => current.map((item, i) => i === index ? { ...item, value: event.target.value } : item))} />
          <Button type="button" variant="ghost" size="sm" aria-label={t("mcpDocker.removeEnv", { defaultValue: "Remove variable" })} onClick={() => updateRows((current) => current.filter((_, i) => i !== index))}>×</Button>
          {row.kind === "secret" && row.value === SECRET_SENTINEL && <span className="text-xs text-muted-foreground sm:col-span-4">{t("mcpDocker.secretPreserved", { defaultValue: "Existing secret stays unchanged; its value is never shown." })}</span>}
        </div>
      ))}
    </div>
  );

  return (
    <section className="space-y-5" aria-label={t("mcpDocker.management", { defaultValue: "MCP Docker management" })}>
      {(error || message) && <div role={error ? "alert" : "status"} className={cn("rounded-lg border p-3 text-sm", error ? "border-destructive/40 bg-destructive/5" : "border-emerald-500/40 bg-emerald-500/5")}>{error ?? message}</div>}

      <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-semibold">{t("mcpDocker.operatorTitle", { defaultValue: "Operator authorization" })}</h2>
        {operatorConfigured === null ? <p className="text-sm text-muted-foreground">{t("mcpDocker.checkingAdmin", { defaultValue: "Checking local operator setup…" })}</p> : operatorConfigured ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {!operatorPassword && <form className="space-y-2" onSubmit={(event) => { event.preventDefault(); setOperatorPassword(setupPassword); setSetupPassword(""); setError(null); }}>
              <Label>{t("mcpDocker.adminPassword", { defaultValue: "Operator password" })}<Input type="password" autoComplete="current-password" maxLength={1024} value={setupPassword} onChange={(event) => setSetupPassword(event.target.value)} /></Label>
              <Button type="submit" disabled={!setupPassword || busy}>{t("mcpDocker.unlock", { defaultValue: "Unlock management" })}</Button>
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

      {enabled && (
        <>
          <details className="rounded-xl border p-4">
            <summary className="cursor-pointer font-semibold">{t("mcpDocker.installTitle", { defaultValue: "Install a local image" })}</summary>
            <div className="mt-4 space-y-4">
              <p className="text-sm text-amber-700 dark:text-amber-300">{t("mcpDocker.installWarning", { defaultValue: "Installation uses broad host file access by default, with mandatory control-plane covers. Only an exact local image ID or local RepoDigest is accepted; no pull is performed." })}</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <Label>{t("mcpDocker.serverId", { defaultValue: "Server ID" })}<Input value={installId} onChange={(event) => setInstallId(event.target.value)} pattern="[a-z][a-z0-9-]{0,39}" placeholder="weather" /></Label>
                <Label>{t("mcpDocker.imageKind", { defaultValue: "Image identity" })}<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={installType} onChange={(event) => setInstallType(event.target.value as typeof installType)}><option value="local-image">local image ID</option><option value="pinned-image">RepoDigest</option></select></Label>
              </div>
              <Label>{t("mcpDocker.imageReference", { defaultValue: "Full image ID or RepoDigest" })}<Input value={installReference} onChange={(event) => setInstallReference(event.target.value)} placeholder={installType === "local-image" ? "sha256:…" : "registry/image@sha256:…"} /></Label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={installPersistent} onChange={(event) => setInstallPersistent(event.target.checked)} />{t("mcpDocker.persistentOptIn", { defaultValue: "Enable persistent start/stop (opt-in)" })}</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={installMountsRestricted} onChange={(event) => setInstallMountsRestricted(event.target.checked)} />{t("mcpDocker.restrictMounts", { defaultValue: "Use reduced host paths instead of the default broad file access" })}</label>
              {installMountsRestricted && <Label>{t("mcpDocker.mountPaths", { defaultValue: "Allowed absolute host paths, one per line" })}<Textarea value={installMountsText} onChange={(event) => setInstallMountsText(event.target.value)} placeholder="/srv/data" /></Label>}
              <p className="text-xs text-muted-foreground">{t("mcpDocker.networkFixed", { defaultValue: "Network access is fixed to none by the current broker contract. Protected Docker/state paths are always covered and cannot be re-enabled here." })}</p>
              {envEditor(installEnvRows, setInstallEnvRows)}
              <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs">{installConfigPreview}</pre>
              <Label>{t("mcpDocker.typeServerId", { defaultValue: "Type the server ID to confirm this broad-access installation" })}<Input value={installConfirmId} onChange={(event) => setInstallConfirmId(event.target.value)} /></Label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={installReviewed} onChange={(event) => setInstallReviewed(event.target.checked)} />{t("mcpDocker.reviewInstall", { defaultValue: "I reviewed the installation scope and configuration preview." })}</label>
              <Button disabled={busy || !installId.trim() || !installReference.trim() || !installReviewed || !installConfirmSatisfied} onClick={() => void submitInstall()}>{t("mcpDocker.install", { defaultValue: "Install and activate" })}</Button>
            </div>
          </details>

          <section className="space-y-3 rounded-xl border p-4">
            <h2 className="font-semibold">Restore an excluded server</h2>
            <p className="text-sm text-muted-foreground">Restore checks the backup checksum, refuses to overwrite an existing server, and reconciles Docker before committing config.</p>
            {snapshot.backups.map((backup) => <div key={backup.backupId} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
              <div><code>{backup.serverId}</code><p className="text-xs text-muted-foreground">{backup.backupId} · revision {backup.sourceRevision}</p></div>
              <Label>Type the server ID to restore<Input value={restoreConfirmId[backup.backupId] ?? ""} onChange={(event) => setRestoreConfirmId((current) => ({ ...current, [backup.backupId]: event.target.value }))} /></Label>
              <Button variant="outline" disabled={busy || Boolean(snapshot.servers[backup.serverId]) || restoreConfirmId[backup.backupId] !== backup.serverId} onClick={() => void invoke("restore", { backup_id: backup.backupId, expected_revision: snapshot.revision }, { success: "Server restored from backup and reconciled." })}>Restore</Button>
            </div>)}
            {!snapshot.backups.length && <p className="text-sm text-muted-foreground">No MCP Docker backups are available.</p>}
          </section>

          {selected && selectedId && <section className="space-y-4 rounded-xl border p-4">
            <h2 className="font-semibold">{t("mcpDocker.manageServer", { defaultValue: "Manage {{server}}", server: selectedId })}</h2>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled={busy || !selected.active} onClick={() => void serverAction("restart", {}, { success: t("mcpDocker.restartComplete", { defaultValue: "Server restarted; its current observed state is shown below." }) })}>{t("mcpDocker.restart", { defaultValue: "Restart" })}</Button>
              {selected.active ? <Button variant="outline" disabled={busy} onClick={() => void serverAction("deactivate", {}, { success: t("mcpDocker.deactivateComplete", { defaultValue: "Server deactivated; tools remain in the registry but are no longer exposed." }) })}>{t("mcpDocker.deactivate", { defaultValue: "Deactivate" })}</Button> : <Button variant="outline" disabled={busy} onClick={() => void serverAction("activate", {}, { success: t("mcpDocker.activateComplete", { defaultValue: "Server reactivated; tools are exposed again." }) })}>{t("mcpDocker.activate", { defaultValue: "Activate" })}</Button>}
              {selected.configuration.persistent && selected.active && (selected.dockerObservation === "stopped" ? <Button variant="outline" disabled={busy} onClick={() => void serverAction("start", {}, { success: t("mcpDocker.startComplete", { defaultValue: "Persistent container started." }) })}>{t("mcpDocker.start", { defaultValue: "Start" })}</Button> : <Button variant="outline" disabled={busy || selected.dockerObservation !== "running"} onClick={() => void serverAction("stop", {}, { success: t("mcpDocker.stopComplete", { defaultValue: "Persistent container stopped." }) })}>{t("mcpDocker.stop", { defaultValue: "Stop" })}</Button>)}
            </div>

            <div className="space-y-2 border-t pt-4">
              <h3 className="text-sm font-semibold">{t("mcpDocker.toolAccess", { defaultValue: "Per-tool access" })}</h3>
              {selected.tools.map((tool) => <div key={tool} className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm"><code>{tool}</code>{selected.toolsDisabled.includes(tool) ? <Button size="sm" variant="outline" disabled={busy} onClick={() => void serverAction("enable-tool", { tool }, { success: t("mcpDocker.toolEnabled", { defaultValue: "Tool re-enabled in the registry." }) })}>{t("mcpDocker.enableTool", { defaultValue: "Enable" })}</Button> : <Button size="sm" variant="outline" disabled={busy} onClick={() => void serverAction("disable-tool", { tool }, { success: t("mcpDocker.toolDisabled", { defaultValue: "Tool disabled in the registry." }) })}>{t("mcpDocker.disableTool", { defaultValue: "Disable" })}</Button>}</div>)}
              {!selected.tools.length && <p className="text-sm text-muted-foreground">{t("mcpDocker.noToolsToManage", { defaultValue: "No discovered tools are available to manage." })}</p>}
            </div>

            <div className="space-y-3 border-t pt-4">
              <h3 className="text-sm font-semibold">{t("mcpDocker.configureHost", { defaultValue: "Configure host" })}</h3>
              <p className="text-sm text-muted-foreground">{t("mcpDocker.mountRisk", { defaultValue: "Host file access is broad by default. Adding narrower paths reduces access; removing or widening reductions increases access. Protected control-plane covers are enforced by the broker." })}</p>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={mountsRestricted} onChange={(event) => setMountsRestricted(event.target.checked)} />{t("mcpDocker.restrictMounts", { defaultValue: "Use reduced host paths instead of the default broad file access" })}</label>
              {mountsRestricted && <Label>{t("mcpDocker.mountPaths", { defaultValue: "Allowed absolute host paths, one per line" })}<Textarea value={mountsText} onChange={(event) => setMountsText(event.target.value)} /></Label>}
              <p className="text-xs text-muted-foreground">{t("mcpDocker.networkFixed", { defaultValue: "Network access is fixed to none by the current broker contract. Protected Docker/state paths are always covered and cannot be re-enabled here." })}</p>
              {envEditor(envRows, setEnvRows)}
              <div className={cn("rounded-md border p-3", needsBroaderConfirm ? "border-destructive/40 bg-destructive/5" : "border-emerald-500/40 bg-emerald-500/5")}>
                <p className="mb-2 text-xs font-semibold">{needsBroaderConfirm ? t("mcpDocker.scopeIncrease", { defaultValue: "This change increases host access; the server ID confirmation is required." }) : t("mcpDocker.scopeReduction", { defaultValue: "This change does not increase host path access. Review explicitly before saving." })}</p>
                <div className="grid gap-3 xl:grid-cols-2"><div><p className="mb-1 text-xs font-medium">{t("mcpDocker.before", { defaultValue: "Before" })}</p><pre className="max-h-48 overflow-auto rounded bg-muted p-3 text-xs">{safeConfigPreview({ ...selected.configuration, env: Object.fromEntries(Object.entries(selected.configuration.env).map(([name, value]) => [name, { kind: value.kind, value: value.value }])) })}</pre></div><div><p className="mb-1 text-xs font-medium">{t("mcpDocker.after", { defaultValue: "After" })}</p><pre className="max-h-48 overflow-auto rounded bg-muted p-3 text-xs">{configPreview}</pre></div></div>
              </div>
              {needsBroaderConfirm && <Label>{t("mcpDocker.typeServerId", { defaultValue: "Type the server ID to confirm this broad-access installation" })}<Input value={scopeConfirmId} onChange={(event) => setScopeConfirmId(event.target.value)} /></Label>}
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={configReviewed} onChange={(event) => setConfigReviewed(event.target.checked)} />{t("mcpDocker.reviewedDiff", { defaultValue: "I reviewed the configuration diff and secret values are redacted." })}</label>
              <Button disabled={busy || !configReviewed || !scopeConfirmationSatisfied} onClick={() => void submitConfigure()}>{t("mcpDocker.saveConfiguration", { defaultValue: "Save configuration" })}</Button>
            </div>

            <div className="grid gap-3 border-t pt-4 sm:grid-cols-[1fr_auto]">
              <div className="space-y-2"><h3 className="text-sm font-semibold">{t("mcpDocker.updateImage", { defaultValue: "Update image" })}</h3><p className="text-xs text-muted-foreground">{selected.source.reference} → {updateReference || "…"}</p><div className="flex gap-2"><select aria-label={t("mcpDocker.imageKind", { defaultValue: "Image identity" })} className="h-10 rounded-md border bg-background px-2 text-sm" value={updateType} onChange={(event) => setUpdateType(event.target.value as typeof updateType)}><option value="local-image">local image ID</option><option value="pinned-image">RepoDigest</option></select><Input aria-label={t("mcpDocker.imageReference", { defaultValue: "Full image ID or RepoDigest" })} value={updateReference} onChange={(event) => setUpdateReference(event.target.value)} /></div><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={updateReviewed} onChange={(event) => setUpdateReviewed(event.target.checked)} />{t("mcpDocker.reviewUpdate", { defaultValue: "I reviewed the new immutable image identity and rollback behavior." })}</label><Label>{t("mcpDocker.typeToUpdate", { defaultValue: "Type {{server}} to confirm this image update", server: selectedId })}<Input value={updateConfirmId} onChange={(event) => setUpdateConfirmId(event.target.value)} /></Label></div>
              <Button className="self-end" variant="outline" disabled={busy || !updateReviewed || updateConfirmId !== selectedId || !updateReference.trim()} onClick={() => void serverAction("update-image", { source: { type: updateType, reference: updateReference.trim() } }, { success: t("mcpDocker.updateImageComplete", { defaultValue: "Image updated and tools redetected." }) })}>{t("mcpDocker.updateImage", { defaultValue: "Update image" })}</Button>
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
