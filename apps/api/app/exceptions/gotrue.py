from app.exceptions.base import AppError


class GoTrueAdminError(AppError):
    """Supabase Auth admin API call failed."""
