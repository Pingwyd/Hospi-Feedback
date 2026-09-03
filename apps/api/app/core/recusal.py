"""Recusal checks for admin actions on reports naming a member (spec section 9).

Pure function only: no request context, no audit_log, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RecusalResult = Literal["blocked", "warn", "clear"]


@dataclass(frozen=True)
class RecusalAdmin:
    id: str
    full_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecusalReport:
    reported_member_name: str | None
    reported_member_admin_id: str | None


def check_recusal(admin: RecusalAdmin, report: RecusalReport) -> RecusalResult:
    """Return blocked, warn, or clear for an admin acting on a report.

    blocked: report is linked to this admin via reported_member_admin_id.
    warn: unlinked and reported_member_name contains full_name or an alias.
    clear: linked to another admin, or no name match, or no reported name.
    """
    linked_admin_id = report.reported_member_admin_id
    if linked_admin_id is not None:
        if linked_admin_id == admin.id:
            return "blocked"
        return "clear"

    reported_name = (report.reported_member_name or "").strip()
    if not reported_name:
        return "clear"

    haystack = reported_name.casefold()
    needles = (admin.full_name, *admin.aliases)
    for needle in needles:
        normalized = needle.strip()
        if normalized and normalized.casefold() in haystack:
            return "warn"
    return "clear"
