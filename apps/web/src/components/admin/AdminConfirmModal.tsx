"use client";

import { AlertTriangle, X } from "lucide-react";
import { useEffect, useId, useRef } from "react";

type AdminConfirmModalProps = {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  returnFocusRef?: React.RefObject<HTMLElement | null>;
};

export function AdminConfirmModal({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  confirming = false,
  onConfirm,
  onCancel,
  returnFocusRef,
}: AdminConfirmModalProps) {
  const titleId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      confirmRef.current?.focus();
    }
  }, [open]);

  function handleCancel() {
    onCancel();
    requestAnimationFrame(() => {
      returnFocusRef?.current?.focus();
    });
  }

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/40 px-4"
      role="presentation"
      onClick={handleCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="w-full max-w-md rounded-2xl border border-brass/30 bg-paper p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 shrink-0 text-brass" size={20} />
            <div>
              <h2 id={titleId} className="text-lg font-semibold text-ink">
                {title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-ink/80">{message}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            disabled={confirming}
            className="rounded-md p-1 text-ink/60 hover:bg-ink/5 hover:text-ink disabled:opacity-60"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>
        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={handleCancel}
            disabled={confirming}
            className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-surface/70 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={onConfirm}
            disabled={confirming}
            className="rounded-lg bg-brass px-4 py-2 text-sm font-semibold text-paper hover:bg-brass/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {confirming ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
