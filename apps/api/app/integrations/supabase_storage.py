"""Supabase Storage uploads via service_role. Reporters never call this directly."""

from __future__ import annotations

import urllib.error
import urllib.request

from app.exceptions.base import AppError


class StorageError(AppError):
    """Supabase Storage operation failed."""


class StorageUploadError(StorageError):
    """Supabase Storage upload failed."""


class StorageDeleteError(StorageError):
    """Supabase Storage delete failed."""


def upload_object(
    *,
    supabase_url: str,
    service_role_key: str,
    bucket: str,
    object_path: str,
    content: bytes,
    content_type: str,
) -> None:
    encoded_path = object_path.lstrip("/")
    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{encoded_path}"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": content_type,
        "x-upsert": "false",
    }
    req = urllib.request.Request(
        url,
        data=content,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status not in (200, 201):
                raise StorageUploadError(
                    "Storage upload returned an unexpected status.",
                    context={"status": response.status},
                )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StorageUploadError(
            f"Storage upload failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise StorageUploadError(
            "Storage upload could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc


def delete_object(
    *,
    supabase_url: str,
    service_role_key: str,
    bucket: str,
    object_path: str,
) -> None:
    encoded_path = object_path.lstrip("/")
    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{encoded_path}"
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status not in (200, 204):
                raise StorageDeleteError(
                    "Storage delete returned an unexpected status.",
                    context={"status": response.status},
                )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StorageDeleteError(
            f"Storage delete failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise StorageDeleteError(
            "Storage delete could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
