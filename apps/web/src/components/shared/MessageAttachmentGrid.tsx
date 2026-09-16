"use client";

import { ChatImageAttachment } from "@/components/shared/ChatImageAttachment";

type AttachmentLike = {
  id: string;
  preview_url: string;
};

type MessageAttachmentGridProps = {
  attachments: AttachmentLike[];
  altPrefix: string;
  authMode?: "session" | "admin";
};

export function MessageAttachmentGrid({
  attachments,
  altPrefix,
  authMode = "session",
}: MessageAttachmentGridProps) {
  if (attachments.length === 0) {
    return null;
  }

  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {attachments.map((attachment, index) => (
        <li key={attachment.id}>
          <ChatImageAttachment
            previewUrl={attachment.preview_url}
            alt={`${altPrefix}${attachments.length > 1 ? ` ${index + 1}` : ""}`}
            authMode={authMode}
            compact
          />
        </li>
      ))}
    </ul>
  );
}
