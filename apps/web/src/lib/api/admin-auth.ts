import { saveAdminSession } from "@/lib/auth/admin-session";

import { apiFetch } from "./client";

export type AdminLoginPayload = {
  email: string;
  password: string;
  totp_code?: string;
};

export type AdminLoginResponse = {
  access_token: string;
  refresh_token: string;
  expires_at: string;
};

export async function loginAdmin(payload: AdminLoginPayload): Promise<void> {
  const result = await apiFetch<AdminLoginResponse>("/api/admin/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  saveAdminSession({
    accessToken: result.access_token,
    refreshToken: result.refresh_token,
    expiresAt: result.expires_at,
  });
}
