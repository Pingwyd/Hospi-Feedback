from __future__ import annotations

from app.core.default_categories import DEFAULT_CATEGORY_NAMES

from lib.postgrest import rest_get, rest_insert


def seed_default_categories(*, supabase_url: str, service_role_key: str) -> list[str]:
    """Insert missing default categories. Returns names that were inserted."""
    existing = rest_get(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        table="categories",
        query={"select": "name"},
    )
    have = {str(row["name"]) for row in existing if "name" in row}
    inserted: list[str] = []
    for name in DEFAULT_CATEGORY_NAMES:
        if name in have:
            continue
        rest_insert(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            table="categories",
            row={"name": name, "active": True},
        )
        inserted.append(name)
    return inserted
