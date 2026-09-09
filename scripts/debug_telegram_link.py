"""Local diagnostics for Telegram /link failures. Does not print secret values."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def secret_fingerprint(raw: str) -> str:
    normalized = raw.strip()
    if not normalized:
        return "EMPTY"
    return f"len={len(normalized)} sha256={hashlib.sha256(normalized.encode()).hexdigest()[:12]}"


def main() -> int:
    root_env = load_env_file(ROOT / ".env")
    api_env = load_env_file(ROOT / "apps" / "api" / ".env")
    bot_env = load_env_file(ROOT / "apps" / "bot" / ".env")

    print("=== Env files present ===")
    print(f"root .env: { (ROOT / '.env').is_file() }")
    print(f"apps/api/.env: { (ROOT / 'apps' / 'api' / '.env').is_file() }")
    print(f"apps/bot/.env: { (ROOT / 'apps' / 'bot' / '.env').is_file() }")

    print("\n=== TELEGRAM_CHAT_ID_ENCRYPTION_KEY fingerprints (API must have this) ===")
    for label, env in [("root", root_env), ("api", api_env)]:
        print(f"{label}: {secret_fingerprint(env.get('TELEGRAM_CHAT_ID_ENCRYPTION_KEY', ''))}")

    print("\n=== BOT_SERVICE_SECRET fingerprints (must match) ===")
    for label, env in [("root", root_env), ("api", api_env), ("bot", bot_env)]:
        print(f"{label}: {secret_fingerprint(env.get('BOT_SERVICE_SECRET', ''))}")

    api_base = bot_env.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    print(f"\n=== API reachability ({api_base}) ===")
    try:
        with urllib.request.urlopen(f"{api_base}/docs", timeout=5) as resp:
            print(f"docs status: {resp.status}")
    except Exception as exc:
        print(f"API not reachable at {api_base}: {type(exc).__name__}: {exc}")
        return 1

    bot_secret = bot_env.get("BOT_SERVICE_SECRET", "").strip()
    if not bot_secret:
        print("\nBot BOT_SERVICE_SECRET is empty in apps/bot/.env")
        return 1

    print("\n=== POST /api/admin/telegram/link probe (dummy code) ===")
    payload = json.dumps(
        {"one_time_code": "AAAAAAAAAAAA", "telegram_chat_id": "123456789"}
    ).encode()
    req = urllib.request.Request(
        f"{api_base}/api/admin/telegram/link",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Bot-Service-Secret": bot_secret,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"unexpected success: {resp.status} {resp.read().decode()}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"status: {exc.code}")
        print(f"body: {body[:500]}")
        if exc.code == 401 and "Invalid bot service secret" in body:
            print("\nLikely cause: BOT_SERVICE_SECRET mismatch between bot and API.")
        elif exc.code == 503:
            print("\nLikely cause: BOT_SERVICE_SECRET missing in apps/api/.env (API not configured).")
        elif exc.code == 401 and "Invalid or expired link code" in body:
            print("\nSecret OK. Dummy code rejected as expected. Generate a fresh 12-char code.")
        elif exc.code == 422:
            print("\nLikely cause: request validation failed (check code length/format).")

    print("\n=== DB table check (telegram_link_codes) ===")
    os.chdir(ROOT / "apps" / "api")
    sys.path.insert(0, str(ROOT / "apps" / "api"))
    try:
        from app.core.settings import get_settings

        settings = get_settings()
        print(f"API settings bot secret: {secret_fingerprint(settings.bot_service_secret)}")
        enc = os.environ.get("TELEGRAM_CHAT_ID_ENCRYPTION_KEY") or api_env.get(
            "TELEGRAM_CHAT_ID_ENCRYPTION_KEY", ""
        )
        if not enc and not hasattr(settings, "telegram_chat_id_encryption_key"):
            # encryption key may live only in env for crypto module
            pass
        q = "select=id&limit=1"
        url = f"{settings.supabase_url.rstrip('/')}/rest/v1/telegram_link_codes?{q}"
        table_req = urllib.request.Request(
            url,
            headers={
                "apikey": settings.supabase_service_role_key,
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
            },
        )
        with urllib.request.urlopen(table_req, timeout=10) as resp:
            rows = json.loads(resp.read().decode())
            print(f"telegram_link_codes reachable, sample rows: {len(rows)}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"table check failed: {exc.code} {body[:300]}")
        if exc.code == 404 or "does not exist" in body.lower():
            print("\nLikely cause: migration not applied. Run supabase db reset or apply migration.")
    except Exception as exc:
        print(f"settings/db check failed: {type(exc).__name__}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
