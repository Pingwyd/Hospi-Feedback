"use client";

import { Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  createCategory,
  listCategories,
  updateCategory,
  type Category,
} from "@/lib/api/admin-settings";

function statusBadgeClass(active: boolean): string {
  return active
    ? "bg-sage/15 text-sage"
    : "bg-ink/10 text-ink/60";
}

export function CategoriesPanel() {
  const { hasPermission } = useAdminSession();
  const canManage = hasPermission("manage_categories");

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [mutatingId, setMutatingId] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listCategories();
      setCategories(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load categories.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCategories();
  }, [loadCategories]);

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = newName.trim();
    if (!trimmed) {
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const created = await createCategory(trimmed);
      setCategories((current) =>
        [...current, created].sort((a, b) => a.name.localeCompare(b.name)),
      );
      setNewName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create category.");
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleActive(category: Category) {
    setMutatingId(category.id);
    setError(null);
    try {
      const updated = await updateCategory(category.id, { active: !category.active });
      setCategories((current) =>
        current.map((row) => (row.id === updated.id ? updated : row)),
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not update category status.",
      );
    } finally {
      setMutatingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink">Categories</h2>
        <p className="mt-1 text-sm text-ink/60">
          Report categories used during triage and filtering.
          {!canManage ? " You have read-only access." : null}
        </p>
      </div>

      {canManage ? (
        <form
          onSubmit={handleCreate}
          className="rounded-2xl border border-ink/10 bg-white/60 p-4 shadow-sm"
        >
          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">
              New category name<span className="text-brass">*</span>
            </span>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="e.g. Welfare, Protocol, Finance"
                required
                className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              />
              <button
                type="submit"
                disabled={creating || !newName.trim()}
                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Plus size={16} />
                {creating ? "Adding..." : "Add category"}
              </button>
            </div>
          </label>
        </form>
      ) : null}

      {loading ? (
        <SkeletonCard />
      ) : error ? (
        <div
          role="alert"
          className="rounded-2xl border border-brass/30 bg-brass/10 p-4 text-sm text-ink"
        >
          {error}
        </div>
      ) : categories.length === 0 ? (
        <div className="rounded-2xl border border-ink/10 bg-white/60 p-8 text-center text-sm text-ink/60">
          No categories yet.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/60 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-ink/10 bg-paper/70 text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  {canManage ? (
                    <th className="px-4 py-3 font-medium">Actions</th>
                  ) : null}
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr
                    key={category.id}
                    className="border-b border-ink/5 hover:bg-paper/50"
                  >
                    <td className="px-4 py-3 font-medium text-ink">{category.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass(category.active)}`}
                      >
                        {category.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    {canManage ? (
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => void handleToggleActive(category)}
                          disabled={mutatingId === category.id}
                          className="rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {mutatingId === category.id
                            ? "Saving..."
                            : category.active
                              ? "Deactivate"
                              : "Reactivate"}
                        </button>
                      </td>
                    ) : null}
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
