import { adminFetch } from "./admin-fetch";

export type DashboardStats = {
  status_counts: Record<string, number>;
  report_type_counts: Record<string, number>;
  submissions_by_day: { date: string; count: number }[];
  oldest_unresolved: {
    report_id: string;
    status: string;
    created_at: string;
  } | null;
};

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const payload = await adminFetch<{ data: DashboardStats }>(
    "/api/admin/dashboard/stats",
  );
  return payload.data;
}

export type AuditLogEntry = {
  id: string;
  admin_id: string;
  report_id: string | null;
  action: string;
  detail: Record<string, unknown> | null;
  created_at: string;
};

export async function fetchAuditLog(limit = 100): Promise<AuditLogEntry[]> {
  const payload = await adminFetch<{ data: AuditLogEntry[] }>(
    `/api/admin/audit-log?limit=${limit}`,
  );
  return payload.data;
}

export type EscalationContact = {
  id: string;
  name: string;
  role_label: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  active?: boolean;
};

export async function fetchEscalationContacts(): Promise<EscalationContact[]> {
  const payload = await adminFetch<{ data: EscalationContact[] }>(
    "/api/admin/escalation-contacts",
  );
  return payload.data;
}
