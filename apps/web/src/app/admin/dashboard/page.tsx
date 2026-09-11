import { DashboardOverview } from "@/components/admin/DashboardOverview";

export default function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Dashboard</h1>
        <p className="mt-1 text-sm text-ink/60">
          Monitor report volume, status mix, and unresolved backlog.
        </p>
      </div>
      <DashboardOverview />
    </div>
  );
}
