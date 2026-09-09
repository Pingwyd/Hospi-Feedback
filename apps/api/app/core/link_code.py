"""One-time Telegram link code generation and hashing."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

LINK_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LINK_CODE_LENGTH = 12
LINK_CODE_PATTERN = re.compile(rf"^[{LINK_CODE_ALPHABET}]{{{LINK_CODE_LENGTH}}}$")


def generate_link_code() -> str:
    return "".join(secrets.choice(LINK_CODE_ALPHABET) for _ in range(LINK_CODE_LENGTH))


def is_valid_link_code_format(code: str) -> bool:
    return bool(LINK_CODE_PATTERN.fullmatch(code.strip().upper()))


def normalize_link_code(code: str) -> str:
    return code.strip().upper()


def hash_link_code(code: str) -> str:
    normalized = normalize_link_code(code)
    return hashlib.sha256(normalized.encode()).hexdigest()


def link_code_matches_hash(code: str, stored_hash_hex: str) -> bool:
    submitted = hashlib.sha256(normalize_link_code(code).encode()).digest()
    try:
        stored = bytes.fromhex(stored_hash_hex)
    except ValueError:
        return False
    return hmac.compare_digest(submitted, stored)
