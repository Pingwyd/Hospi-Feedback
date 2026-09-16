"use client";

import { AlertTriangle, ImageIcon } from "lucide-react";
import { useState } from "react";

import { ImageLightboxModal } from "@/components/shared/ImageLightboxModal";
import { useAttachmentBlobUrl } from "@/lib/hooks/useAttachmentBlobUrl";

type ChatImageAttachmentProps = {
  previewUrl: string;
  alt: string;
  authMode?: "session" | "admin";
  compact?: boolean;
};

export function ChatImageAttachment({
  previewUrl,
  alt,
  authMode = "session",
  compact = false,
}: ChatImageAttachmentProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const { src, failed, loading } = useAttachmentBlobUrl(previewUrl, authMode);

  if (failed) {
    return (
      <div
        role="img"
        aria-label={`${alt} unavailable`}
        className="mt-2 flex max-w-[10rem] items-center gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-xs text-ink"
      >
        <AlertTriangle className="shrink-0 text-brass" size={14} aria-hidden />
        <span>Image unavailable</span>
      </div>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setLightboxOpen(true)}
        disabled={loading || !src}
        className={`group block max-w-[10rem] overflow-hidden rounded-xl border border-ink/10 bg-ink/5 text-left shadow-sm transition hover:border-sage/40 hover:ring-2 hover:ring-sage/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage disabled:opacity-60 ${compact ? "mt-0" : "mt-2"}`}
        aria-label={`View full size: ${alt}`}
      >
        {loading || !src ? (
          <div className="skeleton-shimmer aspect-square w-40" aria-hidden />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt=""
            aria-hidden
            className="aspect-square h-40 w-40 object-cover transition group-hover:opacity-95"
          />
        )}
        <span className="flex items-center gap-1.5 px-2 py-1.5 text-[11px] font-medium text-ink/60">
          <ImageIcon size={12} aria-hidden />
          Tap to enlarge
        </span>
      </button>
      <ImageLightboxModal
        open={lightboxOpen}
        previewUrl={previewUrl}
        alt={alt}
        authMode={authMode}
        onClose={() => setLightboxOpen(false)}
      />
    </>
  );
}
