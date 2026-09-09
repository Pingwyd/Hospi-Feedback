const ACCESS_TOKEN_KEY = "hospi_admin_access_token";
const REFRESH_TOKEN_KEY = "hospi_admin_refresh_token";
const EXPIRES_AT_KEY = "hospi_admin_expires_at";

export type AdminSessionTokens = {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
};

export function saveAdminSession(tokens: AdminSessionTokens): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  sessionStorage.setItem(EXPIRES_AT_KEY, tokens.expiresAt);
}

export function clearAdminSession(): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(EXPIRES_AT_KEY);
}

export function getAdminAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  if (!token) {
    return null;
  }
  const expiresAt = sessionStorage.getItem(EXPIRES_AT_KEY);
  if (expiresAt) {
    const expiry = Date.parse(expiresAt);
    if (!Number.isNaN(expiry) && Date.now() >= expiry) {
      clearAdminSession();
      return null;
    }
  }
  return token;
}

export function adminWebSocketUrl(accessToken: string): string {
  const base =
    process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "") ?? "ws://127.0.0.1:8000";
  return `${base}/api/admin/ws?access_token=${encodeURIComponent(accessToken)}`;
}
