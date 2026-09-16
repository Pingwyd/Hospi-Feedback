"use client";

import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, FileDown, Filter, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { AdminDatePicker } from "@/components/admin/AdminDatePicker";
import { AdminSelect } from "@/components/admin/AdminSelect";
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
import {
  reportInboxFiltersToListApi,
  type ReportInboxUrlFilters,
} from "@/lib/report-inbox-filters";
import { invalidateAdminReportLists } from "@/lib/query/admin-report-queries";

const FIELD_INPUT_CLASS =
  "w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2";

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

const TYPE_OPTIONS = [
  { value: "", label: "All types" },
  { value: "complaint", label: "Complaint" },
  { value: "suggestion", label: "Suggestion" },
  { value: "recognition", label: "Recognition" },
];

const SEVERITY_OPTIONS = [
  { value: "", label: "All severities" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const EXPORT_FORMAT_OPTIONS = [
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "DOCX" },
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

function exportFilterSummary(filters: ReportInboxUrlFilters): string {
  const parts: string[] = [];
  if (filters.status) {
    parts.push(`status: ${filters.status.replace(/_/g, " ")}`);
  }
  if (filters.keyword) {
    parts.push(`keyword: "${filters.keyword}"`);
  }
  if (filters.type) {
    parts.push(`type: ${filters.type}`);
  }
  if (filters.severity) {
    parts.push(`severity: ${filters.severity}`);
  }
  if (filters.from) {
    parts.push(`from: ${filters.from}`);
  }
  if (filters.to) {
    parts.push(`to: ${filters.to}`);
  }
  if (parts.length === 0) {
    return "All reports (no filters applied)";
  }
  return parts.join(", ");
}

export function ReportInbox() {
  const queryClient = useQueryClient();
  const { hasPermission } = useAdminSession();
  const {
    status,
    keyword,
    type,
    severity,
    from,
    to,
    keywordDraft,
    setKeywordDraft,
    setStatus,
    setType,
    setSeverity,
    setFrom,
    setTo,
  } = useReportInboxUrlState();

  const inboxFilters = useMemo(
    (): ReportInboxUrlFilters => ({
      status,
      keyword,
      type,
      severity,
      from,
      to,
    }),
    [from, keyword, severity, status, to, type],
  );
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
  } = useAdminReportsList({ ...inboxFilters, limit: 100 });

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
        reportInboxFiltersToListApi(inboxFilters),
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
              className={FIELD_INPUT_CLASS}
            />
          </label>
          <AdminSelect
            label={
              <span className="flex items-center gap-2">
                <Filter size={16} aria-hidden="true" />
                Status
              </span>
            }
            value={status}
            options={STATUS_OPTIONS}
            onChange={setStatus}
            placeholder="All statuses"
          />
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <AdminSelect
            label="Report type"
            value={type}
            options={TYPE_OPTIONS}
            onChange={setType}
            placeholder="All types"
          />
          <AdminSelect
            label="Severity"
            value={severity}
            options={SEVERITY_OPTIONS}
            onChange={setSeverity}
            placeholder="All severities"
          />
          <AdminDatePicker
            label="Submitted from"
            value={from}
            onChange={setFrom}
            placeholder="Any start date"
            max={to || undefined}
          />
          <AdminDatePicker
            label="Submitted to"
            value={to}
            onChange={setTo}
            placeholder="Any end date"
            min={from || undefined}
          />
        </div>

        {canExport ? (
          <div className="mt-4 flex flex-col gap-3 border-t border-ink/10 pt-4 sm:flex-row sm:items-end sm:justify-between">
            <p className="text-sm text-ink/70">
              Export uses the current URL filters:{" "}
              <span className="font-medium text-ink">
                {exportFilterSummary(inboxFilters)}
              </span>
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <div className="min-w-[8rem]">
                <AdminSelect
                  label={
                    <span className="text-xs font-medium uppercase tracking-wide text-ink/50">
                      Format
                    </span>
                  }
                  value={exportFormat}
                  options={EXPORT_FORMAT_OPTIONS}
                  onChange={(value) =>
                    setExportFormat(value as AdminExportFormat)
                  }
                  disabled={exporting}
                />
              </div>
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
