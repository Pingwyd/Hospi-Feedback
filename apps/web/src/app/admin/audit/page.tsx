"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { ApiError } from "@/lib/api/admin-fetch";
import { fetchAuditLog, type AuditLogEntry } from "@/lib/api/admin-dashboard";

export default function AdminAuditPage() {
  const router = useRouter();
  const { hasRole, loading: sessionLoading } = useAdminSession();
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionLoading) {
      return;
    }
    if (!hasRole("hoh", "asst_head")) {
      router.replace("/admin/dashboard");
    }
  }, [hasRole, router, sessionLoading]);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const rows = await fetchAuditLog();
        if (active) {
          setEntries(rows);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Could not load audit log.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Audit log</h1>
        <p className="mt-1 text-sm text-ink/60">
          Review admin actions across reports and configuration changes.
        </p>
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
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/60 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-ink/10 bg-paper/70 text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Report</th>
                  <th className="px-4 py-3 font-medium">Admin</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-ink/5">
                    <td className="px-4 py-3 text-ink/60">
                      {new Date(entry.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 capitalize text-ink">
                      {entry.action.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-ink/70">
                      {entry.report_id ?? "N/A"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-ink/70">
                      {entry.admin_id}
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
