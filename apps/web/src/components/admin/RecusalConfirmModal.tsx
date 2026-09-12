"use client";

import { AlertTriangle, X } from "lucide-react";
import { useEffect, useRef } from "react";

type RecusalConfirmModalProps = {
  open: boolean;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  returnFocusRef?: React.RefObject<HTMLElement | null>;
};

export function RecusalConfirmModal({
  open,
  message,
  onConfirm,
  onCancel,
  returnFocusRef,
}: RecusalConfirmModalProps) {
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      role="presentation"
      onClick={handleCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="recusal-dialog-title"
        className="w-full max-w-md rounded-2xl border border-brass/30 bg-paper p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 shrink-0 text-brass" size={20} />
            <div>
              <h2 id="recusal-dialog-title" className="text-lg font-semibold text-ink">
                Recusal warning
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-ink/80">{message}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            className="rounded-md p-1 text-ink/60 hover:bg-ink/5 hover:text-ink"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>
        <p className="mb-5 text-sm text-ink/70">
          Confirm only if you have reviewed the conflict and accept responsibility for
          this action.
        </p>
        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={handleCancel}
            className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-white/70"
          >
            Cancel
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={onConfirm}
            className="rounded-lg bg-brass px-4 py-2 text-sm font-semibold text-paper hover:bg-brass/90"
          >
            Confirm override
          </button>
        </div>
      </div>
    </div>
  );
}
