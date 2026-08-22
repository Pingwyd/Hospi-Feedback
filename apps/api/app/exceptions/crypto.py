from app.exceptions.base import AppError


class EncryptionKeyError(AppError):
    """TELEGRAM_CHAT_ID_ENCRYPTION_KEY is missing or not a valid AES key."""


class DecryptionError(AppError):
    """Ciphertext failed authentication or could not be decoded."""


class CryptoInputError(AppError):
    """Caller passed a value that cannot be encrypted."""
