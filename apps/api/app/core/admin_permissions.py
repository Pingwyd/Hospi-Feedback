"""Permission strings stored on admin_permissions. Enforced in the API, not RLS."""

ALL_PERMISSIONS: tuple[str, ...] = (
    "view",
    "respond",
    "assign",
    "close",
    "export",
    "manage_categories",
    "manage_admins",
    "manage_escalation_contacts",
)

# HOH has the full set. Later roles will use subsets of ALL_PERMISSIONS.
HOH_PERMISSIONS: tuple[str, ...] = ALL_PERMISSIONS
