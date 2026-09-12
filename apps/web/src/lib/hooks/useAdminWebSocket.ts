"use client";

import { useEffect, useRef } from "react";

import {
  adminWebSocketUrl,
  getAdminAccessToken,
} from "@/lib/auth/admin-session";

export type AdminWsEvent = {
  event: "new_report" | "new_message";
  payload: Record<string, unknown>;
};

type UseAdminWebSocketOptions = {
  enabled: boolean;
  onEvent: (event: AdminWsEvent) => void;
};

export function useAdminWebSocket({
  enabled,
  onEvent,
}: UseAdminWebSocketOptions): void {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!enabled) {
      return;
    }
    const token = getAdminAccessToken();
    if (!token) {
      return;
    }
    const accessToken = token;

    let active = true;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (!active) {
        return;
      }
      socket = new WebSocket(adminWebSocketUrl(accessToken));
      socket.onmessage = (messageEvent) => {
        try {
          const parsed = JSON.parse(messageEvent.data) as AdminWsEvent;
          if (parsed.event && parsed.payload) {
            onEventRef.current(parsed);
          }
        } catch {
          // Ignore malformed websocket payloads.
        }
      };
      socket.onclose = () => {
        if (!active) {
          return;
        }
        reconnectTimer = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      active = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (!socket) {
        return;
      }
      const currentSocket = socket;
      socket = null;
      currentSocket.onmessage = null;
      currentSocket.onerror = null;
      currentSocket.onclose = null;
      if (currentSocket.readyState === WebSocket.CONNECTING) {
        // Avoid closing while CONNECTING: React Strict Mode unmounts before
        // the handshake finishes and the browser logs a noisy warning.
        currentSocket.onopen = () => {
          currentSocket.close();
        };
      } else if (currentSocket.readyState === WebSocket.OPEN) {
        currentSocket.close();
      }
    };
  }, [enabled]);
}
