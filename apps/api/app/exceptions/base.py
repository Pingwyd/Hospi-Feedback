"""Base exception for the API. Domain errors inherit from this."""


class AppError(Exception):
    def __init__(self, message: str, *, context: dict | None = None) -> None:
        super().__init__(message)
        self.context = context or {}
