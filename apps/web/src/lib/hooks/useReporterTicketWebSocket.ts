"use client";

import { useEffect, useRef, useState } from "react";

import { fetchWsBootstrap } from "@/lib/api/access";
import {
  REPORTER_WS_FALLBACK_POLL_MS,
  REPORTER_WS_RECONNECT_DELAYS_MS,
  reporterTicketWebSocketUrl,
} from "@/lib/auth/reporter-websocket";

export type ReporterWsEvent = {
  event: "new_message" | "session_expired";
  payload: Record<string, unknown>;
};

export type ReporterWsConnectionState =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "polling"
  | "disconnected";

type UseReporterTicketWebSocketOptions = {
  ticketCode: string;
  enabled: boolean;
  onEvent: (event: ReporterWsEvent) => void;
  onFallbackPoll?: () => void;
};

const AUTH_CLOSE_CODES = new Set([4401, 4404]);

function reconnectDelayMs(attemptIndex: number): number {
  const capped = Math.min(attemptIndex, REPORTER_WS_RECONNECT_DELAYS_MS.length - 1);
  return REPORTER_WS_RECONNECT_DELAYS_MS[capped];
}

export function useReporterTicketWebSocket({
  ticketCode,
  enabled,
  onEvent,
  onFallbackPoll,
}: UseReporterTicketWebSocketOptions): {
  connectionState: ReporterWsConnectionState;
} {
  const [connectionState, setConnectionState] =
    useState<ReporterWsConnectionState>("disconnected");
  const onEventRef = useRef(onEvent);
  const onFallbackPollRef = useRef(onFallbackPoll);
  onEventRef.current = onEvent;
  onFallbackPollRef.current = onFallbackPoll;

  useEffect(() => {
    if (!enabled) {
      setConnectionState("disconnected");
      return;
    }

    let active = true;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let reconnectAttempt = 0;

    function clearReconnectTimer() {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    }

    function clearPollTimer() {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    }

    function closeSocket() {
      if (!socket) {
        return;
      }
      const currentSocket = socket;
      socket = null;
      currentSocket.onmessage = null;
      currentSocket.onerror = null;
      currentSocket.onclose = null;
      if (currentSocket.readyState === WebSocket.CONNECTING) {
        currentSocket.onopen = () => {
          currentSocket.close();
        };
      } else if (currentSocket.readyState === WebSocket.OPEN) {
        currentSocket.close();
      }
    }

    function startPollingFallback() {
      if (!active || pollTimer) {
        return;
      }
      setConnectionState("polling");
      onFallbackPollRef.current?.();
      pollTimer = setInterval(() => {
        onFallbackPollRef.current?.();
      }, REPORTER_WS_FALLBACK_POLL_MS);
    }

    function scheduleReconnect() {
      if (!active) {
        return;
      }
      if (reconnectAttempt >= REPORTER_WS_RECONNECT_DELAYS_MS.length) {
        startPollingFallback();
        return;
      }
      setConnectionState("reconnecting");
      const delayMs = reconnectDelayMs(reconnectAttempt);
      reconnectAttempt += 1;
      clearReconnectTimer();
      reconnectTimer = setTimeout(() => {
        void connect();
      }, delayMs);
    }

    async function connect() {
      if (!active) {
        return;
      }
      clearReconnectTimer();
      closeSocket();
      setConnectionState(reconnectAttempt === 0 ? "connecting" : "reconnecting");

      let accessToken: string;
      try {
        const bootstrap = await fetchWsBootstrap();
        accessToken = bootstrap.access_token;
      } catch {
        if (!active) {
          return;
        }
        scheduleReconnect();
        return;
      }

      if (!active) {
        return;
      }

      socket = new WebSocket(reporterTicketWebSocketUrl(ticketCode, accessToken));

      socket.onopen = () => {
        if (!active) {
          return;
        }
        reconnectAttempt = 0;
        clearPollTimer();
        setConnectionState("connected");
      };

      socket.onmessage = (messageEvent) => {
        try {
          const parsed = JSON.parse(messageEvent.data) as ReporterWsEvent;
          if (!parsed.event) {
            return;
          }
          if (parsed.event === "session_expired") {
            onEventRef.current({ event: "session_expired", payload: {} });
            active = false;
            clearReconnectTimer();
            clearPollTimer();
            closeSocket();
            setConnectionState("disconnected");
            return;
          }
          if (parsed.payload) {
            onEventRef.current(parsed);
          }
        } catch {
          // Ignore malformed websocket payloads.
        }
      };

      socket.onclose = (closeEvent) => {
        if (!active) {
          return;
        }
        socket = null;
        if (AUTH_CLOSE_CODES.has(closeEvent.code)) {
          active = false;
          clearReconnectTimer();
          clearPollTimer();
          setConnectionState("disconnected");
          onEventRef.current({ event: "session_expired", payload: {} });
          return;
        }
        scheduleReconnect();
      };

      socket.onerror = () => {
        // onclose handles reconnect/backoff.
      };
    }

    void connect();

    return () => {
      active = false;
      clearReconnectTimer();
      clearPollTimer();
      closeSocket();
      setConnectionState("disconnected");
    };
  }, [enabled, ticketCode]);

  return { connectionState };
}
