"use client";

import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, FileDown, Filter, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  downloadAdminReportExport,
  type AdminExportFormat,
} from "@/lib/api/admin-export";
import { useAdminReportsList } from "@/lib/hooks/useAdminReportsList";
import { useAdminWebSocket } from "@/lib/hooks/useAdminWebSocket";
import { useReportInboxUrlState } from "@/lib/hooks/useReportInboxUrlState";
import { invalidateAdminReportLists } from "@/lib/query/admin-report-queries";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "new", label: "New" },
  { value: "under_review", label: "Under review" },
  { value: "assigned", label: "Assigned" },
  { value: "in_progress", label: "In progress" },
  { value: "escalated", label: "Escalated" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
  { value: "marked_false", label: "Marked false" },
];

function statusBadgeClass(status: string | null | undefined): string {
  switch (status) {
    case "new":
      return "bg-sage/15 text-sage";
    case "escalated":
      return "bg-brass/15 text-brass";
    case "closed":
    case "resolved":
      return "bg-ink/10 text-ink/70";
    default:
      return "bg-surface text-ink/80 ring-1 ring-ink/10";
  }
}

function exportFilterSummary(status: string, keyword: string): string {
  const parts: string[] = [];
  if (status) {
    parts.push(`status: ${status.replace(/_/g, " ")}`);
  }
  if (keyword) {
    parts.push(`keyword: "${keyword}"`);
  }
  if (parts.length === 0) {
    return "All reports (no filters applied)";
  }
  return parts.join(", ");
}

export function ReportInbox() {
  const queryClient = useQueryClient();
  const { hasPermission } = useAdminSession();
  const { status, keyword, keywordDraft, setKeywordDraft, setStatus } =
    useReportInboxUrlState();
  const [liveNotice, setLiveNotice] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<AdminExportFormat>("pdf");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const canExport = hasPermission("export");

  const {
    data: reports = [],
    isPending,
    isFetching,
    error,
  } = useAdminReportsList({ status, keyword, limit: 100 });

  useAdminWebSocket({
    enabled: true,
    onEvent: (event) => {
      if (event.event === "new_report") {
        setLiveNotice("New report received.");
        void invalidateAdminReportLists(queryClient);
      }
      if (event.event === "new_message") {
        setLiveNotice("New message on a report.");
      }
    },
  });

  const loading = isPending || (isFetching && reports.length === 0);
  const errorMessage =
    error instanceof ApiError
      ? error.message
      : error
        ? "Could not load reports."
        : null;

  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      await downloadAdminReportExport(
        {
          status: status || undefined,
          keyword: keyword || undefined,
        },
        exportFormat,
      );
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }

  const resultsAnnouncement = useMemo(() => {
    if (loading) {
      return "Loading reports.";
    }
    if (errorMessage) {
      return "Could not load reports.";
    }
    if (reports.length === 0) {
      return "No reports match the current filters.";
    }
    const noun = reports.length === 1 ? "report" : "reports";
    return `${reports.length} ${noun} shown.`;
  }, [errorMessage, loading, reports.length]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Report inbox</h1>
        <p className="mt-1 text-sm text-ink/60">
          Filter reports and open a case to triage, respond, or escalate.
        </p>
      </div>

      {liveNotice ? (
        <div className="rounded-lg border border-sage/25 bg-sage/10 px-4 py-2 text-sm text-ink">
          {liveNotice}
        </div>
      ) : null}

      <div
        role="search"
        className="rounded-2xl border border-ink/10 bg-surface/60 p-4 shadow-sm"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="mb-1 flex items-center gap-2 text-sm font-medium text-ink">
              <Search size={16} aria-hidden="true" />
              Keyword
            </span>
            <input
              type="search"
              value={keywordDraft}
              onChange={(event) => setKeywordDraft(event.target.value)}
              placeholder="Search description or member name"
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>
          <label className="block">
            <span className="mb-1 flex items-center gap-2 text-sm font-medium text-ink">
              <Filter size={16} aria-hidden="true" />
              Status
            </span>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {canExport ? (
          <div className="mt-4 flex flex-col gap-3 border-t border-ink/10 pt-4 sm:flex-row sm:items-end sm:justify-between">
            <p className="text-sm text-ink/70">
              Export uses the current URL filters:{" "}
              <span className="font-medium text-ink">
                {exportFilterSummary(status, keyword)}
              </span>
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-ink/50">
                  Format
                </span>
                <select
                  value={exportFormat}
                  onChange={(event) =>
                    setExportFormat(event.target.value as AdminExportFormat)
                  }
                  disabled={exporting}
                  className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2 disabled:opacity-60"
                >
                  <option value="pdf">PDF</option>
                  <option value="docx">DOCX</option>
                </select>
              </label>
              <button
                type="button"
                disabled={exporting}
                onClick={() => void handleExport()}
                className="inline-flex items-center gap-2 rounded-lg bg-sage px-4 py-2 text-sm font-semibold text-paper hover:bg-sage/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <FileDown size={16} aria-hidden="true" />
                {exporting ? "Exporting..." : "Export filtered reports"}
              </button>
            </div>
          </div>
        ) : null}

        {exportError ? (
          <div
            role="alert"
            className="mt-4 flex items-start gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-sm text-ink"
          >
            <AlertCircle
              size={16}
              className="mt-0.5 shrink-0 text-brass"
              aria-hidden="true"
            />
            {exportError}
          </div>
        ) : null}
      </div>

      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {resultsAnnouncement}
      </p>

      {loading ? (
        <SkeletonCard />
      ) : errorMessage ? (
        <div
          role="alert"
          className="rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
        >
          {errorMessage}
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-2xl border border-ink/10 bg-surface/60 p-8 text-center text-sm text-ink/60">
          No reports match the current filters.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-surface/60 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-ink/10 bg-paper/70 text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Severity</th>
                  <th className="px-4 py-3 font-medium">Member</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr
                    key={report.id}
                    className="border-b border-ink/5 hover:bg-paper/50"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/admin/reports/${report.id}`}
                        className="font-medium text-sage underline"
                      >
                        {report.report_type ?? "Report"}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${statusBadgeClass(report.status)}`}
                      >
                        {(report.status ?? "unknown").replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 capitalize text-ink/70">
                      {report.severity ?? "N/A"}
                    </td>
                    <td className="px-4 py-3 text-ink/70">
                      {report.reported_member_name ?? "N/A"}
                    </td>
                    <td className="px-4 py-3 text-ink/60">
                      {report.created_at
                        ? new Date(report.created_at).toLocaleString()
                        : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
