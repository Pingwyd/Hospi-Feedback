import { Info } from "lucide-react";

import {
  PRIVACY_NOTICE_BULLETS,
  PRIVACY_NOTICE_HEADING,
} from "@/components/report/privacy-notice-content";

type PrivacyNoticeFullProps = {
  /** When true, use larger page title styling on /privacy. */
  variant?: "page" | "embedded";
};

export function PrivacyNoticeFull({ variant = "embedded" }: PrivacyNoticeFullProps) {
  const headingClass =
    variant === "page"
      ? "text-2xl font-semibold text-ink"
      : "text-sm font-semibold text-ink";

  return (
    <section
      aria-labelledby="privacy-notice-heading"
      className={
        variant === "page"
          ? "space-y-5"
          : "rounded-xl border border-sage/25 bg-sage/10 p-5"
      }
    >
      <div className="flex items-center gap-2">
        {variant === "embedded" ? (
          <Info size={18} className="text-sage" aria-hidden />
        ) : null}
        <h1 id="privacy-notice-heading" className={headingClass}>
          {PRIVACY_NOTICE_HEADING}
        </h1>
      </div>
      <ul className="space-y-3 text-sm leading-relaxed text-ink/80 md:text-base">
        {PRIVACY_NOTICE_BULLETS.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
