"use client";

import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { AdminUser } from "@/lib/api/admin-settings";

import { AdminPermissionsEditor } from "./AdminPermissionsEditor";

type AdminPermissionsModalProps = {
  open: boolean;
  admin: AdminUser | null;
  saving: boolean;
  onCancel: () => void;
  onSave: (permissions: string[]) => void;
};

export function AdminPermissionsModal({
  open,
  admin,
  saving,
  onCancel,
  onSave,
}: AdminPermissionsModalProps) {
  const titleId = "admin-permissions-modal-title";
  const saveRef = useRef<HTMLButtonElement>(null);
  const [permissions, setPermissions] = useState<string[]>([]);

  useEffect(() => {
    if (!open || !admin) {
      return;
    }
    setPermissions(admin.permissions);
    saveRef.current?.focus();
  }, [open, admin]);

  if (!open || !admin) {
    return null;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave(permissions);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4 py-6"
      role="presentation"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-ink/10 bg-paper p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h2 id={titleId} className="text-lg font-semibold text-ink">
              Edit permissions
            </h2>
            <p className="mt-1 text-sm text-ink/60">{admin.full_name}</p>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md p-1 text-ink/60 hover:bg-ink/5 hover:text-ink"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <AdminPermissionsEditor
            selected={permissions}
            onChange={setPermissions}
          />
          <div className="flex flex-wrap justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-white/70"
            >
              Cancel
            </button>
            <button
              ref={saveRef}
              type="submit"
              disabled={saving}
              className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : "Save permissions"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
