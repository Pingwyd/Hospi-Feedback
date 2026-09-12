"use client";

import { KeyRound, Plus, UserX } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  ADMIN_ROLES,
  createAdminUser,
  deactivateAdminUser,
  listAdminUsers,
  updateAdminUserPermissions,
  type AdminUser,
  type CreateAdminInput,
} from "@/lib/api/admin-settings";

import { AdminPermissionsModal } from "./AdminPermissionsModal";
import { AdminUserCreateModal } from "./AdminUserCreateModal";
import { SettingsConfirmModal } from "./SettingsConfirmModal";

function roleLabel(role: string): string {
  return ADMIN_ROLES.find((item) => item.value === role)?.label ?? role;
}

function statusBadgeClass(active: boolean): string {
  return active ? "bg-sage/15 text-sage" : "bg-ink/10 text-ink/60";
}

export function AdminUsersPanel() {
  const { profile, hasPermission } = useAdminSession();
  const canManage = hasPermission("manage_admins");

  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [permissionsAdmin, setPermissionsAdmin] = useState<AdminUser | null>(null);
  const [savingPermissions, setSavingPermissions] = useState(false);
  const [deactivateTarget, setDeactivateTarget] = useState<AdminUser | null>(null);
  const [deactivating, setDeactivating] = useState(false);

  const loadAdmins = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listAdminUsers();
      setAdmins(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load admin users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canManage) {
      void loadAdmins();
    }
  }, [canManage, loadAdmins]);

  if (!canManage) {
    return null;
  }

  async function handleCreate(input: CreateAdminInput) {
    setCreating(true);
    setError(null);
    try {
      const created = await createAdminUser(input);
      setAdmins((current) =>
        [...current, { ...created, active: created.active ?? true }].sort((a, b) =>
          a.full_name.localeCompare(b.full_name),
        ),
      );
      setCreateOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create admin user.");
    } finally {
      setCreating(false);
    }
  }

  async function handleSavePermissions(permissions: string[]) {
    if (!permissionsAdmin) {
      return;
    }
    setSavingPermissions(true);
    setError(null);
    try {
      const updated = await updateAdminUserPermissions(
        permissionsAdmin.id,
        permissions,
      );
      setAdmins((current) =>
        current.map((row) =>
          row.id === updated.id ? { ...row, permissions: updated.permissions } : row,
        ),
      );
      setPermissionsAdmin(null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not update admin permissions.",
      );
    } finally {
      setSavingPermissions(false);
    }
  }

  async function handleDeactivate() {
    if (!deactivateTarget) {
      return;
    }
    setDeactivating(true);
    setError(null);
    try {
      const updated = await deactivateAdminUser(deactivateTarget.id);
      setAdmins((current) =>
        current.map((row) =>
          row.id === deactivateTarget.id
            ? { ...row, active: updated.active ?? false }
            : row,
        ),
      );
      setDeactivateTarget(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not deactivate admin user.");
    } finally {
      setDeactivating(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Admin users</h2>
          <p className="mt-1 text-sm text-ink/60">
            Create admins, adjust permissions, and deactivate accounts.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-paper hover:bg-ink/90"
        >
          <Plus size={16} />
          Create admin
        </button>
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
      ) : admins.length === 0 ? (
        <div className="rounded-2xl border border-ink/10 bg-white/60 p-8 text-center text-sm text-ink/60">
          No admin users found.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/60 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-ink/10 bg-paper/70 text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Full name</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Subunit</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Permissions</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((admin) => {
                  const isSelf = profile?.id === admin.id;
                  return (
                    <tr
                      key={admin.id}
                      className="border-b border-ink/5 hover:bg-paper/50"
                    >
                      <td className="px-4 py-3 font-medium text-ink">
                        {admin.full_name}
                        {isSelf ? (
                          <span className="ml-2 text-xs font-normal text-ink/50">
                            (you)
                          </span>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 text-ink/70">{roleLabel(admin.role)}</td>
                      <td className="px-4 py-3 text-ink/70">
                        {admin.subunit ?? "N/A"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass(admin.active)}`}
                        >
                          {admin.active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex max-w-xs flex-wrap gap-1">
                          {admin.permissions.length > 0 ? (
                            admin.permissions.map((permission) => (
                              <span
                                key={permission}
                                className="rounded-full bg-ink/5 px-2 py-0.5 text-xs text-ink/70"
                              >
                                {permission}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-ink/50">None</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => setPermissionsAdmin(admin)}
                            disabled={!admin.active}
                            className="inline-flex items-center gap-1 rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            <KeyRound size={14} />
                            Permissions
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeactivateTarget(admin)}
                            disabled={!admin.active || isSelf}
                            title={
                              isSelf
                                ? "You cannot deactivate your own account."
                                : undefined
                            }
                            className="inline-flex items-center gap-1 rounded-lg border border-brass/30 px-3 py-1.5 text-xs font-medium text-brass hover:bg-brass/10 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            <UserX size={14} />
                            Deactivate
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <AdminUserCreateModal
        open={createOpen}
        saving={creating}
        onCancel={() => setCreateOpen(false)}
        onSave={(input) => void handleCreate(input)}
      />

      <AdminPermissionsModal
        open={permissionsAdmin !== null}
        admin={permissionsAdmin}
        saving={savingPermissions}
        onCancel={() => setPermissionsAdmin(null)}
        onSave={(permissions) => void handleSavePermissions(permissions)}
      />

      <SettingsConfirmModal
        open={deactivateTarget !== null}
        title="Deactivate admin user"
        message={
          deactivateTarget
            ? `Deactivate ${deactivateTarget.full_name}? They will lose access immediately. This is a soft offboarding (active = false), not a hard delete.`
            : ""
        }
        confirmLabel="Deactivate admin"
        confirming={deactivating}
        onCancel={() => setDeactivateTarget(null)}
        onConfirm={() => void handleDeactivate()}
      />
    </div>
  );
}
