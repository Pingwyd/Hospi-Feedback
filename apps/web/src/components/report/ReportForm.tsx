"use client";

import { AlertCircle, ImagePlus } from "lucide-react";
import { FormEvent, useRef, useState } from "react";

import { PrivacyNotice } from "@/components/report/PrivacyNotice";
import { ApiError } from "@/lib/api/client";
import {
  type CreateReportPayload,
  type ReportType,
  type Severity,
  createReport,
  uploadAttachment,
} from "@/lib/api/reports";

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

type ReportFormProps = {
  onSubmitted: (ticketCode: string) => void;
};

export function ReportForm({ onSubmitted }: ReportFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [reportType, setReportType] = useState<ReportType>("complaint");
  const [description, setDescription] = useState("");
  const [memberName, setMemberName] = useState("");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  function handlePhotoChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setPhoto(file);
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

      if (photo) {
        await uploadAttachment(result.ticket_code, photo);
      }

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

      <div className="space-y-5 rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
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
          <span className="mb-2 block text-sm font-medium text-ink">Photo (optional)</span>
          <input
            ref={fileInputRef}
            id="photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handlePhotoChange}
            className="sr-only"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-2 rounded-lg border border-dashed border-ink/20 bg-paper px-4 py-3 text-sm font-medium text-ink transition hover:border-sage hover:text-sage"
          >
            <ImagePlus size={18} aria-hidden />
            {photo ? photo.name : "Choose JPEG, PNG, or WebP (max 5 MB)"}
          </button>
        </div>
      </div>

      <PrivacyNotice />

      <label className="flex items-start gap-3 text-sm text-ink/80">
        <input
          type="checkbox"
          checked={privacyAccepted}
          onChange={(event) => setPrivacyAccepted(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-ink/20 text-sage focus:ring-sage"
        />
        <span>
          I have read the privacy notice and understand how anonymity works on this
          platform. <span className="text-brass">*</span>
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
        disabled={submitting}
        className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Submitting..." : "Submit report"}
      </button>
    </form>
  );
}
