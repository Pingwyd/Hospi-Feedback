import { getAdminAccessToken } from "@/lib/auth/admin-session";

import { ApiError, type ApiErrorBody, apiFetch } from "./client";

export { ApiError };

export async function adminFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = getAdminAccessToken();
  if (!token) {
    throw new ApiError(401, "unauthorized", "Admin session required.");
  }
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return apiFetch<T>(path, { ...init, headers });
}

export type AdminProfile = {
  id: string;
  full_name: string;
  role: string | null;
  subunit: string | null;
  permissions: string[];
};

export type AdminTeamMember = {
  id: string;
  full_name: string;
  role: string | null;
};

export async function fetchAdminProfile(): Promise<AdminProfile> {
  const payload = await adminFetch<{ data: AdminProfile }>("/api/admin/me");
  return payload.data;
}

export async function fetchAdminTeam(): Promise<AdminTeamMember[]> {
  const payload = await adminFetch<{ data: AdminTeamMember[] }>("/api/admin/team");
  return payload.data;
}

export function isRecusalBlocked(error: unknown): boolean {
  return error instanceof ApiError && error.code === "recusal_blocked";
}

export function isRecusalConfirmationRequired(error: unknown): boolean {
  return error instanceof ApiError && error.code === "recusal_confirmation_required";
}

export type ApiErrorBodyExport = ApiErrorBody;
