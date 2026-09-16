import type { AttachmentSummary } from "@/lib/api/reports";

export const PHOTO_PLACEHOLDER = "Photo attached";

export function messageAttachments(message: {
  attachment?: AttachmentSummary | null;
  attachments?: AttachmentSummary[] | null;
}): AttachmentSummary[] {
  if (message.attachments && message.attachments.length > 0) {
    return message.attachments;
  }
  if (message.attachment) {
    return [message.attachment];
  }
  return [];
}

export function shouldShowMessageText(message: {
  content: string;
  attachment?: AttachmentSummary | null;
  attachments?: AttachmentSummary[] | null;
}): boolean {
  const attachments = messageAttachments(message);
  if (message.content !== PHOTO_PLACEHOLDER) {
    return true;
  }
  return attachments.length === 0;
}

export function attachmentsMatch(
  left: AttachmentSummary[],
  right: AttachmentSummary[],
): boolean {
  if (left.length !== right.length) {
    return false;
  }
  for (let index = 0; index < left.length; index += 1) {
    if (
      left[index].id !== right[index].id ||
      left[index].preview_url !== right[index].preview_url
    ) {
      return false;
    }
  }
  return true;
}
