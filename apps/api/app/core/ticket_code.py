"""Ticket code generation and hashing. Plaintext codes never touch storage or logs."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

TICKET_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
# 8 chars (~40 bits). Below spec floor; rate limit required before production.
TICKET_CODE_LENGTH = 8
TICKET_CODE_PATTERN = re.compile(rf"^[{TICKET_CODE_ALPHABET}]{{{TICKET_CODE_LENGTH}}}$")


def generate_ticket_code() -> str:
    return "".join(
        secrets.choice(TICKET_CODE_ALPHABET) for _ in range(TICKET_CODE_LENGTH)
    )


def is_valid_ticket_code_format(code: str) -> bool:
    return bool(TICKET_CODE_PATTERN.fullmatch(code))


def hash_ticket_code(code: str) -> str:
    """Return a hex SHA-256 digest for PostgREST lookup and storage."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def ticket_code_matches_hash(code: str, stored_hash_hex: str) -> bool:
    submitted = hashlib.sha256(code.encode("utf-8")).digest()
    try:
        stored = bytes.fromhex(stored_hash_hex)
    except ValueError:
        return False
    return hmac.compare_digest(submitted, stored)
