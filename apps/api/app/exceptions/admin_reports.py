"""Domain errors for admin report triage endpoints."""


class RecusalBlockedError(Exception):
    """Hard recusal block: admin is linked on the report."""


class RecusalConfirmationRequiredError(Exception):
    """Soft recusal warn: confirm_recusal_override required to proceed."""


class HohRoleRequiredError(Exception):
    """Action restricted to Head of Hospi role."""


class AdminReportValidationError(Exception):
    """Invalid admin report request payload."""
