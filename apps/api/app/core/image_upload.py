"""Validate reporter image uploads and strip EXIF before storage."""

from __future__ import annotations

import io

import filetype
from PIL import Image, UnidentifiedImageError

from app.exceptions.reports import AttachmentRejectedError

ALLOWED_IMAGE_MIMES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)
MIME_TO_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MIME_TO_PIL_FORMAT: dict[str, str] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def prepare_image_for_storage(data: bytes, *, max_bytes: int) -> tuple[bytes, str, str]:
    """Return stripped bytes, mime type, and file extension."""
    if not data:
        raise AttachmentRejectedError("Empty file is not allowed.")
    if len(data) > max_bytes:
        raise AttachmentRejectedError("File exceeds the maximum allowed size.")

    detected = filetype.guess(data)
    if detected is None or detected.mime not in ALLOWED_IMAGE_MIMES:
        raise AttachmentRejectedError("Only JPEG, PNG, and WebP images are allowed.")

    mime = detected.mime
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError) as exc:
        raise AttachmentRejectedError(
            "Only JPEG, PNG, and WebP images are allowed.",
        ) from exc

    if mime == "image/jpeg" and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    elif mime == "image/png" and image.mode not in {"RGB", "RGBA", "L", "LA"}:
        image = image.convert("RGBA")
    elif mime == "image/webp" and image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")

    output = io.BytesIO()
    save_format = MIME_TO_PIL_FORMAT[mime]
    save_kwargs: dict[str, object] = {}
    if save_format == "JPEG":
        save_kwargs["quality"] = 85
        save_kwargs["optimize"] = True
    image.save(output, format=save_format, **save_kwargs)
    stripped = output.getvalue()
    extension = MIME_TO_EXTENSION[mime]
    return stripped, mime, extension
