"use client";

import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { checkAccessSession } from "@/lib/api/access";

export default function StatusLookupPage() {
  const router = useRouter();
  const [checkingSession, setCheckingSession] = useState(true);
  const [ticketCode, setTicketCode] = useState("");
  const [error, setError] = useState<string | null>(null);

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

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = ticketCode.trim().toUpperCase();
    if (!trimmed) {
      setError("Enter your ticket code.");
      return;
    }
    setError(null);
    router.push(`/status/${encodeURIComponent(trimmed)}`);
  }

  if (checkingSession) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16">
        <div className="skeleton-shimmer h-40 rounded-2xl" />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-16">
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-ink/10 bg-white/60 p-8 shadow-sm"
      >
        <h1 className="text-xl font-semibold text-ink">Check ticket status</h1>
        <p className="mt-2 text-sm text-ink/70">
          Enter the ticket code you received when you submitted your report.
        </p>

        <label htmlFor="ticket-code" className="mb-2 mt-6 block text-sm font-medium text-ink">
          Ticket code <span className="text-brass">*</span>
        </label>
        <input
          id="ticket-code"
          name="ticketCode"
          type="text"
          autoComplete="off"
          spellCheck={false}
          value={ticketCode}
          onChange={(event) => setTicketCode(event.target.value.toUpperCase())}
          className="mb-4 w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 font-mono tracking-widest text-ink outline-none ring-sage/30 focus:border-sage focus:ring-2"
          placeholder="ABCD2345"
        />

        {error ? (
          <p
            role="alert"
            className="mb-4 flex items-start gap-2 rounded-lg border border-brass/30 bg-brass/10 px-3 py-2 text-sm text-ink"
          >
            <AlertCircle size={16} className="mt-0.5 shrink-0 text-brass" aria-hidden />
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper transition hover:bg-ink/90"
        >
          View status
        </button>
      </form>

      <p className="mt-8 text-center text-xs text-ink/50">
        <Link href="/report" className="font-medium text-sage underline">
          Submit a new report
        </Link>
      </p>
    </main>
  );
}
