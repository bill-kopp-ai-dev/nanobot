import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  type ReactNode,
} from "react";

import type { NanobotClient } from "@/lib/nanobot-client";
import type { WebUIIngressLimits } from "@/lib/types";

export interface ClientSession {
  sessionId: string;
  csrfToken: string;
  elevated: boolean;
  elevationRemainingS: number;
  elevationTtlS: number;
  signIn(password: string): Promise<void>;
  signOut(): Promise<void>;
  elevate(password: string): Promise<void>;
  refreshElevation(): Promise<void>;
}

interface ClientContextValue {
  client: NanobotClient;
  token: string;
  getToken: () => string;
  modelName: string | null;
  ingressLimits: WebUIIngressLimits | null;
  webuiCapabilities: string[];
  session: ClientSession;
}

const ClientContext = createContext<ClientContextValue | null>(null);

export function ClientProvider({
  client,
  token,
  modelName = null,
  ingressLimits = null,
  webuiCapabilities = [],
  session,
  children,
}: {
  client: NanobotClient;
  token: string;
  modelName?: string | null;
  ingressLimits?: WebUIIngressLimits | null;
  webuiCapabilities?: string[];
  session: ClientSession;
  children: ReactNode;
}) {
  const tokenRef = useRef(token);
  tokenRef.current = token;
  const getToken = useCallback(() => tokenRef.current, []);
  const value = useMemo(
    () => ({ client, token, getToken, modelName, ingressLimits, webuiCapabilities, session }),
    [client, getToken, ingressLimits, modelName, session, token, webuiCapabilities],
  );

  return (
    <ClientContext.Provider value={value}>
      {children}
    </ClientContext.Provider>
  );
}

export function useClient(): ClientContextValue {
  const ctx = useContext(ClientContext);
  if (!ctx) {
    throw new Error("useClient must be used within a ClientProvider");
  }
  return ctx;
}
