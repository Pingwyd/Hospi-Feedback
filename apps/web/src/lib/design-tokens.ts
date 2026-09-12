/** Light-mode defaults; CSS custom properties in globals.css drive runtime theming. */
export const tokens = {
  ink: "#16241F",
  paper: "#F3EFE6",
  brass: "#A6803C",
  sage: "#6B8F71",
  surface: "#FFFFFF",
} as const;

export const darkTokens = {
  ink: "#E8E4DB",
  paper: "#121A17",
  brass: "#D4A855",
  sage: "#9DBEA4",
  surface: "#1C2420",
} as const;

export function siteUrl(): string {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}
