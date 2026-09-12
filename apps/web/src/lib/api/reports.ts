import { apiFetch } from "@/lib/api/client";

export type ReportType = "complaint" | "suggestion" | "recognition";
export type Severity = "low" | "medium" | "high";

export type CreateReportPayload = {
  report_type: ReportType;
  description: string;
  reported_member_name?: string;
  severity?: Severity;
  source?: "web";
};

export type CreateReportResponse = {
  ticket_code: string;
  status: string;
  created_at: string;
};

export type AttachmentSummary = {
  id: string;
  file_type: string;
  uploaded_at: string;
  preview_url: string;
};

export type Message = {
  id: string;
  sender_type: "reporter" | "admin";
  content: string;
  created_at: string;
  attachment?: AttachmentSummary | null;
};

export type TicketStatusResponse = {
  status: string;
  report_type: string;
  description: string;
  reported_member_name: string | null;
  severity: string | null;
  created_at: string;
  updated_at: string;
  report_attachments: AttachmentSummary[];
  messages: Message[];
};

export type AttachmentResponse = {
  id: string;
  file_type: string;
  uploaded_at: string;
  message_id?: string | null;
  preview_url?: string | null;
};

export async function createReport(
  payload: CreateReportPayload,
): Promise<CreateReportResponse> {
  return apiFetch<CreateReportResponse>("/api/reports", {
    method: "POST",
    body: JSON.stringify({ ...payload, source: "web" }),
  });
}

export async function fetchTicketStatus(ticketCode: string): Promise<TicketStatusResponse> {
  return apiFetch<TicketStatusResponse>(`/api/reports/ticket/${encodeURIComponent(ticketCode)}`);
}

export async function postReporterMessage(
  ticketCode: string,
  content: string,
): Promise<Message> {
  return apiFetch<Message>(`/api/reports/ticket/${encodeURIComponent(ticketCode)}/message`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function uploadAttachment(
  ticketCode: string,
  file: File,
  options: { linkToThread?: boolean } = {},
): Promise<AttachmentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const query = options.linkToThread ? "?link_to_thread=true" : "";
  return apiFetch<AttachmentResponse>(
    `/api/reports/ticket/${encodeURIComponent(ticketCode)}/attachments${query}`,
    {
      method: "POST",
      body: formData,
    },
  );
}
