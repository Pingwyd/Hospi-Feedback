"use client";

import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Check, Send, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { RecusalConfirmModal } from "@/components/admin/RecusalConfirmModal";
import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import {
  ApiError,
  fetchAdminTeam,
  isRecusalBlocked,
  isRecusalConfirmationRequired,
  type AdminTeamMember,
} from "@/lib/api/admin-fetch";
import { fetchEscalationContacts } from "@/lib/api/admin-dashboard";
import {
  addInternalNote,
  assignReport,
  deleteReport,
  escalateReport,
  getAdminReport,
  linkReportMember,
  markReportFalse,
  sendAdminMessage,
  updateReportStatus,
  type ReportDetail,
  type ReportStatus,
} from "@/lib/api/admin-reports";
import { useAdminWebSocket } from "@/lib/hooks/useAdminWebSocket";
import { invalidateAdminReportLists } from "@/lib/query/admin-report-queries";
import { AttachmentPreview } from "@/components/shared/AttachmentPreview";

const PHOTO_PLACEHOLDER = "Photo attached";

type ReportDetailPanelProps = {
  reportId: string;
};

type PendingRecusalAction =
  | { type: "status"; status: ReportStatus }
  | { type: "mark_false" };

const STATUS_OPTIONS: { value: ReportStatus; permission: string }[] = [
  { value: "under_review", permission: "respond" },
  { value: "in_progress", permission: "respond" },
  { value: "assigned", permission: "assign" },
  { value: "escalated", permission: "respond" },
  { value: "resolved", permission: "close" },
  { value: "closed", permission: "close" },
];

/** Spec §4 authoritative status vocabulary, in triage-friendly order. */
const ALL_REPORT_STATUSES: ReportStatus[] = [
  "new",
  "under_review",
  "assigned",
  "in_progress",
  "escalated",
  "resolved",
  "closed",
  "marked_false",
];

function formatStatusLabel(status: ReportStatus): string {
  return status.replace(/_/g, " ");
}

function statusControlButtonClass(isCurrent: boolean): string {
  if (isCurrent) {
    return "rounded-full border border-sage/50 bg-sage/15 px-3 py-1.5 text-xs font-semibold capitalize text-sage ring-2 ring-sage/25";
  }
  return "rounded-full border border-ink/10 bg-paper px-3 py-1.5 text-xs font-medium capitalize text-ink hover:bg-white disabled:cursor-not-allowed disabled:opacity-60";
}

function statusButtonAriaLabel(
  status: ReportStatus,
  options: { isCurrent: boolean; isActionable: boolean },
): string {
  const label = formatStatusLabel(status);
  if (options.isCurrent) {
    return `${label}, current status`;
  }
  if (options.isActionable) {
    return `Change status to ${label}`;
  }
  return `${label}, not available`;
}

