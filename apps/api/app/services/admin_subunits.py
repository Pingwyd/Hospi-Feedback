"""Canonical admin subunit values and create-time validation."""

from __future__ import annotations

from app.exceptions.admin_reports import AdminReportValidationError

ADMIN_SUBUNITS = frozenset(
    {
        "protocol",
        "welfare",
        "creative_writers",
        "follow_up",
        "pr",
    }
)

SUBUNIT_SCOPED_ROLES = frozenset({"subunit_head", "subunit_asst"})


def validate_admin_subunit_for_create(role: str, subunit: str | None) -> str | None:
    """Return the subunit value to persist on admin create.

    Non-subunit roles must omit subunit (422 if a value is sent). Subunit-scoped
    roles require a canonical subunit enum value.
    """
    if role in SUBUNIT_SCOPED_ROLES:
        if subunit is None or not str(subunit).strip():
            raise AdminReportValidationError(
                "subunit is required for subunit_head and subunit_asst roles.",
            )
        cleaned = str(subunit).strip()
        if cleaned not in ADMIN_SUBUNITS:
            raise AdminReportValidationError(
                f"Invalid subunit. Allowed values: {', '.join(sorted(ADMIN_SUBUNITS))}."
            )
        return cleaned

    if subunit is not None and str(subunit).strip():
        raise AdminReportValidationError(
            "subunit must be omitted for roles other than subunit_head and "
            "subunit_asst.",
        )
    return None
