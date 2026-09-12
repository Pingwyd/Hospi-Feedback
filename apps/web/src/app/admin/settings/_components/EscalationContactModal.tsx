"use client";

import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { EscalationContact, EscalationContactInput } from "@/lib/api/admin-settings";

type EscalationContactModalProps = {
  open: boolean;
  mode: "create" | "edit";
  contact: EscalationContact | null;
  saving: boolean;
  onCancel: () => void;
  onSave: (input: EscalationContactInput) => void;
};

const EMPTY_FORM: EscalationContactInput = {
  name: "",
  role_label: "",
  contact_email: "",
  contact_phone: "",
};

export function EscalationContactModal({
  open,
  mode,
  contact,
  saving,
  onCancel,
  onSave,
}: EscalationContactModalProps) {
  const titleId = "escalation-contact-modal-title";
  const firstFieldRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState<EscalationContactInput>(EMPTY_FORM);

  useEffect(() => {
    if (!open) {
      return;
    }
    if (mode === "edit" && contact) {
      setForm({
        name: contact.name,
        role_label: contact.role_label,
        contact_email: contact.contact_email ?? "",
        contact_phone: contact.contact_phone ?? "",
      });
    } else {
      setForm(EMPTY_FORM);
    }
    firstFieldRef.current?.focus();
  }, [open, mode, contact]);

  if (!open) {
    return null;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = form.contact_email?.trim() ?? "";
    const phone = form.contact_phone?.trim() ?? "";
    onSave({
      name: form.name.trim(),
      role_label: form.role_label.trim(),
      contact_email: email || null,
      contact_phone: phone || null,
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/40 px-4"
      role="presentation"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="w-full max-w-lg rounded-2xl border border-ink/10 bg-paper p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-3">
          <h2 id={titleId} className="text-lg font-semibold text-ink">
            {mode === "create" ? "Add escalation contact" : "Edit escalation contact"}
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
              Name<span className="text-brass">*</span>
            </span>
            <input
              ref={firstFieldRef}
              value={form.name}
              onChange={(event) =>
                setForm((current) => ({ ...current, name: event.target.value }))
              }
              required
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">
              Role label<span className="text-brass">*</span>
            </span>
            <input
              value={form.role_label}
              onChange={(event) =>
                setForm((current) => ({ ...current, role_label: event.target.value }))
              }
              required
              placeholder="e.g. Unit Chaplain, HR Liaison"
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">Contact email</span>
            <input
              type="email"
              value={form.contact_email ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  contact_email: event.target.value,
                }))
              }
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

          <label className="block">
            <span className="mb-1 text-sm font-medium text-ink">Contact phone</span>
            <input
              type="tel"
              value={form.contact_phone ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  contact_phone: event.target.value,
                }))
              }
              className="w-full rounded-lg border border-ink/15 bg-surface/80 px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>

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
                saving || !form.name.trim() || !form.role_label.trim()
              }
              className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-paper hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : mode === "create" ? "Add contact" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