export function ReportDetailPanel({ reportId }: ReportDetailPanelProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { profile, hasPermission, hasRole } = useAdminSession();
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [team, setTeam] = useState<AdminTeamMember[]>([]);
  const [contacts, setContacts] = useState<
    { id: string; name: string; role_label: string }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [messageText, setMessageText] = useState("");
  const [assignAdminId, setAssignAdminId] = useState("");
  const [linkAdminId, setLinkAdminId] = useState("");
  const [escalationContactId, setEscalationContactId] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [recusalOpen, setRecusalOpen] = useState(false);
  const [recusalMessage, setRecusalMessage] = useState("");
  const [pendingRecusal, setPendingRecusal] = useState<PendingRecusalAction | null>(
    null,
  );
  const [busy, setBusy] = useState(false);

  const refreshInboxLists = useCallback(async () => {
    await invalidateAdminReportLists(queryClient);
  }, [queryClient]);

  const loadDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reportDetail, teamMembers, escalationContacts] = await Promise.all([
        getAdminReport(reportId),
        fetchAdminTeam(),
        fetchEscalationContacts(),
      ]);
      setDetail(reportDetail);
      setTeam(teamMembers);
      setContacts(
        escalationContacts.filter((contact) => contact.active !== false),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load report.");
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  useAdminWebSocket({
    enabled: true,
    onEvent: (event) => {
      if (
        event.event === "new_message" &&
        event.payload.report_id === reportId
      ) {
        void loadDetail();
      }
    },
  });

  const report = detail?.report ?? null;
  const allowedStatuses = useMemo(
    () =>
      STATUS_OPTIONS.filter((option) => hasPermission(option.permission)).map(
        (option) => option.value,
      ),
    [hasPermission],
  );

  const currentStatus = (report?.status ?? "new") as ReportStatus;
  const canChangeStatus = allowedStatuses.length > 0;

  async function runRecusalSensitiveAction(
    action: PendingRecusalAction,
    confirmOverride = false,
  ) {
    setBusy(true);
    setActionError(null);
    try {
      if (action.type === "status") {
        await updateReportStatus(reportId, action.status, confirmOverride);
      } else {
        await markReportFalse(reportId, confirmOverride);
      }
      setRecusalOpen(false);
      setPendingRecusal(null);
      await refreshInboxLists();
      await loadDetail();
    } catch (err) {
      if (isRecusalConfirmationRequired(err)) {
        setPendingRecusal(action);
        setRecusalMessage(err instanceof ApiError ? err.message : "Recusal warning.");
        setRecusalOpen(true);
        return;
      }
      if (isRecusalBlocked(err)) {
        setActionError(err instanceof ApiError ? err.message : "Recusal blocked.");
        return;
      }
      setActionError(err instanceof ApiError ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleStatusChange(status: ReportStatus) {
    await runRecusalSensitiveAction({ type: "status", status });
  }

  async function handleMarkFalse() {
    await runRecusalSensitiveAction({ type: "mark_false" });
  }

  async function handleAssign() {
    if (!assignAdminId) {
      setActionError("Select an admin to assign.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await assignReport(reportId, assignAdminId);
      await refreshInboxLists();
      await loadDetail();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Assign failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLinkMember() {
    if (!linkAdminId) {
      setActionError("Select a member to link.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await linkReportMember(reportId, linkAdminId);
      await refreshInboxLists();
      await loadDetail();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Link failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddNote() {
    if (!noteText.trim()) {
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await addInternalNote(reportId, noteText.trim());
      setNoteText("");
      await loadDetail();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not add note.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSendMessage() {
    if (!messageText.trim()) {
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await sendAdminMessage(reportId, messageText.trim());
      setMessageText("");
      await loadDetail();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not send message.");
    } finally {
      setBusy(false);
    }
  }

  async function handleEscalate() {
    if (!escalationContactId) {
      setActionError("Select an escalation contact.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await escalateReport(reportId, escalationContactId);
      await refreshInboxLists();
      await loadDetail();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Escalation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!deleteReason.trim()) {
      setActionError("Delete reason is required.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await deleteReport(reportId, deleteReason.trim());
      await refreshInboxLists();
      router.push("/admin/reports");
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <SkeletonCard />;
  }

  if (error || !report) {
    return (
      <div
        role="alert"
        className="rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
      >
        {error ?? "Report not found."}
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div>
          <p className="text-sm text-ink/60">Report detail</p>
          <h1 className="text-2xl font-semibold capitalize text-ink">
            {(String(report.report_type) || "Report").replace(/_/g, " ")}
          </h1>
          <p className="mt-2 text-sm text-ink/70">
            Status:{" "}
            <span className="font-medium capitalize text-ink">
              {String(report.status ?? "unknown").replace(/_/g, " ")}
            </span>
          </p>
        </div>

        {actionError ? (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
          >
            <AlertCircle className="mt-0.5 shrink-0 text-brass" size={18} />
            <span>{actionError}</span>
          </div>
        ) : null}

        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
            Case summary
          </h2>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-ink/50">Description</dt>
              <dd className="mt-1 whitespace-pre-wrap text-ink">
                {String(report.description ?? "N/A")}
              </dd>
            </div>
            <div>
              <dt className="text-ink/50">Reported member</dt>
              <dd className="mt-1 text-ink">
                {String(report.reported_member_name ?? "Not named")}
              </dd>
            </div>
            <div>
              <dt className="text-ink/50">Severity</dt>
              <dd className="mt-1 capitalize text-ink">
                {String(report.severity ?? "N/A")}
              </dd>
            </div>
            <div>
              <dt className="text-ink/50">Source</dt>
              <dd className="mt-1 capitalize text-ink">
                {String(report.source ?? "N/A")}
              </dd>
            </div>
          </dl>
        </section>

        <div className="grid gap-6 xl:grid-cols-2">
          <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
              Status
            </h2>
            <div
              role="group"
              aria-label="Report status"
              className="mt-4 flex flex-wrap gap-2"
            >
              {ALL_REPORT_STATUSES.map((status) => {
                const isCurrent = status === currentStatus;
                const isActionable =
                  canChangeStatus && allowedStatuses.includes(status) && !isCurrent;
                return (
                  <button
                    key={status}
                    type="button"
                    aria-current={isCurrent ? true : undefined}
                    aria-label={statusButtonAriaLabel(status, {
                      isCurrent,
                      isActionable,
                    })}
                    disabled={busy || isCurrent || !isActionable}
                    onClick={() => void handleStatusChange(status)}
                    className={`inline-flex items-center gap-1.5 ${statusControlButtonClass(isCurrent)}`}
                  >
                    {isCurrent ? <Check size={14} aria-hidden="true" /> : null}
                    <span aria-hidden="true">{formatStatusLabel(status)}</span>
                  </button>
                );
              })}
            </div>
            {!canChangeStatus ? (
              <p className="mt-3 text-sm text-ink/60">
                You do not have permission to change report status.
              </p>
            ) : null}
            {hasPermission("close") ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleMarkFalse()}
                className="mt-4 rounded-lg border border-brass/30 px-3 py-2 text-sm font-medium text-brass hover:bg-brass/10 disabled:opacity-60"
              >
                Mark as false report
              </button>
            ) : null}
          </section>

          <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
              Assignment
            </h2>
            {hasPermission("assign") ? (
              <div className="mt-4 space-y-3">
                <select
                  value={assignAdminId}
                  onChange={(event) => setAssignAdminId(event.target.value)}
                  className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
                >
                  <option value="">Select admin</option>
                  {team.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.full_name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void handleAssign()}
                  className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-60"
                >
                  Assign report
                </button>
                {profile ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      void (async () => {
                        setBusy(true);
                        setActionError(null);
                        try {
                          await assignReport(reportId, profile.id);
                          await refreshInboxLists();
                          await loadDetail();
                        } catch (err) {
                          setActionError(
                            err instanceof ApiError ? err.message : "Assign failed.",
                          );
                        } finally {
                          setBusy(false);
                        }
                      })();
                    }}
                    className="ml-2 rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-white/70 disabled:opacity-60"
                  >
                    Assign to me
                  </button>
                ) : null}
              </div>
            ) : (
              <p className="mt-3 text-sm text-ink/60">
                You do not have permission to assign reports.
              </p>
            )}
          </section>

          <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
              Link member
            </h2>
            {hasPermission("respond") ? (
              <div className="mt-4 space-y-3">
                <select
                  value={linkAdminId}
                  onChange={(event) => setLinkAdminId(event.target.value)}
                  className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
                >
                  <option value="">Select admin member</option>
                  {team.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.full_name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void handleLinkMember()}
                  className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-60"
                >
                  Confirm member link
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-ink/60">
                You do not have permission to link members.
              </p>
            )}
          </section>

          <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
              Escalation
            </h2>
            {hasPermission("respond") ? (
              <div className="mt-4 space-y-3">
                <select
                  value={escalationContactId}
                  onChange={(event) => setEscalationContactId(event.target.value)}
                  className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
                >
                  <option value="">Select escalation contact</option>
                  {contacts.map((contact) => (
                    <option key={contact.id} value={contact.id}>
                      {contact.name} ({contact.role_label})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void handleEscalate()}
                  className="rounded-lg bg-brass px-4 py-2 text-sm font-semibold text-paper hover:bg-brass/90 disabled:opacity-60"
                >
                  Escalate report
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-ink/60">
                You do not have permission to escalate reports.
              </p>
            )}
          </section>
        </div>

        {(detail?.report_attachments?.length ?? 0) > 0 ? (
          <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
              Photos on original report
            </h2>
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {(detail?.report_attachments ?? []).map((attachment) => (
                <li key={attachment.id}>
                  <AttachmentPreview
                    previewUrl={attachment.preview_url}
                    alt="Original report photo"
                    authMode="admin"
                  />
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
            Reporter chat
          </h2>
          <div className="mt-4 space-y-3">
            {(detail?.messages ?? []).map((message) => (
              <div
                key={message.id}
                className={`rounded-xl px-4 py-3 text-sm ${
                  message.sender_type === "admin"
                    ? "ml-8 bg-ink text-paper"
                    : "mr-8 bg-paper text-ink ring-1 ring-ink/10"
                }`}
              >
                <p className="mb-1 text-xs uppercase tracking-wide opacity-70">
                  {message.sender_type}
                </p>
                {message.attachment ? (
                  <AttachmentPreview
                    previewUrl={message.attachment.preview_url}
                    alt="Follow-up photo"
                    authMode="admin"
                  />
                ) : null}
                {message.content !== PHOTO_PLACEHOLDER || !message.attachment ? (
                  <p>{message.content}</p>
                ) : null}
              </div>
            ))}
          </div>
          {hasPermission("respond") ? (
            <div className="mt-4 flex gap-2">
              <input
                value={messageText}
                onChange={(event) => setMessageText(event.target.value)}
                placeholder="Reply to reporter"
                className="min-w-0 flex-1 rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleSendMessage()}
                className="inline-flex items-center gap-2 rounded-lg bg-sage px-4 py-3 text-sm font-semibold text-paper hover:bg-sage/90 disabled:opacity-60"
              >
                <Send size={16} />
                Send
              </button>
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink/60">
              You do not have permission to respond to reporters.
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink/60">
            Internal notes
          </h2>
          <div className="mt-4 space-y-3">
            {(detail?.internal_notes ?? []).map((note) => (
              <div
                key={note.id}
                className="rounded-xl border border-ink/10 bg-paper px-4 py-3 text-sm text-ink"
              >
                <p>{note.content}</p>
                <p className="mt-2 text-xs text-ink/50">
                  {new Date(note.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
          {hasPermission("respond") ? (
            <div className="mt-4 space-y-3">
              <textarea
                value={noteText}
                onChange={(event) => setNoteText(event.target.value)}
                rows={3}
                placeholder="Add an internal note"
                className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleAddNote()}
                className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-60"
              >
                Add note
              </button>
            </div>
          ) : (
            <p className="mt-3 text-sm text-ink/60">
              You do not have permission to add internal notes.
            </p>
          )}
        </section>

        {hasRole("hoh") ? (
          <section className="rounded-2xl border border-brass/30 bg-brass/5 p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <Trash2 className="mt-0.5 text-brass" size={18} />
              <div className="w-full">
                <h2 className="font-semibold text-ink">Delete report</h2>
                <p className="mt-1 text-sm text-ink/70">
                  Head of Hospi only. This archives the report and writes a delete audit
                  entry.
                </p>
                <textarea
                  value={deleteReason}
                  onChange={(event) => setDeleteReason(event.target.value)}
                  rows={3}
                  placeholder="Delete reason"
                  className="mt-4 w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
                />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void handleDelete()}
                  className="mt-3 rounded-lg bg-brass px-4 py-2 text-sm font-semibold text-paper hover:bg-brass/90 disabled:opacity-60"
                >
                  Delete and archive
                </button>
              </div>
            </div>
          </section>
        ) : null}
      </div>

      <RecusalConfirmModal
        open={recusalOpen}
        message={recusalMessage}
        onCancel={() => {
          setRecusalOpen(false);
          setPendingRecusal(null);
        }}
        onConfirm={() => {
          if (pendingRecusal) {
            void runRecusalSensitiveAction(pendingRecusal, true);
          }
        }}
      />
    </>
  );
}
