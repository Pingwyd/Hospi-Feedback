"use client";

import { X } from "lucide-react";
import { useEffect, useId, useRef } from "react";

import { AttachmentPreview } from "@/components/shared/AttachmentPreview";

type ImageLightboxModalProps = {
  open: boolean;
  previewUrl: string;
  alt: string;
  authMode?: "session" | "admin" | "none";
  onClose: () => void;
};

export function ImageLightboxModal({
  open,
  previewUrl,
  alt,
  authMode = "session",
  onClose,
}: ImageLightboxModalProps) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    closeRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const resolvedAuth = authMode === "none" ? "session" : authMode;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-scrim/70 px-4 py-8"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative flex max-h-[min(90vh,900px)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-ink/10 bg-paper shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 border-b border-ink/10 px-4 py-3">
          <h2 id={titleId} className="text-sm font-semibold text-ink">
            {alt}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-ink/60 hover:bg-ink/5 hover:text-ink"
            aria-label="Close full size photo"
          >
            <X size={20} aria-hidden />
          </button>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center overflow-auto p-4">
          <AttachmentPreview
            previewUrl={previewUrl}
            alt={alt}
            authMode={resolvedAuth}
            className="max-h-[min(75vh,800px)] w-auto max-w-full rounded-lg object-contain"
          />
        </div>
      </div>
    </div>
  );
}
