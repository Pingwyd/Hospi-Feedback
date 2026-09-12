import { Suspense } from "react";

import { ReportInbox } from "@/components/admin/ReportInbox";
import { SkeletonCard } from "@/components/admin/SkeletonBlock";

export default function AdminReportsPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-ink">Report inbox</h1>
            <p className="mt-1 text-sm text-ink/60">
              Filter reports and open a case to triage, respond, or escalate.
            </p>
          </div>
          <SkeletonCard />
        </div>
      }
    >
      <ReportInbox />
    </Suspense>
  );
}
