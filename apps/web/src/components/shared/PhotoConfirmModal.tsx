"use client";

import { Trash2, X } from "lucide-react";
import { useCallback, useEffect, useId, useRef } from "react";

export type PhotoConfirmModalItem = {
  id: string;
  previewUrl: string;
  fileName: string;
};

type PhotoConfirmModalProps = {
  open: boolean;
  items: PhotoConfirmModalItem[];
  title: string;
  description: string;
  confirmLabel: string;
  confirming?: boolean;
  confirmingLabel?: string;
  onConfirm: () => void;
  onAddMorePhotos: () => void;
  onRemoveItem: (id: string) => void;
  onCancel: () => void;
  returnFocusRef?: React.RefObject<HTMLElement | null>;
};

export function PhotoConfirmModal({
  open,
  items,
  title,
  description,
  confirmLabel,
  confirming = false,
  confirmingLabel = "Uploading...",
  onConfirm,
  onAddMorePhotos,
  onRemoveItem,
  onCancel,
  returnFocusRef,
}: PhotoConfirmModalProps) {
  const titleId = useId();
  const descId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);
  const photoCount = items.length;
  const cancelLabel =
    photoCount > 1 ? "Cancel and discard photos" : "Cancel and discard photo";

  const handleCancel = useCallback(() => {
    if (confirming) {
      return;
    }
    onCancel();
    requestAnimationFrame(() => {
      returnFocusRef?.current?.focus();
    });
  }, [confirming, onCancel, returnFocusRef]);

  useEffect(() => {
    if (!open) {
      return;
    }
    confirmRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !confirming) {
        handleCancel();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [confirming, handleCancel, open]);

  if (!open || items.length === 0) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/40 px-4 py-6"
      role="presentation"
      onClick={handleCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="flex max-h-[min(92vh,720px)] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-ink/10 bg-paper shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 border-b border-ink/10 px-5 py-4">
          <div>
            <h2 id={titleId} className="text-lg font-semibold text-ink">
              {title}
            </h2>
            <p id={descId} className="mt-1 text-sm text-ink/70">
              {description}
            </p>
            <p className="mt-2 text-xs font-medium text-ink/60">
              {photoCount} photo{photoCount === 1 ? "" : "s"} selected
            </p>
          </div>
          <button
            type="button"
            onClick={handleCancel}
            disabled={confirming}
            className="rounded-md p-1 text-ink/60 hover:bg-ink/5 hover:text-ink disabled:opacity-60"
            aria-label="Close photo review dialog"
          >
            <X size={18} aria-hidden />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto px-5 py-4">
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {items.map((item) => (
              <li key={item.id} className="relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={item.previewUrl}
                  alt={`Preview of ${item.fileName}`}
                  className="aspect-square w-full rounded-xl border border-ink/10 object-cover"
                />
                <button
                  type="button"
                  disabled={confirming}
                  onClick={() => onRemoveItem(item.id)}
                  className="absolute right-1.5 top-1.5 rounded-full border border-ink/10 bg-paper p-1 text-ink/70 shadow-sm hover:text-brass focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/40 disabled:opacity-60"
                  aria-label={`Remove ${item.fileName} from selection`}
                >
                  <Trash2 size={14} aria-hidden />
                </button>
                <p className="mt-1 truncate text-[11px] text-ink/60">{item.fileName}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex flex-col gap-3 border-t border-ink/10 px-5 py-4">
          <button
            ref={confirmRef}
            type="button"
            disabled={confirming || photoCount === 0}
            onClick={onConfirm}
            className="w-full rounded-lg bg-sage px-4 py-3 text-sm font-semibold text-paper hover:bg-sage/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {confirming ? confirmingLabel : confirmLabel}
          </button>
          <button
            type="button"
            disabled={confirming}
            onClick={onAddMorePhotos}
            className="self-center rounded-lg border border-ink/15 bg-paper px-3 py-2 text-xs font-medium text-ink hover:bg-surface/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/40 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Add more photos
          </button>
          <button
            type="button"
            disabled={confirming}
            onClick={handleCancel}
            className="self-center rounded-sm px-1 text-xs font-medium text-brass underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/40 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {cancelLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
