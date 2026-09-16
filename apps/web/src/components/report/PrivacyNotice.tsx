import Link from "next/link";
import { Info } from "lucide-react";

import {
  PRIVACY_NOTICE_HEADING,
  PRIVACY_NOTICE_LINK_LABEL,
  PRIVACY_NOTICE_SUMMARY_LEAD,
} from "@/components/report/privacy-notice-content";

const privacyLinkClass = "font-medium text-sage underline underline-offset-2";

export function PrivacyNotice() {
  return (
    <section
      aria-labelledby="privacy-notice-summary-heading"
      className="rounded-xl border border-sage/25 bg-sage/10 p-5"
    >
      <div className="mb-3 flex items-center gap-2">
        <Info size={18} className="text-sage" aria-hidden />
        <h2 id="privacy-notice-summary-heading" className="text-sm font-semibold text-ink">
          {PRIVACY_NOTICE_HEADING}
        </h2>
      </div>
      <p className="text-sm leading-relaxed text-ink/80">
        {PRIVACY_NOTICE_SUMMARY_LEAD}{" "}
        <Link href="/privacy" className={privacyLinkClass}>
          {PRIVACY_NOTICE_LINK_LABEL}
        </Link>{" "}
        before you submit.
      </p>
    </section>
  );
}

export { privacyLinkClass };
