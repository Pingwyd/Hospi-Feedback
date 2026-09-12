"use client";

import { ADMIN_PERMISSIONS } from "@/lib/api/admin-settings";

const PERMISSION_LABELS: Record<string, string> = {
  view: "View reports",
  respond: "Respond to reports",
  assign: "Assign reports",
  close: "Close reports",
  export: "Export data",
  manage_categories: "Manage categories",
  manage_admins: "Manage admins",
  manage_escalation_contacts: "Manage escalation contacts",
};

type AdminPermissionsEditorProps = {
  selected: string[];
  onChange: (permissions: string[]) => void;
  disabled?: boolean;
};

export function AdminPermissionsEditor({
  selected,
  onChange,
  disabled = false,
}: AdminPermissionsEditorProps) {
  function togglePermission(permission: string) {
    if (disabled) {
      return;
    }
    if (selected.includes(permission)) {
      onChange(selected.filter((item) => item !== permission));
      return;
    }
    onChange([...selected, permission]);
  }

  return (
    <fieldset className="space-y-2" disabled={disabled}>
      <legend className="mb-2 text-sm font-medium text-ink">Permissions</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {ADMIN_PERMISSIONS.map((permission) => {
          const checked = selected.includes(permission);
          return (
            <label
              key={permission}
              className={`flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 text-sm ${
                checked
                  ? "border-sage/40 bg-sage/10 text-ink"
                  : "border-ink/10 bg-white/60 text-ink/80"
              } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => togglePermission(permission)}
                className="mt-0.5 accent-sage"
              />
              <span>
                <span className="block font-medium">
                  {PERMISSION_LABELS[permission] ?? permission}
                </span>
                <span className="text-xs text-ink/50">{permission}</span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
