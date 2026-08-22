import pytest
from app.core.environment import ensure_local_seed_allowed
from app.exceptions.environment import EnvironmentGuardError


@pytest.mark.parametrize("env", ["local", "development", "dev", "test"])
def test_seed_allowed_for_local_envs(env: str) -> None:
    assert ensure_local_seed_allowed({"ENVIRONMENT": env}) == env


@pytest.mark.parametrize(
    "env",
    ["production", "prod", "staging", "stage", "PRODUCTION"],
)
def test_seed_blocked_for_staging_and_production(env: str) -> None:
    with pytest.raises(EnvironmentGuardError):
        ensure_local_seed_allowed({"ENVIRONMENT": env})


def test_seed_blocked_when_environment_missing() -> None:
    with pytest.raises(EnvironmentGuardError):
        ensure_local_seed_allowed({})


def test_seed_blocked_for_unknown_environment() -> None:
    with pytest.raises(EnvironmentGuardError):
        ensure_local_seed_allowed({"ENVIRONMENT": "qa"})
