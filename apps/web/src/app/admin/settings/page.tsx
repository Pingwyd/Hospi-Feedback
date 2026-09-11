"use client";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";

export default function AdminSettingsPage() {
  const { hasPermission } = useAdminSession();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Settings</h1>
        <p className="mt-1 text-sm text-ink/60">
          Configuration screens are permission-gated to match the admin API.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="font-semibold text-ink">Categories</h2>
          <p className="mt-2 text-sm text-ink/70">
            Manage report categories used during triage and filtering.
          </p>
          {hasPermission("manage_categories") ? (
            <p className="mt-4 text-sm font-medium text-sage">
              API ready. Full CRUD UI lands in the next settings pass.
            </p>
          ) : (
            <p className="mt-4 text-sm text-ink/50">
              Hidden: requires manage_categories permission.
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="font-semibold text-ink">Escalation contacts</h2>
          <p className="mt-2 text-sm text-ink/70">
            Maintain the contact list used when escalating a report.
          </p>
          {hasPermission("manage_escalation_contacts") ? (
            <p className="mt-4 text-sm font-medium text-sage">
              API ready. Full CRUD UI lands in the next settings pass.
            </p>
          ) : (
            <p className="mt-4 text-sm text-ink/50">
              Hidden: requires manage_escalation_contacts permission.
            </p>
          )}
        </section>

        <section className="rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
          <h2 className="font-semibold text-ink">Admin users</h2>
          <p className="mt-2 text-sm text-ink/70">
            Create admins, adjust permissions, and deactivate accounts.
          </p>
          {hasPermission("manage_admins") ? (
            <p className="mt-4 text-sm font-medium text-sage">
              API ready. Full CRUD UI lands in the next settings pass.
            </p>
          ) : (
            <p className="mt-4 text-sm text-ink/50">
              Hidden: requires manage_admins permission.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
