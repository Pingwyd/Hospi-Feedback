import { apiFetch } from "@/lib/api/client";

export type AccessVerifyResponse = {
  expires_at: string;
  session_token: string | null;
};

export async function verifyAccessCode(accessCode: string): Promise<AccessVerifyResponse> {
  return apiFetch<AccessVerifyResponse>("/api/access/verify", {
    method: "POST",
    body: JSON.stringify({ access_code: accessCode }),
  });
}

export async function checkAccessSession(): Promise<boolean> {
  try {
    await apiFetch<{ ok: boolean }>("/api/_phase2/public-ping");
    return true;
  } catch {
    return false;
  }
}
