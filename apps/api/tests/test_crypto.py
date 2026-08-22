import base64

import pytest
from app.core.crypto import (
    TELEGRAM_CHAT_ID_AAD,
    decrypt_aes_gcm,
    decrypt_telegram_chat_id,
    encrypt_aes_gcm,
    encrypt_telegram_chat_id,
    generate_aes256_key_b64,
    load_encryption_key,
)
from app.exceptions.crypto import CryptoInputError, DecryptionError, EncryptionKeyError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

FABRICATED_CHAT_ID = "1000000001"


def test_generate_key_is_32_bytes() -> None:
    key = base64.b64decode(generate_aes256_key_b64())
    assert len(key) == 32


def test_load_encryption_key_from_mapping() -> None:
    encoded = generate_aes256_key_b64()
    key = load_encryption_key({"TELEGRAM_CHAT_ID_ENCRYPTION_KEY": encoded})
    assert len(key) == 32


def test_load_encryption_key_missing() -> None:
    with pytest.raises(EncryptionKeyError):
        load_encryption_key({})


def test_load_encryption_key_wrong_length() -> None:
    short = base64.b64encode(b"too-short").decode("ascii")
    with pytest.raises(EncryptionKeyError):
        load_encryption_key({"TELEGRAM_CHAT_ID_ENCRYPTION_KEY": short})


def test_encrypt_decrypt_round_trip() -> None:
    key = AESGCM.generate_key(bit_length=256)
    token = encrypt_telegram_chat_id(FABRICATED_CHAT_ID, key=key)
    assert token != FABRICATED_CHAT_ID
    assert decrypt_telegram_chat_id(token, key=key) == FABRICATED_CHAT_ID


def test_same_plaintext_yields_different_tokens() -> None:
    key = AESGCM.generate_key(bit_length=256)
    first = encrypt_telegram_chat_id(FABRICATED_CHAT_ID, key=key)
    second = encrypt_telegram_chat_id(FABRICATED_CHAT_ID, key=key)
    assert first != second


def test_wrong_aad_fails() -> None:
    key = AESGCM.generate_key(bit_length=256)
    token = encrypt_aes_gcm(FABRICATED_CHAT_ID, key=key, aad=TELEGRAM_CHAT_ID_AAD)
    with pytest.raises(DecryptionError):
        decrypt_aes_gcm(token, key=key, aad=b"other-purpose")


def test_tampered_ciphertext_fails() -> None:
    key = AESGCM.generate_key(bit_length=256)
    token = encrypt_telegram_chat_id(FABRICATED_CHAT_ID, key=key)
    blob = bytearray(base64.b64decode(token))
    blob[-1] ^= 0x01
    tampered = base64.b64encode(bytes(blob)).decode("ascii")
    with pytest.raises(DecryptionError):
        decrypt_telegram_chat_id(tampered, key=key)


def test_refuses_empty_plaintext() -> None:
    key = AESGCM.generate_key(bit_length=256)
    with pytest.raises(CryptoInputError):
        encrypt_telegram_chat_id("", key=key)
