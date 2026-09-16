"use client";

import { AlertCircle, ImagePlus, Trash2 } from "lucide-react";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useId, useRef, useState } from "react";

import { PrivacyNotice, privacyLinkClass } from "@/components/report/PrivacyNotice";
import { PhotoConfirmModal } from "@/components/shared/PhotoConfirmModal";
import { ApiError } from "@/lib/api/client";
import {
  type CreateReportPayload,
  type ReportType,
  type Severity,
  createReport,
  uploadAttachment,
} from "@/lib/api/reports";
import { formatMaxAttachmentSize } from "@/lib/attachments/constants";
import { usePhotoConfirmFlow } from "@/lib/hooks/usePhotoConfirmFlow";

const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: "complaint", label: "Complaint" },
  { value: "suggestion", label: "Suggestion" },
  { value: "recognition", label: "Recognition" },
];

const SEVERITIES: { value: Severity; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

type PendingReportPhoto = {
  id: string;
  file: File;
  previewUrl: string;
};

type ReportFormProps = {
  onSubmitted: (ticketCode: string) => void;
};

export function ReportForm({ onSubmitted }: ReportFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const addPhotoButtonRef = useRef<HTMLButtonElement>(null);
  const pendingPhotosRef = useRef<PendingReportPhoto[]>([]);
  const idPrefix = useId();

  const [reportType, setReportType] = useState<ReportType>("complaint");
  const [description, setDescription] = useState("");
  const [memberName, setMemberName] = useState("");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [pendingPhotos, setPendingPhotos] = useState<PendingReportPhoto[]>([]);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    pendingPhotosRef.current = pendingPhotos;
  }, [pendingPhotos]);

  useEffect(() => {
    return () => {
      for (const entry of pendingPhotosRef.current) {
        URL.revokeObjectURL(entry.previewUrl);
      }
    };
  }, []);

  const addPendingPhoto = useCallback((file: File) => {
    const previewUrl = URL.createObjectURL(file);
    setPendingPhotos((current) => [
      ...current,
      { id: `${idPrefix}-${file.name}-${file.lastModified}-${current.length}`, file, previewUrl },
    ]);
  }, [idPrefix]);

  const photoFlow = usePhotoConfirmFlow({
    onValidationErrors: (messages) => {
      setFieldErrors(messages);
    },
    onConfirm: async (files) => {
      for (const file of files) {
        addPendingPhoto(file);
      }
    },
  });

  function removePendingPhoto(id: string) {
    setPendingPhotos((current) => {
      const target = current.find((entry) => entry.id === id);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return current.filter((entry) => entry.id !== id);
    });
  }

  function handlePhotoInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    if (photoFlow.isBusy) {
      event.target.value = "";
      return;
    }
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length === 0) {
      return;
    }
    setFieldErrors([]);
    photoFlow.enqueueFiles(files);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors([]);

    const nextFieldErrors: string[] = [];
    if (!description.trim()) {
      nextFieldErrors.push("Description is required.");
    }
    if (!privacyAccepted) {
      nextFieldErrors.push("You must read and accept the privacy notice.");
    }
    if (nextFieldErrors.length > 0) {
      setFieldErrors(nextFieldErrors);
      return;
    }

    setSubmitting(true);
    try {
      const payload: CreateReportPayload = {
        report_type: reportType,
        description: description.trim(),
      };
      if (memberName.trim()) {
        payload.reported_member_name = memberName.trim();
      }
      if (severity) {
        payload.severity = severity;
      }

      const result = await createReport(payload);

      for (const entry of pendingPhotos) {
        await uploadAttachment(result.ticket_code, entry.file);
      }

      for (const entry of pendingPhotos) {
        URL.revokeObjectURL(entry.previewUrl);
      }
      setPendingPhotos([]);

      onSubmitted(result.ticket_code);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Submission failed. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-ink">Submit a report</h1>
        <p className="mt-2 text-sm text-ink/70">
          Share feedback anonymously. Fields marked with * are required.
        </p>
      </header>

      <div className="space-y-5 rounded-2xl border border-ink/10 bg-surface/60 p-6 shadow-sm">
        <div>
          <label htmlFor="report-type" className="mb-2 block text-sm font-medium text-ink">
            Report type <span className="text-brass">*</span>
          </label>
          <select
            id="report-type"
            value={reportType}
            onChange={(event) => setReportType(event.target.value as ReportType)}
            className="w-full appearance-none rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
          >
            {REPORT_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="description" className="mb-2 block text-sm font-medium text-ink">
            Description <span className="text-brass">*</span>
          </label>
          <textarea
            id="description"
            required
            rows={6}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="w-full resize-y rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
            placeholder="What happened? Include relevant context."
          />
        </div>

        <div>
          <label htmlFor="member-name" className="mb-2 block text-sm font-medium text-ink">
            Named member (optional)
          </label>
          <input
            id="member-name"
            type="text"
            value={memberName}
            onChange={(event) => setMemberName(event.target.value)}
            className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
            placeholder="If applicable"
          />
        </div>

        <div>
          <label htmlFor="severity" className="mb-2 block text-sm font-medium text-ink">
            Severity (optional)
          </label>
          <select
            id="severity"
            value={severity}
            onChange={(event) => setSeverity(event.target.value as Severity | "")}
            className="w-full appearance-none rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
          >
            <option value="">Not specified</option>
            {SEVERITIES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <span className="mb-2 block text-sm font-medium text-ink">Photos (optional)</span>
          <input
            ref={fileInputRef}
            id="photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={handlePhotoInputChange}
            className="sr-only"
          />
          <button
            ref={addPhotoButtonRef}
            type="button"
            disabled={submitting || photoFlow.isBusy || photoFlow.modalOpen}
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-2 rounded-lg border border-dashed border-ink/20 bg-paper px-4 py-3 text-sm font-medium text-ink transition hover:border-sage hover:text-sage disabled:opacity-60"
          >
            <ImagePlus size={18} aria-hidden />
            Add photo evidence
          </button>
          <p className="mt-2 text-xs text-ink/60">
            JPEG, PNG, or WebP. Up to {formatMaxAttachmentSize()} per photo. Add as many photos
            as you need; each is reviewed before it is attached.
          </p>

          {pendingPhotos.length > 0 ? (
            <ul className="mt-4 flex flex-wrap gap-3">
              {pendingPhotos.map((entry) => (
                <li key={entry.id} className="relative">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={entry.previewUrl}
                    alt={`Pending evidence: ${entry.file.name}`}
                    className="h-24 w-24 rounded-xl border border-ink/10 object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => removePendingPhoto(entry.id)}
                    disabled={submitting}
                    className="absolute -right-2 -top-2 rounded-full border border-ink/10 bg-paper p-1 text-ink/70 shadow-sm hover:text-brass disabled:opacity-60"
                    aria-label={`Remove ${entry.file.name} from report`}
                  >
                    <Trash2 size={14} aria-hidden />
                  </button>
                  <p className="mt-1 max-w-24 truncate text-[11px] text-ink/60">{entry.file.name}</p>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>

      <PhotoConfirmModal
        open={photoFlow.modalOpen}
        items={photoFlow.pendingItems.map((item) => ({
          id: item.id,
          previewUrl: item.previewUrl,
          fileName: item.file.name,
        }))}
        title="Add photos to report"
        description="Review each photo below before attaching them as evidence on your report."
        confirmLabel={
          photoFlow.pendingItems.length > 1
            ? `Add ${photoFlow.pendingItems.length} photos to report`
            : "Add photo to report"
        }
        confirming={photoFlow.confirming}
        confirmingLabel="Adding..."
        onConfirm={() => {
          void photoFlow.handleConfirm();
        }}
        onAddMorePhotos={() => {
          if (!photoFlow.isBusy) {
            fileInputRef.current?.click();
          }
        }}
        onRemoveItem={photoFlow.removePendingItem}
        onCancel={photoFlow.handleCancel}
        returnFocusRef={addPhotoButtonRef}
      />

      <PrivacyNotice />

      <label className="flex items-start gap-3 text-sm text-ink/80">
        <input
          type="checkbox"
          checked={privacyAccepted}
          onChange={(event) => setPrivacyAccepted(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-ink/20 text-sage focus:ring-sage"
        />
        <span>
          I have read the{" "}
          <Link href="/privacy" className={privacyLinkClass}>
            privacy notice
          </Link>{" "}
          and understand how anonymity works on this platform.{" "}
          <span className="text-brass">*</span>
        </span>
      </label>

      {fieldErrors.length > 0 ? (
        <div
          role="alert"
          className="rounded-lg border border-brass/30 bg-brass/10 px-4 py-3 text-sm text-ink"
        >
          <ul className="list-disc space-y-1 pl-5">
            {fieldErrors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {error ? (
        <p
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-sm text-ink"
        >
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-brass" aria-hidden />
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={submitting || photoFlow.modalOpen}
        className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Submitting..." : "Submit report"}
      </button>
    </form>
  );
}
