"use client";

import { useEffect, useState } from "react";

import { getAdminAccessToken } from "@/lib/auth/admin-session";

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

type AuthMode = "session" | "admin" | "none";

/**
 * Resolves a display URL for attachment images. Session mode uses the proxy URL directly;
 * admin mode fetches with bearer auth and returns a blob URL.
 */
export function useAttachmentBlobUrl(previewUrl: string, authMode: AuthMode): {
  src: string | null;
  failed: boolean;
  loading: boolean;
} {
  const [failed, setFailed] = useState(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(authMode === "admin");

  useEffect(() => {
    if (authMode === "none") {
      setBlobUrl(previewUrl);
      setLoading(false);
      setFailed(false);
      return;
    }

    if (authMode === "session") {
      setBlobUrl(previewUrl);
      setLoading(false);
      setFailed(false);
      return;
    }

    let active = true;
    let objectUrl: string | null = null;
    setFailed(false);
    setBlobUrl(null);
    setLoading(true);

    void loadAdminBlobUrl(previewUrl)
      .then((url) => {
        if (!active) {
          URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setBlobUrl(url);
        setLoading(false);
      })
      .catch(() => {
        if (active) {
          setFailed(true);
          setLoading(false);
        }
      });

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [authMode, previewUrl]);

  return { src: blobUrl, failed, loading };
}
