"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ReportForm } from "@/components/report/ReportForm";
import { WaxSealReveal } from "@/components/report/WaxSealReveal";
import { checkAccessSession } from "@/lib/api/access";

export default function ReportPage() {
  const router = useRouter();
  const [checkingSession, setCheckingSession] = useState(true);
  const [ticketCode, setTicketCode] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    checkAccessSession().then((ok) => {
      if (!active) {
        return;
      }
      if (!ok) {
        router.replace("/access");
        return;
      }
      setCheckingSession(false);
    });
    return () => {
      active = false;
    };
  }, [router]);

  if (checkingSession) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <div className="space-y-4">
          <div className="skeleton-shimmer h-8 w-48 rounded-lg" />
          <div className="skeleton-shimmer h-40 rounded-2xl" />
          <div className="skeleton-shimmer h-24 rounded-2xl" />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12 md:py-16">
      {ticketCode ? (
        <WaxSealReveal ticketCode={ticketCode} />
      ) : (
        <ReportForm onSubmitted={setTicketCode} />
      )}
      <p className="mt-8 text-center text-xs text-ink/50">
        <Link href="/status" className="font-medium text-sage underline">
          Check an existing ticket
        </Link>
      </p>
    </main>
  );
}
