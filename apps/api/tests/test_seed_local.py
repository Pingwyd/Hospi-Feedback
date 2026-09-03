import importlib.util
from pathlib import Path

from app.exceptions.environment import EnvironmentGuardError

_SEED_PATH = Path(__file__).resolve().parents[3] / "infra" / "scripts" / "seed_local.py"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("hospi_seed_local", _SEED_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load seed script at {_SEED_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_seed_exits_1_on_production() -> None:
    seed = _load_seed_module()
    assert seed.run_seed({"ENVIRONMENT": "production"}) == 1


def test_run_seed_exits_1_on_staging() -> None:
    seed = _load_seed_module()
    assert seed.run_seed({"ENVIRONMENT": "staging"}) == 1


def test_run_seed_stops_before_network_when_blocked() -> None:
    seed = _load_seed_module()
    assert seed.run_seed({"ENVIRONMENT": "production"}) == 1
    try:
        seed.run_seed({"ENVIRONMENT": "local"})
    except RuntimeError as exc:
        assert "SUPABASE_URL" in str(exc)
    except EnvironmentGuardError:
        raise AssertionError("local seed should pass the env guard") from None
