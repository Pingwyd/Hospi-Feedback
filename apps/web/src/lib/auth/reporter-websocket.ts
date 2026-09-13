export function reporterTicketWebSocketUrl(
  ticketCode: string,
  accessToken: string,
): string {
  const base =
    process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "") ?? "ws://127.0.0.1:8000";
  return `${base}/api/reports/ticket/${encodeURIComponent(ticketCode)}/ws?access_token=${encodeURIComponent(accessToken)}`;
}

/** Backoff delays after a dropped connection (cap 30s). */
export const REPORTER_WS_RECONNECT_DELAYS_MS = [
  1_000,
  2_000,
  4_000,
  8_000,
  16_000,
  30_000,
  30_000,
  30_000,
  30_000,
  30_000,
  30_000,
  30_000,
] as const;

export const REPORTER_WS_FALLBACK_POLL_MS = 30_000;
