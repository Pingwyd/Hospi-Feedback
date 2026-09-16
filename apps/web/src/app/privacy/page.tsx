import Link from "next/link";

import { PrivacyNoticeFull } from "@/components/report/PrivacyNoticeFull";

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-12 md:py-16">
      <PrivacyNoticeFull variant="page" />
      <p className="mt-10 text-center text-sm text-ink/60">
        <Link href="/report" className="font-medium text-sage underline underline-offset-2">
          Back to submit a report
        </Link>
      </p>
    </main>
  );
}
