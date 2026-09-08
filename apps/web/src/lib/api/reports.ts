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

export type Message = {
  id: string;
  sender_type: "reporter" | "admin";
  content: string;
  created_at: string;
};

export type TicketStatusResponse = {
  status: string;
  report_type: string;
  description: string;
  reported_member_name: string | null;
  severity: string | null;
  created_at: string;
  updated_at: string;
  messages: Message[];
};

export type AttachmentResponse = {
  id: string;
  file_type: string;
  uploaded_at: string;
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
): Promise<AttachmentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<AttachmentResponse>(
    `/api/reports/ticket/${encodeURIComponent(ticketCode)}/attachments`,
    {
      method: "POST",
      body: formData,
    },
  );
}
