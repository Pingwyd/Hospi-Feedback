"use client";

import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";

import { getAdminAccessToken } from "@/lib/auth/admin-session";

type AttachmentPreviewProps = {
  previewUrl: string;
  alt: string;
  className?: string;
  authMode?: "session" | "admin";
};

async function loadAdminBlobUrl(previewUrl: string): Promise<string> {
  const token = getAdminAccessToken();
  if (!token) {
    throw new Error("Admin session required.");
  }
  const response = await fetch(previewUrl, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("Attachment fetch failed.");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export function AttachmentPreview({
  previewUrl,
  alt,
  className = "mt-2 max-h-64 w-full rounded-lg border border-ink/10 object-contain",
  authMode = "session",
}: AttachmentPreviewProps) {
  const [failed, setFailed] = useState(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (authMode !== "admin") {
      return;
    }
    let active = true;
    let objectUrl: string | null = null;
    setFailed(false);
    setBlobUrl(null);
    void loadAdminBlobUrl(previewUrl)
      .then((url) => {
        if (!active) {
          URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setBlobUrl(url);
      })
      .catch(() => {
        if (active) {
          setFailed(true);
        }
      });
    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [authMode, previewUrl]);

  if (failed) {
    return (
      <div
        role="img"
        aria-label={`${alt} unavailable`}
        className="mt-2 flex items-center gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-sm text-ink"
      >
        <AlertTriangle className="shrink-0 text-brass" size={16} aria-hidden />
        <span>Image could not be loaded.</span>
      </div>
    );
  }

  if (authMode === "admin") {
    if (!blobUrl) {
      return (
        <div
          className="mt-2 skeleton-shimmer h-40 w-full max-w-sm rounded-lg"
          aria-hidden
        />
      );
    }
    return (
      // Proxy and blob URLs are session-scoped; next/image cannot authenticate these sources.
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={blobUrl}
        alt={alt}
        className={className}
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={previewUrl}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
