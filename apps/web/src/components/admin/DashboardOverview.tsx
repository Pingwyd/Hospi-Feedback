"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";

import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  fetchDashboardStats,
  type DashboardStats,
} from "@/lib/api/admin-dashboard";

function BarChart({
  title,
  counts,
}: {
  title: string;
  counts: Record<string, number>;
}) {
  const entries = Object.entries(counts);
  const max = Math.max(...entries.map(([, count]) => count), 1);

  return (
    <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-ink/60">
        {title}
      </h2>
      <div className="space-y-3">
        {entries.length === 0 ? (
          <p className="text-sm text-ink/60">No data yet.</p>
        ) : (
          entries.map(([label, count]) => (
            <div key={label}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="capitalize text-ink">{label.replace(/_/g, " ")}</span>
                <span className="font-medium text-ink/70">{count}</span>
              </div>
              <div className="h-2 rounded-full bg-paper">
                <div
                  className="h-2 rounded-full bg-sage"
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export function DashboardOverview() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchDashboardStats();
        if (active) {
          setStats(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Could not load stats.");
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

  if (loading) {
    return (
      <div className="grid gap-6 lg:grid-cols-2">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div
        role="alert"
        className="rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
      >
        {error ?? "Could not load dashboard stats."}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {stats.system_alerts?.map((alert) => (
        <div
          key={alert.id}
          role="alert"
          className="rounded-2xl border border-brass/40 bg-brass/15 p-4"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 shrink-0 text-brass" size={18} />
            <div>
              <p className="font-semibold text-ink">System alert</p>
              <p className="mt-1 text-sm text-ink/80">{alert.message}</p>
            </div>
          </div>
        </div>
      ))}

      {stats.oldest_unresolved ? (
        <div className="rounded-2xl border border-brass/30 bg-brass/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 text-brass" size={18} />
            <div>
              <p className="font-semibold text-ink">Oldest unresolved report</p>
              <p className="mt-1 text-sm text-ink/70">
                Status {stats.oldest_unresolved.status} since{" "}
                {new Date(stats.oldest_unresolved.created_at).toLocaleString()}
              </p>
              <Link
                href={`/admin/reports/${stats.oldest_unresolved.report_id}`}
                className="mt-2 inline-block text-sm font-medium text-sage underline"
              >
                Open report
              </Link>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <BarChart title="Status breakdown" counts={stats.status_counts} />
        <BarChart title="Report types" counts={stats.report_type_counts} />
      </div>

      <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-ink/60">
          Submissions by day
        </h2>
        <div className="flex items-end gap-2 overflow-x-auto pb-2">
          {stats.submissions_by_day.length === 0 ? (
            <p className="text-sm text-ink/60">No submissions recorded yet.</p>
          ) : (
            stats.submissions_by_day.map((entry) => {
              const maxDay = Math.max(
                ...stats.submissions_by_day.map((item) => item.count),
                1,
              );
              return (
                <div key={entry.date} className="flex min-w-[3rem] flex-col items-center gap-2">
                  <div
                    className="w-8 rounded-t-md bg-brass/80"
                    style={{ height: `${Math.max(12, (entry.count / maxDay) * 120)}px` }}
                    title={`${entry.count} on ${entry.date}`}
                  />
                  <span className="text-[10px] text-ink/60">
                    {entry.date.slice(5)}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
