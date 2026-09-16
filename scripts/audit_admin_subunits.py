"""Aggregate non-null admins.subunit values from a Supabase project.

Usage (from repo root):
  python scripts/audit_admin_subunits.py

Default env file: apps/api/.env. For staging before merge:
  set AUDIT_ENV_FILE=apps/api/.env.staging   (Windows)
  python scripts/audit_admin_subunits.py
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
_API_DIR = _REPO_ROOT / "apps" / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from app.core.settings import Settings  # noqa: E402


def main() -> int:
    env_file = os.environ.get("AUDIT_ENV_FILE", str(_API_DIR / ".env"))
    settings = Settings(_env_file=env_file)
    host = urlparse(settings.supabase_url).netloc
    print(f"env_file={env_file!r} environment={settings.environment!r} supabase_host={host!r}")

    url = settings.supabase_url.rstrip("/") + "/rest/v1/admins"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    params = {"select": "subunit", "subunit": "not.is.null"}

    try:
        response = httpx.get(url, headers=headers, params=params, timeout=30.0)
    except httpx.HTTPError as exc:
        print(f"fetch_failed={exc!r}")
        return 1

    print(f"http_status={response.status_code}")
    if response.status_code != 200:
        print(response.text[:500])
        return 1

    rows = response.json()
    counts = Counter(
        row.get("subunit") for row in rows if isinstance(row, dict) and row.get("subunit")
    )
    print(f"non_null_rows={len(rows)}")
    if not counts:
        print("(no non-null subunit values)")
        return 0

    for subunit, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {subunit!r}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
