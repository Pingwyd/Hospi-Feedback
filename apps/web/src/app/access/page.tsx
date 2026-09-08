import Link from "next/link";

import { AccessGateForm } from "@/components/access/AccessGateForm";

export default function AccessPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-16">
      <AccessGateForm />
      <p className="mt-8 text-center text-xs leading-relaxed text-ink/60">
        This gate filters out people outside the unit. It is not identity verification
        and does not compromise anonymity.
      </p>
      <p className="mt-4 text-center text-xs text-ink/50">
        Already submitted?{" "}
        <Link href="/status" className="font-medium text-sage underline">
          Check ticket status
        </Link>
      </p>
    </main>
  );
}
