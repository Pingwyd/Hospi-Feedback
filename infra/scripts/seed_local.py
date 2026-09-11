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

from app.core.environment import ensure_local_seed_allowed
from app.exceptions.environment import EnvironmentGuardError
from lib.bootstrap_admin import seed_bootstrap_hoh
from lib.categories import seed_default_categories


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip().strip("'").strip('"')
    return values


def load_dotenv_files() -> None:
    """Fill missing os.environ keys from repo and API .env files. Process env wins."""
    for path in (_REPO_ROOT / ".env", _API_ROOT / ".env"):
        for key, value in _parse_env_file(path).items():
            os.environ.setdefault(key, value)


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
    load_dotenv_files()
    raise SystemExit(run_seed())
