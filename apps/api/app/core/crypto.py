"""AES-GCM helpers for reversible admin Telegram chat ids.

This is not a one-way hash. Reporter-side Telegram identifiers must never
go through this module.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.exceptions.crypto import CryptoInputError, DecryptionError, EncryptionKeyError

ENV_KEY_NAME = "TELEGRAM_CHAT_ID_ENCRYPTION_KEY"
AES256_KEY_BYTES = 32
GCM_NONCE_BYTES = 12
# Binds ciphertext to this column so a token cannot be reused for another field.
TELEGRAM_CHAT_ID_AAD = b"hospi.v1.telegram_chat_id"


def generate_aes256_key_b64() -> str:
    """Return a new 32-byte AES key as standard base64 for .env files."""
    return base64.b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")


def load_encryption_key(
    environ: Mapping[str, str] | None = None,
    *,
    env_name: str = ENV_KEY_NAME,
) -> bytes:
    source = os.environ if environ is None else environ
    raw = (source.get(env_name) or "").strip()
    if not raw:
        raise EncryptionKeyError(
            f"{env_name} is missing. Set a 32-byte AES key as base64.",
            context={"env_name": env_name},
        )
    try:
        key = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise EncryptionKeyError(
            f"{env_name} is not valid base64.",
            context={"env_name": env_name},
        ) from exc
    if len(key) != AES256_KEY_BYTES:
        raise EncryptionKeyError(
            f"{env_name} must decode to {AES256_KEY_BYTES} bytes (AES-256).",
            context={"env_name": env_name, "decoded_length": len(key)},
        )
    return key


def encrypt_aes_gcm(
    plaintext: str,
    *,
    key: bytes,
    aad: bytes,
) -> str:
    """Encrypt UTF-8 plaintext. Return base64(nonce + ciphertext_and_tag)."""
    if not plaintext:
        raise CryptoInputError("Refusing to encrypt an empty value.")
    nonce = os.urandom(GCM_NONCE_BYTES)
    token = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.b64encode(nonce + token).decode("ascii")


def decrypt_aes_gcm(
    token_b64: str,
    *,
    key: bytes,
    aad: bytes,
) -> str:
    """Decrypt a token produced by encrypt_aes_gcm."""
    if not token_b64:
        raise DecryptionError("Ciphertext is empty.")
    try:
        blob = base64.b64decode(token_b64, validate=True)
    except Exception as exc:
        raise DecryptionError("Ciphertext is not valid base64.") from exc
    if len(blob) <= GCM_NONCE_BYTES:
        raise DecryptionError("Ciphertext is too short to contain a nonce.")
    nonce, body = blob[:GCM_NONCE_BYTES], blob[GCM_NONCE_BYTES:]
    try:
        plaintext = AESGCM(key).decrypt(nonce, body, aad)
    except InvalidTag as exc:
        raise DecryptionError("Ciphertext failed authentication.") from exc
    return plaintext.decode("utf-8")


def encrypt_telegram_chat_id(
    chat_id: str,
    *,
    key: bytes | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    resolved = key if key is not None else load_encryption_key(environ)
    return encrypt_aes_gcm(chat_id, key=resolved, aad=TELEGRAM_CHAT_ID_AAD)


def decrypt_telegram_chat_id(
    token_b64: str,
    *,
    key: bytes | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    resolved = key if key is not None else load_encryption_key(environ)
    return decrypt_aes_gcm(token_b64, key=resolved, aad=TELEGRAM_CHAT_ID_AAD)
