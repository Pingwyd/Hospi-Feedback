"""Local-only seed: default categories plus one bootstrap HOH admin.

Refuses staging and production. Does not store reporter identifiers.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "apps" / "api"
_SCRIPTS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_API_ROOT))
sys.path.insert(0, str(_SCRIPTS_ROOT))

from app.core.environment import ensure_local_seed_allowed  # noqa: E402
from app.exceptions.environment import EnvironmentGuardError  # noqa: E402
from lib.bootstrap_admin import seed_bootstrap_hoh  # noqa: E402
from lib.categories import seed_default_categories  # noqa: E402


def _required_env(name: str, environ: Mapping[str, str]) -> str:
    value = (environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for local seed.")
    return value


def run_seed(environ: Mapping[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    try:
        ensure_local_seed_allowed(env)
    except EnvironmentGuardError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    supabase_url = _required_env("SUPABASE_URL", env)
    service_role_key = _required_env("SUPABASE_SERVICE_ROLE_KEY", env)

    inserted = seed_default_categories(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
    )
    admin_id = seed_bootstrap_hoh(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        environ=env,
    )
    print(f"Seed complete. Categories added: {len(inserted)}. HOH admin id: {admin_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_seed())
