from __future__ import annotations

from collections.abc import Mapping

from app.core.admin_permissions import HOH_PERMISSIONS
from app.integrations.gotrue_admin import ensure_confirmed_email_user

from lib.postgrest import rest_get, rest_insert

DEFAULT_HOH_EMAIL = "local-hoh@example.test"
DEFAULT_HOH_NAME = "Local Bootstrap HOH"


def seed_bootstrap_hoh(
    *,
    supabase_url: str,
    service_role_key: str,
    environ: Mapping[str, str],
) -> str:
    """Create or reuse a local Auth user and a HOH admins row. Returns admin id."""
    email = (environ.get("LOCAL_HOH_EMAIL") or DEFAULT_HOH_EMAIL).strip()
    password = (environ.get("LOCAL_HOH_PASSWORD") or "").strip()
    full_name = (environ.get("LOCAL_HOH_FULL_NAME") or DEFAULT_HOH_NAME).strip()
    if not password:
        raise RuntimeError(
            "LOCAL_HOH_PASSWORD is required for local seed. "
            "Do not use a production password."
        )

    user_id = ensure_confirmed_email_user(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        email=email,
        password=password,
    )

    existing = rest_get(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        table="admins",
        query={"select": "id", "id": f"eq.{user_id}"},
    )
    if not existing:
        rest_insert(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            table="admins",
            row={
                "id": user_id,
                "full_name": full_name,
                "role": "hoh",
                "active": True,
            },
        )

    held = rest_get(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        table="admin_permissions",
        query={"select": "permission", "admin_id": f"eq.{user_id}"},
    )
    have = {str(row["permission"]) for row in held if "permission" in row}
    for permission in HOH_PERMISSIONS:
        if permission in have:
            continue
        rest_insert(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            table="admin_permissions",
            row={"admin_id": user_id, "permission": permission},
        )
    return user_id
