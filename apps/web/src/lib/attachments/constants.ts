const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export const REPORT_ATTACHMENT_MAX_BYTES = 5 * 1024 * 1024;

export const REPORT_ATTACHMENT_ACCEPT = "image/jpeg,image/png,image/webp";

export function formatMaxAttachmentSize(): string {
  return "5 MB";
}

export function validateReportImageFile(file: File): string | null {
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
    return "Use a JPEG, PNG, or WebP image.";
  }
  if (file.size > REPORT_ATTACHMENT_MAX_BYTES) {
    return `Each photo must be ${formatMaxAttachmentSize()} or smaller. This file is too large.`;
  }
  return null;
}

export function filterValidReportImageFiles(files: File[]): {
  valid: File[];
  errors: string[];
} {
  const valid: File[] = [];
  const errors: string[] = [];
  for (const file of files) {
    const message = validateReportImageFile(file);
    if (message) {
      errors.push(`${file.name}: ${message}`);
    } else {
      valid.push(file);
    }
  }
  return { valid, errors };
}
