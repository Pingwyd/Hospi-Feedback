import { adminFetch } from "./admin-fetch";

export type ReportStatus =
  | "new"
  | "under_review"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "escalated"
  | "closed"
  | "marked_false";

export type ReportSummary = {
  id: string;
  source?: string | null;
  report_type?: string | null;
  reported_member_name?: string | null;
  severity?: string | null;
  status?: string | null;
  assigned_admin_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ReportMessage = {
  id: string;
  sender_type: "reporter" | "admin";
  content: string;
  created_at: string;
};

export type InternalNote = {
  id: string;
  content: string;
  created_at: string;
  admin_id?: string | null;
};

export type ReportDetail = {
  report: Record<string, unknown>;
  messages: ReportMessage[];
  internal_notes: InternalNote[];
};

export type ReportListFilters = {
  status?: string;
  keyword?: string;
  created_from?: string;
  created_to?: string;
  limit?: number;
  offset?: number;
};

export async function listAdminReports(
  filters: ReportListFilters = {},
): Promise<ReportSummary[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.keyword) params.set("keyword", filters.keyword);
  if (filters.created_from) params.set("created_from", filters.created_from);
  if (filters.created_to) params.set("created_to", filters.created_to);
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.offset) params.set("offset", String(filters.offset));
  const query = params.toString();
  const payload = await adminFetch<{ data: ReportSummary[] }>(
    `/api/admin/reports${query ? `?${query}` : ""}`,
  );
  return payload.data;
}

export async function getAdminReport(reportId: string): Promise<ReportDetail> {
  return adminFetch<ReportDetail>(`/api/admin/reports/${reportId}`);
}

export async function updateReportStatus(
  reportId: string,
  status: ReportStatus,
  confirmRecusalOverride = false,
): Promise<Record<string, unknown>> {
  const payload = await adminFetch<{ data: Record<string, unknown> }>(
    `/api/admin/reports/${reportId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
        confirm_recusal_override: confirmRecusalOverride,
      }),
    },
  );
  return payload.data;
}

export async function assignReport(
  reportId: string,
  assignedAdminId: string,
): Promise<Record<string, unknown>> {
  const payload = await adminFetch<{ data: Record<string, unknown> }>(
    `/api/admin/reports/${reportId}/assign`,
    {
      method: "PATCH",
      body: JSON.stringify({ assigned_admin_id: assignedAdminId }),
    },
  );
  return payload.data;
}

export async function linkReportMember(
  reportId: string,
  reportedMemberAdminId: string,
): Promise<Record<string, unknown>> {
  const payload = await adminFetch<{ data: Record<string, unknown> }>(
    `/api/admin/reports/${reportId}/link-member`,
    {
      method: "PATCH",
      body: JSON.stringify({
        reported_member_admin_id: reportedMemberAdminId,
      }),
    },
  );
  return payload.data;
}

export async function addInternalNote(
  reportId: string,
  content: string,
): Promise<InternalNote> {
  const payload = await adminFetch<{ data: InternalNote }>(
    `/api/admin/reports/${reportId}/notes`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    },
  );
  return payload.data;
}

export async function sendAdminMessage(
  reportId: string,
  content: string,
): Promise<ReportMessage> {
  const payload = await adminFetch<{ data: ReportMessage }>(
    `/api/admin/reports/${reportId}/message`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    },
  );
  return payload.data;
}

export async function escalateReport(
  reportId: string,
  escalationContactId: string,
): Promise<Record<string, unknown>> {
  const payload = await adminFetch<{ data: Record<string, unknown> }>(
    `/api/admin/reports/${reportId}/escalate`,
    {
      method: "POST",
      body: JSON.stringify({ escalation_contact_id: escalationContactId }),
    },
  );
  return payload.data;
}

export async function markReportFalse(
  reportId: string,
  confirmRecusalOverride = false,
): Promise<Record<string, unknown>> {
  const payload = await adminFetch<{ data: Record<string, unknown> }>(
    `/api/admin/reports/${reportId}/mark-false`,
    {
      method: "POST",
      body: JSON.stringify({
        confirm_recusal_override: confirmRecusalOverride,
      }),
    },
  );
  return payload.data;
}

export async function deleteReport(
  reportId: string,
  deleteReason: string,
): Promise<void> {
  await adminFetch<void>(`/api/admin/reports/${reportId}`, {
    method: "DELETE",
    body: JSON.stringify({ delete_reason: deleteReason }),
  });
}
