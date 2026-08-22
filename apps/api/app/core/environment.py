"""ENVIRONMENT gates for local-only tooling (seed, destructive resets)."""

from __future__ import annotations

import os
from collections.abc import Mapping

from app.exceptions.environment import EnvironmentGuardError

LOCAL_SEED_ENVIRONMENTS = frozenset({"local", "development", "dev", "test"})
BLOCKED_SEED_ENVIRONMENTS = frozenset({"production", "prod", "staging", "stage"})


def get_environment(environ: Mapping[str, str] | None = None) -> str:
    source = os.environ if environ is None else environ
    return (source.get("ENVIRONMENT") or "").strip().lower()


def ensure_local_seed_allowed(environ: Mapping[str, str] | None = None) -> str:
    """Allow seed only on an explicit local-dev environment. Fail closed otherwise."""
    env = get_environment(environ)
    if not env:
        raise EnvironmentGuardError(
            "ENVIRONMENT is required. Seed will not run without an explicit value."
        )
    if env in BLOCKED_SEED_ENVIRONMENTS:
        raise EnvironmentGuardError(
            f"Seed is blocked for ENVIRONMENT={env}.",
            context={"environment": env},
        )
    if env not in LOCAL_SEED_ENVIRONMENTS:
        raise EnvironmentGuardError(
            f"Seed is blocked for unknown ENVIRONMENT={env}. "
            f"Allowed: {', '.join(sorted(LOCAL_SEED_ENVIRONMENTS))}.",
            context={"environment": env},
        )
    return env
