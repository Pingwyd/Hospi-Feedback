"use client";

import Link from "next/link";
import { Filter, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  listAdminReports,
  type ReportSummary,
} from "@/lib/api/admin-reports";
import { useAdminWebSocket } from "@/lib/hooks/useAdminWebSocket";

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
      return "bg-white text-ink/80 ring-1 ring-ink/10";
  }
}

export function ReportInbox() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [status, setStatus] = useState("");
  const [keyword, setKeyword] = useState("");
  const [appliedKeyword, setAppliedKeyword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveNotice, setLiveNotice] = useState<string | null>(null);

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listAdminReports({
        status: status || undefined,
        keyword: appliedKeyword || undefined,
        limit: 100,
      });
      setReports(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load reports.");
    } finally {
      setLoading(false);
    }
  }, [status, appliedKeyword]);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  useAdminWebSocket({
    enabled: true,
    onEvent: (event) => {
      if (event.event === "new_report") {
        setLiveNotice("New report received.");
        void loadReports();
      }
      if (event.event === "new_message") {
        setLiveNotice("New message on a report.");
      }
    },
  });

  function handleSearchSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAppliedKeyword(keyword.trim());
  }

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

      <div className="rounded-2xl border border-ink/10 bg-white/60 p-4 shadow-sm">
        <form
          onSubmit={handleSearchSubmit}
          className="grid gap-4 md:grid-cols-[1fr_auto_auto]"
        >
          <label className="block">
            <span className="mb-1 flex items-center gap-2 text-sm font-medium text-ink">
              <Search size={16} />
              Keyword
            </span>
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Search description or member name"
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>
          <label className="block">
            <span className="mb-1 flex items-center gap-2 text-sm font-medium text-ink">
              <Filter size={16} />
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
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-ink/90"
            >
              Apply filters
            </button>
          </div>
        </form>
      </div>

      {loading ? (
        <SkeletonCard />
      ) : error ? (
        <div
          role="alert"
          className="rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
        >
          {error}
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-2xl border border-ink/10 bg-white/60 p-8 text-center text-sm text-ink/60">
          No reports match the current filters.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/60 shadow-sm">
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
