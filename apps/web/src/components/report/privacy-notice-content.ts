/** Full privacy notice bullets (web report flow). Shared by /privacy and form summary context. */

export const PRIVACY_NOTICE_HEADING = "Privacy notice";

export const PRIVACY_NOTICE_BULLETS = [
  "We do not ask for your name, email, or login. Your report cannot be traced back to you through this website.",
  "Your ticket code is the only way to return to this thread. We cannot recover it if you lose it.",
  "On Telegram, we use a hidden code to deliver your message and prevent spam. Admins never see that code, and it is not linked to what you report.",
  "Admins who choose Telegram alerts for themselves use a separate protected setup. That does not change reporter anonymity.",
  "If you submit via Telegram and your session ends, an admin reply will not push to you automatically. Run status again with your ticket code to read replies.",
] as const;

export const PRIVACY_NOTICE_SUMMARY_LEAD =
  "We do not ask for your name, email, or login, and your report is not linked to your identity on this website.";

export const PRIVACY_NOTICE_SUMMARY_TELEGRAM =
  "If you use Telegram, your report works the same way, but you may need to check back manually for replies.";

export const PRIVACY_NOTICE_LINK_LABEL = "Read our full privacy notice";
