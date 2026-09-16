/** Stored subunit slugs (spec section 4 / 7). */
export const ADMIN_SUBUNIT_VALUES = [
  "protocol",
  "welfare",
  "creative_writers",
  "follow_up",
  "pr",
] as const;

export type AdminSubunitValue = (typeof ADMIN_SUBUNIT_VALUES)[number];

const ADMIN_SUBUNIT_LABELS: Record<AdminSubunitValue, string> = {
  protocol: "Protocol",
  welfare: "Welfare",
  creative_writers: "Creative Writers",
  follow_up: "Follow-up",
  pr: "PR",
};

export const ADMIN_SUBUNIT_OPTIONS = ADMIN_SUBUNIT_VALUES.map((value) => ({
  value,
  label: ADMIN_SUBUNIT_LABELS[value],
}));

export function adminRoleRequiresSubunit(role: string): boolean {
  return role === "subunit_head" || role === "subunit_asst";
}

export function adminSubunitDisplayLabel(subunit: string): {
  label: string;
  unlisted: boolean;
} {
  if (
    (ADMIN_SUBUNIT_VALUES as readonly string[]).includes(subunit)
  ) {
    return {
      label: ADMIN_SUBUNIT_LABELS[subunit as AdminSubunitValue],
      unlisted: false,
    };
  }
  return { label: subunit, unlisted: true };
}
