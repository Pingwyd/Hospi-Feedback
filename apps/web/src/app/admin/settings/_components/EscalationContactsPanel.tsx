"use client";

import { Pencil, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { ApiError } from "@/lib/api/admin-fetch";
import {
  createEscalationContact,
  listEscalationContacts,
  updateEscalationContact,
  type EscalationContact,
  type EscalationContactInput,
} from "@/lib/api/admin-settings";

import { EscalationContactModal } from "./EscalationContactModal";

function statusBadgeClass(active: boolean): string {
  return active ? "bg-sage/15 text-sage" : "bg-ink/10 text-ink/60";
}

type ModalState =
  | { mode: "closed" }
  | { mode: "create" }
  | { mode: "edit"; contact: EscalationContact };

export function EscalationContactsPanel() {
  const { hasPermission } = useAdminSession();
  const canManage = hasPermission("manage_escalation_contacts");

  const [contacts, setContacts] = useState<EscalationContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>({ mode: "closed" });
  const [saving, setSaving] = useState(false);
  const [mutatingId, setMutatingId] = useState<string | null>(null);

  const loadContacts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listEscalationContacts();
      setContacts(rows);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not load escalation contacts.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadContacts();
  }, [loadContacts]);

  async function handleSave(input: EscalationContactInput) {
    setSaving(true);
    setError(null);
    try {
      if (modal.mode === "create") {
        const created = await createEscalationContact(input);
        setContacts((current) =>
          [...current, created].sort((a, b) => a.name.localeCompare(b.name)),
        );
      } else if (modal.mode === "edit") {
        const updated = await updateEscalationContact(modal.contact.id, input);
        setContacts((current) =>
          current.map((row) => (row.id === updated.id ? updated : row)),
        );
      }
      setModal({ mode: "closed" });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : modal.mode === "create"
            ? "Could not create escalation contact."
            : "Could not update escalation contact.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleActive(contact: EscalationContact) {
    setMutatingId(contact.id);
    setError(null);
    try {
      const updated = await updateEscalationContact(contact.id, {
        active: !contact.active,
      });
      setContacts((current) =>
        current.map((row) => (row.id === updated.id ? updated : row)),
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not update escalation contact status.",
      );
    } finally {
      setMutatingId(null);
    }
  }

  const modalOpen = modal.mode !== "closed";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Escalation contacts</h2>
          <p className="mt-1 text-sm text-ink/60">
            Contacts used when escalating a report externally.
            {!canManage ? " You have read-only access." : null}
          </p>
        </div>
        {canManage ? (
          <button
            type="button"
            onClick={() => setModal({ mode: "create" })}
            className="inline-flex items-center gap-2 rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-paper hover:bg-ink/90"
          >
            <Plus size={16} />
            Add contact
          </button>
        ) : null}
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
      ) : contacts.length === 0 ? (
        <div className="rounded-2xl border border-ink/10 bg-white/60 p-8 text-center text-sm text-ink/60">
          No escalation contacts yet.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white/60 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-ink/10 bg-paper/70 text-xs uppercase tracking-wide text-ink/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Phone</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  {canManage ? (
                    <th className="px-4 py-3 font-medium">Actions</th>
                  ) : null}
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => (
                  <tr
                    key={contact.id}
                    className="border-b border-ink/5 hover:bg-paper/50"
                  >
                    <td className="px-4 py-3 font-medium text-ink">{contact.name}</td>
                    <td className="px-4 py-3 text-ink/70">{contact.role_label}</td>
                    <td className="px-4 py-3 text-ink/70">
                      {contact.contact_email ?? "N/A"}
                    </td>
                    <td className="px-4 py-3 text-ink/70">
                      {contact.contact_phone ?? "N/A"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClass(contact.active)}`}
                      >
                        {contact.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    {canManage ? (
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => setModal({ mode: "edit", contact })}
                            className="inline-flex items-center gap-1 rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper"
                          >
                            <Pencil size={14} />
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleToggleActive(contact)}
                            disabled={mutatingId === contact.id}
                            className="rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {mutatingId === contact.id
                              ? "Saving..."
                              : contact.active
                                ? "Deactivate"
                                : "Reactivate"}
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <EscalationContactModal
        open={modalOpen}
        mode={modal.mode === "edit" ? "edit" : "create"}
        contact={modal.mode === "edit" ? modal.contact : null}
        saving={saving}
        onCancel={() => setModal({ mode: "closed" })}
        onSave={(input) => void handleSave(input)}
      />
    </div>
  );
}
