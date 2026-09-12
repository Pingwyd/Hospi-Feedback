import { getAdminAccessToken } from "@/lib/auth/admin-session";

import { ApiError, type ApiErrorBody } from "./client";

export type AdminExportFormat = "pdf" | "docx";

export type AdminExportFilters = {
  status?: string;
  keyword?: string;
  created_from?: string;
  created_to?: string;
};

export function buildAdminExportSearchParams(
  filters: AdminExportFilters,
  format: AdminExportFormat = "pdf",
): URLSearchParams {
  const params = new URLSearchParams();
  params.set("format", format);
  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.keyword) {
    params.set("keyword", filters.keyword);
  }
  if (filters.created_from) {
    params.set("created_from", filters.created_from);
  }
  if (filters.created_to) {
    params.set("created_to", filters.created_to);
  }
  return params;
}

function parseFilenameFromContentDisposition(header: string | null): string | null {
  if (!header) {
    return null;
  }
  const match = /filename="([^"]+)"/i.exec(header);
  return match?.[1] ?? null;
}

export async function downloadAdminReportExport(
  filters: AdminExportFilters,
  format: AdminExportFormat = "pdf",
): Promise<string> {
  const token = getAdminAccessToken();
  if (!token) {
    throw new ApiError(401, "unauthorized", "Admin session required.");
  }

  const params = buildAdminExportSearchParams(filters, format);
  const response = await fetch(`/api/admin/export?${params.toString()}`, {
    method: "GET",
    credentials: "include",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    let code = "unknown";
    let message = "Export failed.";
    try {
      const payload = (await response.json()) as ApiErrorBody;
      code = payload.error?.code ?? code;
      message = payload.error?.message ?? message;
    } catch {
      // Non-JSON error body
    }
    throw new ApiError(response.status, code, message);
  }

  const blob = await response.blob();
  const filename =
    parseFilenameFromContentDisposition(response.headers.get("Content-Disposition")) ??
    `hospi-export.${format}`;

  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }

  return filename;
}
