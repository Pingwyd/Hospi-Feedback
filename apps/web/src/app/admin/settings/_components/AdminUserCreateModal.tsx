"use client";

import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import {
  ADMIN_ROLES,
  type AdminRole,
  type CreateAdminInput,
} from "@/lib/api/admin-settings";

import { AdminPermissionsEditor } from "./AdminPermissionsEditor";

type AdminUserCreateModalProps = {
  open: boolean;
  saving: boolean;
  onCancel: () => void;
  onSave: (input: CreateAdminInput) => void;
};

const EMPTY_FORM = {
  full_name: "",
  email: "",
  password: "",
  role: "custom" as AdminRole,
  subunit: "",
  permissions: [] as string[],
};

export function AdminUserCreateModal({
  open,
  saving,
  onCancel,
  onSave,
}: AdminUserCreateModalProps) {
  const titleId = "admin-user-create-modal-title";
  const firstFieldRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  useEffect(() => {
    if (!open) {
      return;
    }
    setForm(EMPTY_FORM);
    firstFieldRef.current?.focus();
  }, [open]);

  if (!open) {
    return null;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave({
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
      role: form.role,
      subunit: form.subunit.trim() || null,
      permissions: form.permissions,
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/40 px-4 py-6"
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
          <h2 id={titleId} className="text-lg font-semibold text-ink">
            Create admin user
          </h2>
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
          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">
              Full name<span className="text-brass">*</span>
            </span>
            <input
              ref={firstFieldRef}
              value={form.full_name}
              onChange={(event) =>
                setForm((current) => ({ ...current, full_name: event.target.value }))
              }
              required
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">
              Email<span className="text-brass">*</span>
            </span>
            <input
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
              required
              autoComplete="off"
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">
              Initial password<span className="text-brass">*</span>
            </span>
            <input
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
              required
              minLength={12}
              autoComplete="new-password"
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
            <p className="mt-1 text-xs text-ink/50">Minimum 12 characters.</p>
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1 text-sm font-medium text-ink">
                Role<span className="text-brass">*</span>
              </span>
              <select
                value={form.role}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    role: event.target.value as AdminRole,
                  }))
                }
                required
                className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              >
                {ADMIN_ROLES.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="mb-1 text-sm font-medium text-ink">Subunit</span>
              <input
                value={form.subunit}
                onChange={(event) =>
                  setForm((current) => ({ ...current, subunit: event.target.value }))
                }
                placeholder="Optional"
                className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              />
            </label>
          </div>

          <AdminPermissionsEditor
            selected={form.permissions}
            onChange={(permissions) =>
              setForm((current) => ({ ...current, permissions }))
            }
          />

          <div className="flex flex-wrap justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-surface/70"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={
                saving ||
                !form.full_name.trim() ||
                !form.email.trim() ||
                form.password.length < 12
              }
              className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Creating..." : "Create admin"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
