import { Info } from "lucide-react";

export function PrivacyNotice() {
  return (
    <section
      aria-labelledby="privacy-notice-heading"
      className="rounded-xl border border-sage/25 bg-sage/10 p-5"
    >
      <div className="mb-3 flex items-center gap-2">
        <Info size={18} className="text-sage" aria-hidden />
        <h2 id="privacy-notice-heading" className="text-sm font-semibold text-ink">
          Privacy notice
        </h2>
      </div>
      <ul className="space-y-2 text-sm leading-relaxed text-ink/80">
        <li>
          We do not ask for your name, email, or login. Your report cannot be traced back
          to you through this website.
        </li>
        <li>
          Your ticket code is the only way to return to this thread. We cannot recover it
          if you lose it.
        </li>
        <li>
          On Telegram, messages are tied to a chat id for routing and rate limiting only.
          That id is hashed, never shown to admins, and never linked to report content.
        </li>
        <li>
          Admins who link Telegram for notifications store an encrypted chat id so pushes
          can be delivered. That is separate from reporter anonymity.
        </li>
        <li>
          If you submit via Telegram and your session ends, an admin reply will not push
          to you automatically. Run status again with your ticket code to read replies.
        </li>
      </ul>
    </section>
  );
}
