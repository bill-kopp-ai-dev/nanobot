import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, mutateMcpDocker, type McpDockerSnapshot } from "@/lib/api";
import { useClient } from "@/providers/ClientProvider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { elevate, ElevationError } from "@/lib/bootstrap";

type Server = McpDockerSnapshot["servers"][string];
type CatalogApp = NonNullable<McpDockerSnapshot["catalogs"]>[number]["apps"][number];
type CatalogChoice = { catalogId: string; app: CatalogApp };
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
  const { client, session } = useClient();
  const [elevationPassword, setElevationPassword] = useState("");
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
  const [catalogIdToRegister, setCatalogIdToRegister] = useState("pblabs");
  const [catalogRegisterConfirmation, setCatalogRegisterConfirmation] = useState("");
  const [schemaMigrationConfirmation, setSchemaMigrationConfirmation] = useState("");
  const [catalogSelection, setCatalogSelection] = useState("");
  const [catalogServerId, setCatalogServerId] = useState("");
  const [catalogMountSources, setCatalogMountSources] = useState<Record<string, string>>({});
  const [catalogEnvironment, setCatalogEnvironment] = useState<Record<string, string>>({});
  const [catalogNetwork, setCatalogNetwork] = useState<"none" | "bridge">("none");
  const [catalogInstallConfirmation, setCatalogInstallConfirmation] = useState("");
  const [schemaRestoreConfirmations, setSchemaRestoreConfirmations] = useState<Record<string, string>>({});

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
    setCatalogRegisterConfirmation("");
    setSchemaMigrationConfirmation("");
    setCatalogInstallConfirmation("");
    setCatalogSelection("");
    setCatalogServerId("");
    setCatalogMountSources({});
    setCatalogEnvironment({});
    setSchemaRestoreConfirmations({});
    setDraftDirty(false);
    setDraftConflict(false);
  }, [snapshot.revision]);

  useEffect(() => {
    const unsubscribe = client.onStatus((status) => {
      if (status !== "open") setElevationPassword("");
    });
    return () => {
      unsubscribe();
    };
  }, [client]);

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

  const elevated = session.elevated;
  const selectedAppRelease = selectedId ? snapshot.appReleases?.[selectedId] : undefined;
  const enabled = elevated && !busy && snapshot.pendingTransitions.length === 0 && !snapshotStale && (awaitingRevision === null || snapshot.revision >= awaitingRevision);
  const mounts = mountMode === "full" ? null : mountMode === "minimum" ? [] : mountsText.split(/\r?\n/).map((path) => path.trim()).filter(Boolean);
  const needsBroaderConfirm = useMemo(() => broaderMountAccess(
    selected?.configuration.mounts,
    mounts,
  ) || (selected?.configuration.network === "none" && network === "bridge"), [mounts, network, selected?.configuration.mounts, selected?.configuration.network]);
  const catalogChoices = useMemo<CatalogChoice[]>(() => (snapshot.catalogs ?? [])
    .filter((catalog) => catalog.status === "ready")
    .flatMap((catalog) => catalog.apps.map((app) => ({ catalogId: catalog.catalogId, app }))), [snapshot.catalogs]);
  const selectedCatalogChoice = catalogChoices.find((choice) => `${choice.catalogId}:${choice.app.id}` === catalogSelection);
  const catalogInstallPhrase = selectedCatalogChoice
    ? `${catalogServerId.trim()}/${selectedCatalogChoice.app.id}@${selectedCatalogChoice.app.version}`
    : "";
  const catalogRequiredMountMissing = selectedCatalogChoice?.app.mounts.some((mount) => mount.required && !catalogMountSources[mount.target]?.trim()) ?? false;
  const catalogInvalidMount = selectedCatalogChoice?.app.mounts.some((mount) => {
    const value = catalogMountSources[mount.target]?.trim();
    return Boolean(value && invalidHostPaths([value]));
  }) ?? false;
  const catalogMissingEnvironment = selectedCatalogChoice?.app.environmentVariables.some(
    (variable) => variable.required && !catalogEnvironment[variable.name]?.trim(),
  ) ?? false;
  const catalogBrokerReady = snapshot.minimumMountsSupported === true && snapshot.appMountsSupported === true && snapshot.catalogAcquisitionSupported === true;
  const catalogInstallReady = Boolean(
    enabled && snapshot.schemaVersion === 2 && catalogBrokerReady && selectedCatalogChoice &&
    /^[a-z][a-z0-9-]{0,39}$/.test(catalogServerId.trim()) && !catalogRequiredMountMissing &&
    !catalogInvalidMount && !catalogMissingEnvironment && catalogInstallConfirmation === catalogInstallPhrase,
  );

  const failMessage = useCallback((reason: unknown) => {
    if (reason instanceof ApiError) {
      if (reason.status === 401) return t("mcpDocker.adminUnauthorized", { defaultValue: "Your session expired. Sign in again to continue." });
      if (reason.status === 403) return t("mcpDocker.adminForbidden", { defaultValue: "This action requires elevated authorization. Re-enter the instance password and try again." });
      if (reason.status === 409) return t("mcpDocker.conflict", { defaultValue: "The server changed since this page was loaded. The latest state has been refreshed." });
      if (reason.status === 503) return t("mcpDocker.brokerUnavailable", { defaultValue: "Docker MCP broker is unavailable; no successful result was confirmed." });
      if (reason.status === 502) return t("mcpDocker.actionError", { defaultValue: "The MCP Docker broker rejected the operation. Review the current server state before retrying." });
    }
    return t("mcpDocker.actionError", { defaultValue: "The operation could not be completed. Review the server state before retrying." });
  }, [t]);

  const invoke = useCallback(async (
    action: string,
    payload: Record<string, unknown>,
    options: { success?: string } = {},
  ): Promise<McpDockerSnapshot | null> => {
    setBusy(true);
    setError(null);
    setMessage(null);
    setRestartRequired(false);
    try {
      if (!session.elevated && elevationPassword) {
        try {
          await elevate(elevationPassword, session.csrfToken);
          await session.refreshElevation();
        } catch (reason) {
          setElevationPassword("");
          if (reason instanceof ElevationError) {
            setError(t("mcpDocker.elevationRejected", { defaultValue: "The instance password was rejected; cannot elevate this session." }));
            return null;
          }
          throw reason;
        }
      }
      const result = await mutateMcpDocker<{ revision?: number; server?: string; mcp_runtime?: { requires_restart?: boolean } }>(client, action, payload);
      const needsRuntimeRestart = result.mcp_runtime?.requires_restart === true;
      setInstallConfirmId("");
      setScopeConfirmId("");
      setUpdateConfirmId("");
      setExcludeConfirmId("");
      setRestoreConfirmId({});
      setInstallReviewed(false);
      setConfigReviewed(false);
      setUpdateReviewed(false);
      setRestartRequired(needsRuntimeRestart);
      setElevationPassword("");
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
      if (reason instanceof ApiError && reason.status === 401) {
        setElevationPassword("");
      }
      setError(reason instanceof ApiError && reason.status === 409 && !latest ? "Revision conflict; refresh failed. No further change is allowed until a current snapshot is available." : failMessage(reason));
      return null;
    } finally {
      setBusy(false);
    }
  }, [client, elevationPassword, failMessage, refresh, session, t]);

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

  const registerLocalCatalog = async () => {
    const candidate = snapshot.localCatalogCandidate;
    const catalogId = catalogIdToRegister.trim();
    if (!candidate || candidate.status !== "ready" || !candidate.snapshotSha256) return;
    await invoke("register-catalog", {
      catalog_id: catalogId,
      snapshot_sha256: candidate.snapshotSha256,
      expected_revision: snapshot.revision,
      expected_confirmation: catalogRegisterConfirmation,
    }, { success: "Local catalog snapshot pinned; entries remain subject to broker policy and per-install consent." });
    setCatalogRegisterConfirmation("");
  };

  const migrateCatalogConfig = async () => {
    await invoke("migrate-schema", {
      expected_revision: snapshot.revision,
      expected_confirmation: schemaMigrationConfirmation,
    }, { success: "MCP configuration migrated to schema 2 with a private v1 backup." });
    setSchemaMigrationConfirmation("");
  };

  const exportCapabilities = async () => {
    await invoke("export-capabilities", {}, { success: "Sanitized capabilities.lock exported from the current manager state." });
  };

  const restoreSchema = async (backupId: string) => {
    await invoke("restore-schema-v1", {
      backup_id: backupId,
      expected_revision: snapshot.revision,
      expected_confirmation: schemaRestoreConfirmations[backupId] ?? "",
    }, { success: "MCP schema restored to v1 from the migration snapshot." });
    setSchemaRestoreConfirmations((current) => ({ ...current, [backupId]: "" }));
  };

  const submitCatalogInstall = async () => {
    if (!selectedCatalogChoice) return;
    const { app, catalogId } = selectedCatalogChoice;
    const serverId = catalogServerId.trim();
    const mountSources: Record<string, string> = {};
    for (const [target, source] of Object.entries(catalogMountSources)) {
      if (source.trim()) mountSources[target] = source.trim();
    }
    const environment: Record<string, { kind: "secret" | "plain"; value: string }> = {};
    for (const variable of app.environmentVariables) {
      const value = catalogEnvironment[variable.name]?.trim() ?? "";
      if (value) environment[variable.name] = { kind: variable.secret ? "secret" : "plain", value };
    }
    const result = await invoke("install-catalog", {
      catalog_id: catalogId,
      app_id: app.id,
      server_id: serverId,
      expected_revision: snapshot.revision,
      expected_confirmation: catalogInstallConfirmation,
      mount_sources: mountSources,
      environment,
      host_mounts: [],
      network: catalogNetwork,
    }, { success: `Installed ${app.name}@${app.version} from the pinned local catalog.` });
    if (result?.servers[serverId]) {
      onInstalled(serverId);
      setInstallOpen(false);
      setCatalogSelection("");
      setCatalogServerId("");
      setCatalogMountSources({});
      setCatalogEnvironment({});
      setCatalogInstallConfirmation("");
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
        app_mounts: selected.configuration.appMounts ?? [],
      },
      ...(needsBroaderConfirm ? { expected_confirmation: scopeConfirmId } : {}),
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
      <p className="text-xs text-muted-foreground">Elevation: {elevated ? `granted for ${Math.max(0, Math.floor(session.elevationRemainingS))}s` : "required to mutate MCP servers"}</p>

      <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-semibold">{t("mcpDocker.elevationTitle", { defaultValue: "Elevation" })}</h2>
        {elevated ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <p className="text-sm text-muted-foreground">{t("mcpDocker.elevationActive", { defaultValue: "This session is elevated. You can run mutations for the next 15 minutes." })}</p>
            <p className="self-center text-xs text-muted-foreground">{t("mcpDocker.passwordMemoryOnly", { defaultValue: "The password is held in page memory only and is cleared on disconnect." })}</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <form className="space-y-2" onSubmit={async (event) => {
                event.preventDefault();
                if (!elevationPassword) return;
                setBusy(true);
                setError(null);
                try {
                  await elevate(elevationPassword, session.csrfToken);
                  await session.refreshElevation();
                  setElevationPassword("");
                } catch (reason) {
                  setElevationPassword("");
                  if (reason instanceof ElevationError) {
                    setError(t("mcpDocker.elevationRejected", { defaultValue: "The instance password was rejected. Re-enter it and try again." }));
                  } else {
                    setError(t("mcpDocker.actionError", { defaultValue: "The operation could not be completed. Review the server state before retrying." }));
                  }
                } finally {
                  setBusy(false);
                }
              }}>
                <Label>{t("mcpDocker.elevationPassword", { defaultValue: "Instance password" })}<Input type="password" autoComplete="current-password" maxLength={1024} value={elevationPassword} onChange={(event) => setElevationPassword(event.target.value)} /></Label>
                <Button type="submit" disabled={!elevationPassword || busy}>{t("mcpDocker.elevateAction", { defaultValue: "Elevate session" })}</Button>
              </form>
            <p className="self-center text-xs text-muted-foreground">{t("mcpDocker.passwordMemoryOnly", { defaultValue: "The password is held in page memory only and is cleared on disconnect." })}</p>
          </div>
        )}
        <p className="text-xs text-muted-foreground">{snapshot.allowRemoteAdmin ? t("mcpDocker.remoteAdminEnabled", { defaultValue: "Remote operator administration is enabled by host configuration." }) : t("mcpDocker.remoteAdminDisabled", { defaultValue: "Remote operator administration is disabled by default; enable it only in trusted host configuration." })}</p>
      </section>

      {snapshot.pendingTransitions.length > 0 && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-3 text-sm">
        <strong>Recovery is pending; management mutations are blocked until the broker can reconcile these transitions.</strong>
        <ul className="mt-2 list-disc pl-5">{snapshot.pendingTransitions.map((transition) => <li key={transition.server_id}>{transition.server_id}{transition.action ? ` — ${transition.action}` : ""}</li>)}</ul>
      </div>}

      {installOpen && <section className="rounded-xl border p-4" aria-label="Add MCP server"><div className="flex items-center justify-between gap-2"><h2 className="font-semibold">Add MCP server</h2><Button variant="outline" onClick={() => { setInstallOpen(false); setInstallReviewed(false); setInstallConfirmId(""); }}>Cancel</Button></div>
        {!enabled && <p className="mt-3 text-sm text-muted-foreground">Enter the instance password above and load a current snapshot to install a server.</p>}
        {enabled && <section className="mt-4 space-y-3 rounded-lg border border-primary/30 bg-primary/5 p-4" aria-label="PBLabs catalog install">
          <h3 className="font-semibold">PBLabs local catalog</h3>
          <p className="text-sm text-muted-foreground">Catalog snapshots are local and hash-pinned. Installation pulls only an exact digest permitted by the separately provisioned broker policy; no catalog entry can grant host access.</p>
          {snapshot.localCatalogCandidate?.status === "ready" ? <p className="break-all font-mono text-xs">Available snapshot SHA-256: {snapshot.localCatalogCandidate.snapshotSha256} · {snapshot.localCatalogCandidate.appCount} approved app(s)</p> : <p className="text-xs text-muted-foreground">No local index is provisioned in this gateway.</p>}
          {snapshot.schemaVersion !== 2 ? <div className="space-y-2 rounded-md border p-3">
            <p className="text-sm">Schema 2 is required to pin catalogs and app profiles. Migration creates a private v1 backup and uses the current config revision.</p>
            <Label>Type MCP-Docker-v1-to-v2<Input value={schemaMigrationConfirmation} onChange={(event) => setSchemaMigrationConfirmation(event.target.value)} /></Label>
            <Button variant="outline" disabled={busy || schemaMigrationConfirmation !== "MCP-Docker-v1-to-v2"} onClick={() => void migrateCatalogConfig()}>Migrate manager config</Button>
          </div> : <>
            {snapshot.localCatalogCandidate?.status === "ready" && <div className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
              <Label>Catalog ID<Input value={catalogIdToRegister} onChange={(event) => { setCatalogIdToRegister(event.target.value); setCatalogRegisterConfirmation(""); }} placeholder="pblabs" /></Label>
              <Label>Type the catalog ID to trust this snapshot<Input value={catalogRegisterConfirmation} onChange={(event) => setCatalogRegisterConfirmation(event.target.value)} /></Label>
              <Button variant="outline" disabled={busy || !/^[a-z][a-z0-9-]{0,39}$/.test(catalogIdToRegister.trim()) || catalogRegisterConfirmation !== catalogIdToRegister.trim() || snapshot.catalogs?.some((catalog) => catalog.catalogId === catalogIdToRegister.trim())} onClick={() => void registerLocalCatalog()}>Pin local snapshot</Button>
            </div>}
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" disabled={busy} onClick={() => void exportCapabilities()}>Export capabilities.lock</Button>
              {!catalogBrokerReady && <span className="text-xs text-amber-700 dark:text-amber-300">Broker mount/acquisition policy support is unavailable; catalog installation is disabled.</span>}
            </div>
            {(snapshot.catalogs?.length ?? 0) > 0 && <div className="space-y-2 text-sm">
              <h4 className="font-medium">Trusted snapshots</h4>
              {snapshot.catalogs?.map((catalog) => <div key={catalog.catalogId} className="rounded-md border p-3">
                <p className="font-medium">{catalog.catalogId} · {catalog.status} · {catalog.apps.length} app(s)</p>
                <p className="break-all font-mono text-xs text-muted-foreground">{catalog.snapshotSha256}</p>
              </div>)}
            </div>}
            {catalogChoices.length === 0 ? <p className="text-sm text-muted-foreground">No approved app releases are present in a trusted local snapshot yet.</p> : <div className="space-y-3 rounded-md border p-3">
              <h4 className="font-medium">Install an approved app release</h4>
              <Label>Catalog app<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={catalogSelection} onChange={(event) => {
                const selectedValue = event.target.value;
                setCatalogSelection(selectedValue);
                const choice = catalogChoices.find((item) => `${item.catalogId}:${item.app.id}` === selectedValue);
                setCatalogMountSources(Object.fromEntries((choice?.app.mounts ?? []).map((mount) => [mount.target, ""])));
                setCatalogEnvironment(Object.fromEntries((choice?.app.environmentVariables ?? []).map((variable) => [variable.name, ""])));
                setCatalogNetwork(choice?.app.needsNetwork ? "bridge" : "none");
                setCatalogServerId("");
                setCatalogInstallConfirmation("");
              }}><option value="">Select a pinned app</option>{catalogChoices.map((choice) => <option key={`${choice.catalogId}:${choice.app.id}`} value={`${choice.catalogId}:${choice.app.id}`}>{choice.app.name} · {choice.app.version}</option>)}</select></Label>
              {selectedCatalogChoice && <>
                <div className="space-y-1 text-xs text-muted-foreground"><p>Registry name: <code>{selectedCatalogChoice.app.name}</code> · {selectedCatalogChoice.app.sourceClass} · {selectedCatalogChoice.app.platform}</p><p className="break-all font-mono">OCI: {selectedCatalogChoice.app.repositoryDigest}</p><p>Host access is fixed to no broad binds; declared data paths are mapped directly to their container targets.</p></div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Label>Manager server ID<Input value={catalogServerId} onChange={(event) => { setCatalogServerId(event.target.value); setCatalogInstallConfirmation(""); }} placeholder="example-server" /></Label>
                  <Label>Network access<select className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={catalogNetwork} onChange={(event) => setCatalogNetwork(event.target.value as "none" | "bridge")}><option value="none">none</option>{selectedCatalogChoice.app.needsNetwork && snapshot.supportedNetworks?.includes("bridge") && <option value="bridge">bridge</option>}</select></Label>
                </div>
                {selectedCatalogChoice.app.mounts.map((mount) => <Label key={mount.target}>Host source for {mount.target} ({mount.kind}, {mount.access}{mount.required ? ", required" : ", optional"})<Input value={catalogMountSources[mount.target] ?? ""} onChange={(event) => setCatalogMountSources((current) => ({ ...current, [mount.target]: event.target.value }))} placeholder="Absolute installation-specific path" /></Label>)}
                {selectedCatalogChoice.app.environmentVariables.map((variable) => <Label key={variable.name}>{variable.name} ({variable.secret ? "secret" : "configuration"}{variable.required ? ", required" : ", optional"})<Input type={variable.secret ? "password" : "text"} autoComplete="new-password" value={catalogEnvironment[variable.name] ?? ""} onChange={(event) => setCatalogEnvironment((current) => ({ ...current, [variable.name]: event.target.value }))} /></Label>)}
                <Label>Type {catalogInstallPhrase} to consent to acquisition and install<Input value={catalogInstallConfirmation} onChange={(event) => setCatalogInstallConfirmation(event.target.value)} /></Label>
                {(catalogRequiredMountMissing || catalogInvalidMount || catalogMissingEnvironment) && <p role="alert" className="text-sm text-destructive">Provide every required mount source and environment value using canonical absolute paths and declared variables.</p>}
                <Button disabled={!catalogInstallReady} onClick={() => void submitCatalogInstall()}>Acquire pinned digest and install</Button>
              </>}
            </div>}
            {snapshot.backups.filter((backup) => backup.action === "migrate-schema").map((backup) => <div key={backup.backupId} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
              <p className="text-xs">Schema v1 backup {backup.backupId}; rollback is permitted only if manager app/server state is unchanged.</p>
              <Label>Type restore:{backup.backupId}<Input value={schemaRestoreConfirmations[backup.backupId] ?? ""} onChange={(event) => setSchemaRestoreConfirmations((current) => ({ ...current, [backup.backupId]: event.target.value }))} /></Label>
              <Button variant="outline" disabled={busy || schemaRestoreConfirmations[backup.backupId] !== `restore:${backup.backupId}`} onClick={() => void restoreSchema(backup.backupId)}>Restore schema 1</Button>
            </div>)}
          </>}
        </section>}
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
          {snapshot.backups.some((backup) => backup.action !== "migrate-schema") && <details className="rounded-xl border p-4"><summary className="cursor-pointer font-semibold">Restore an excluded server ({snapshot.backups.filter((backup) => backup.action !== "migrate-schema" && !snapshot.servers[backup.serverId]).length} eligible)</summary><section className="mt-4 space-y-3">
            <h2 className="font-semibold">Restore an excluded server</h2>
            <p className="text-sm text-muted-foreground">Restore checks the backup checksum, refuses to overwrite an existing server, and reconciles Docker before committing config.</p>
            {snapshot.backups.filter((backup) => backup.action !== "migrate-schema").map((backup) => <div key={backup.backupId} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
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
              <Button variant="outline" disabled={selected.state === "stopped-persistent" || Boolean(selectedAppRelease)} title={selectedAppRelease ? "Catalog-managed image identity is immutable; exclude and reinstall from a newer trusted catalog release." : selected.state === "stopped-persistent" ? "Start the persistent server before updating its image" : undefined} onClick={() => setUpdateOpen(true)}>Update image</Button>
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

            <div className="space-y-4 rounded-lg border border-destructive/40 bg-destructive/[0.04] p-4">
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-destructive">{t("mcpDocker.excludeServer", { defaultValue: "Exclude server" })}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{t("mcpDocker.excludeWarning", { defaultValue: "A backup will be created, tools revoked, and only the managed container and registry entry removed. The image and volumes will remain on disk." })}</p>
              </div>
              <div className="space-y-2"><Label>{t("mcpDocker.typeToExclude", { defaultValue: "Type {{server}} to confirm", server: selectedId })}</Label><Input autoComplete="off" spellCheck={false} value={excludeConfirmId} onChange={(event) => setExcludeConfirmId(event.target.value)} /></div>
              <Button className="w-full sm:w-auto" variant="destructive" disabled={busy || excludeConfirmId !== selectedId} onClick={() => void serverAction("exclude", { expected_confirmation: selectedId }, { success: t("mcpDocker.excludeComplete", { defaultValue: "Server backed up and excluded; the image and volumes remain on disk." }) })}>{t("mcpDocker.exclude", { defaultValue: "Back up and exclude" })}</Button>
            </div>
          </section>}
        </>
      )}
    </section>
  );
}
