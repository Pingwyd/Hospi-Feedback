export const tokens = {
  ink: "#16241F",
  paper: "#F3EFE6",
  brass: "#A6803C",
  sage: "#6B8F71",
} as const;

export function siteUrl(): string {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}
