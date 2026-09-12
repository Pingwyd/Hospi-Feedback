"use client";

import { useMemo, useState } from "react";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";

import { AdminUsersPanel } from "./_components/AdminUsersPanel";
import { CategoriesPanel } from "./_components/CategoriesPanel";
import { EscalationContactsPanel } from "./_components/EscalationContactsPanel";

type SettingsTab = "categories" | "escalation-contacts" | "admins";

export default function AdminSettingsPage() {
  const { hasPermission } = useAdminSession();

  const tabs = useMemo(
    () =>
      [
        { id: "categories" as const, label: "Categories", visible: true },
        {
          id: "escalation-contacts" as const,
          label: "Escalation contacts",
          visible: true,
        },
        {
          id: "admins" as const,
          label: "Admin users",
          visible: hasPermission("manage_admins"),
        },
      ].filter((tab) => tab.visible),
    [hasPermission],
  );

  const [activeTab, setActiveTab] = useState<SettingsTab>("categories");

  const resolvedTab = tabs.some((tab) => tab.id === activeTab)
    ? activeTab
    : tabs[0]?.id ?? "categories";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Settings</h1>
        <p className="mt-1 text-sm text-ink/60">
          Configuration screens are permission-gated to match the admin API.
        </p>
      </div>

      <div
        role="tablist"
        aria-label="Settings sections"
        className="flex flex-wrap gap-2"
      >
        {tabs.map((tab) => {
          const selected = resolvedTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                selected
                  ? "bg-ink text-paper"
                  : "bg-surface/70 text-ink/70 ring-1 ring-ink/10 hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      <div role="tabpanel">
        {resolvedTab === "categories" ? <CategoriesPanel /> : null}
        {resolvedTab === "escalation-contacts" ? <EscalationContactsPanel /> : null}
        {resolvedTab === "admins" ? <AdminUsersPanel /> : null}
      </div>
    </div>
  );
}
