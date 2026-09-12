"use client";

import { AlertCircle, ImagePlus, RefreshCw, Send } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { checkAccessSession } from "@/lib/api/access";
import { AttachmentPreview } from "@/components/shared/AttachmentPreview";
import {
  type TicketStatusResponse,
  fetchTicketStatus,
  postReporterMessage,
  uploadAttachment,
} from "@/lib/api/reports";

const PHOTO_PLACEHOLDER = "Photo attached";

type StatusPanelProps = {
  ticketCode: string;
};

function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

export function StatusPanel({ ticketCode }: StatusPanelProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TicketStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await fetchTicketStatus(ticketCode);
      setData(payload);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError("No report found for that ticket code.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Could not load status.");
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [ticketCode]);

  useEffect(() => {
    let active = true;
    checkAccessSession().then((ok) => {
      if (!active) {
        return;
      }
      if (!ok) {
        router.replace("/access");
        return;
      }
      setCheckingSession(false);
      void loadStatus();
    });
    return () => {
      active = false;
    };
  }, [loadStatus, router]);

  async function handleMessageSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim() || data?.status === "closed") {
      return;
    }
    setActionError(null);
    setSending(true);
    try {
      await postReporterMessage(ticketCode, message.trim());
      setMessage("");
      await loadStatus();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Could not send message.");
      }
    } finally {
      setSending(false);
    }
  }

  async function handleAttachmentSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || data?.status === "closed") {
      return;
    }
    setActionError(null);
    setUploading(true);
    try {
      await uploadAttachment(ticketCode, file, { linkToThread: true });
      await loadStatus();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError("Could not upload attachment.");
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  if (checkingSession || loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton-shimmer h-10 w-40 rounded-lg" />
        <div className="skeleton-shimmer h-32 rounded-2xl" />
        <div className="skeleton-shimmer h-48 rounded-2xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-brass/30 bg-brass/10 p-6">
        <p className="flex items-start gap-2 text-sm text-ink">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-brass" aria-hidden />
          {error ?? "Report not found."}
        </p>
        <Link href="/status" className="mt-4 inline-block text-sm font-medium text-sage underline">
          Try another code
        </Link>
      </div>
    );
  }

  const isClosed = data.status === "closed";

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-sage">Ticket</p>
          <h1 className="font-mono text-2xl font-bold tracking-[0.25em] text-ink">
            {ticketCode}
          </h1>
        </div>
        <button
          type="button"
          onClick={() => void loadStatus()}
          className="inline-flex items-center gap-2 rounded-lg border border-ink/15 px-3 py-2 text-sm font-medium text-ink transition hover:bg-ink/5"
        >
          <RefreshCw size={16} aria-hidden />
          Refresh
        </button>
      </header>

      <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
        <dl className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-ink/60">Status</dt>
            <dd className="mt-1 font-medium capitalize text-ink">{statusLabel(data.status)}</dd>
          </div>
          <div>
            <dt className="text-ink/60">Type</dt>
            <dd className="mt-1 font-medium capitalize text-ink">{data.report_type}</dd>
          </div>
          {data.severity ? (
            <div>
              <dt className="text-ink/60">Severity</dt>
              <dd className="mt-1 font-medium capitalize text-ink">{data.severity}</dd>
            </div>
          ) : null}
          <div className="sm:col-span-2">
            <dt className="text-ink/60">Description</dt>
            <dd className="mt-1 whitespace-pre-wrap text-ink">{data.description}</dd>
          </div>
        </dl>
      </section>

      {(data.report_attachments?.length ?? 0) > 0 ? (
        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-ink">Photos on original report</h2>
          <ul className="grid gap-4 sm:grid-cols-2">
            {data.report_attachments.map((attachment) => (
              <li key={attachment.id}>
                <AttachmentPreview
                  previewUrl={attachment.preview_url}
                  alt="Original report photo"
                  authMode="session"
                />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold text-ink">Conversation</h2>
        {data.messages.length === 0 ? (
          <p className="text-sm text-ink/60">No messages yet.</p>
        ) : (
          <ul className="space-y-3">
            {data.messages.map((entry) => (
              <li
                key={entry.id}
                className={`rounded-xl px-4 py-3 text-sm ${
                  entry.sender_type === "reporter"
                    ? "bg-sage/10 text-ink"
                    : "border border-ink/10 bg-paper text-ink"
                }`}
              >
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink/50">
                  {entry.sender_type}
                </p>
                {entry.attachment ? (
                  <AttachmentPreview
                    previewUrl={entry.attachment.preview_url}
                    alt="Follow-up photo"
                    authMode="session"
                  />
                ) : null}
                {entry.content !== PHOTO_PLACEHOLDER || !entry.attachment ? (
                  <p className="whitespace-pre-wrap">{entry.content}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {isClosed ? (
        <p className="rounded-xl border border-ink/10 bg-paper px-4 py-3 text-sm text-ink/70">
          This report is closed. You can no longer send messages or upload attachments.
        </p>
      ) : (
        <section className="space-y-4 rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <form onSubmit={handleMessageSubmit} className="space-y-3">
            <label htmlFor="message" className="block text-sm font-medium text-ink">
              Send a message
            </label>
            <textarea
              id="message"
              rows={3}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
              placeholder="Follow up with the team"
            />
            <button
              type="submit"
              disabled={sending || !message.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper disabled:opacity-60"
            >
              <Send size={16} aria-hidden />
              {sending ? "Sending..." : "Send"}
            </button>
          </form>

          <div>
            <input
              ref={fileInputRef}
              id="status-photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleAttachmentSelected}
              className="sr-only"
            />
            <button
              type="button"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-lg border border-dashed border-ink/20 px-4 py-2 text-sm font-medium text-ink transition hover:border-sage hover:text-sage disabled:opacity-60"
            >
              <ImagePlus size={16} aria-hidden />
              {uploading ? "Uploading..." : "Add photo"}
            </button>
          </div>
        </section>
      )}

      {actionError ? (
        <p
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-sm text-ink"
        >
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-brass" aria-hidden />
          {actionError}
        </p>
      ) : null}
    </div>
  );
}
