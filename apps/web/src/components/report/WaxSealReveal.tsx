"use client";

import { Copy, ExternalLink, ShieldCheck } from "lucide-react";
import { useCallback, useState } from "react";

import { siteUrl } from "@/lib/design-tokens";

type WaxSealRevealProps = {
  ticketCode: string;
};

export function WaxSealReveal({ ticketCode }: WaxSealRevealProps) {
  const [revealed, setRevealed] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleReveal = useCallback(() => {
    setRevealed(true);
  }, []);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(ticketCode);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [ticketCode]);

  const statusHref = revealed
    ? `${siteUrl()}/status/${encodeURIComponent(ticketCode)}`
    : undefined;

  return (
    <section
      aria-labelledby="confirmation-heading"
      className="rounded-2xl border border-ink/10 bg-white/70 p-8 shadow-sm"
    >
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-sage/15 text-sage">
          <ShieldCheck size={20} aria-hidden />
        </span>
        <div>
          <h1 id="confirmation-heading" className="text-xl font-semibold text-ink">
            Report received
          </h1>
          <p className="text-sm text-ink/70">
            Your ticket code is shown once below. Save it before you leave.
          </p>
        </div>
      </div>

      {!revealed ? (
        <button
          type="button"
          onClick={handleReveal}
          className="group mx-auto flex w-full max-w-xs flex-col items-center gap-4 rounded-2xl border-2 border-brass/40 bg-paper px-8 py-10 transition hover:border-brass hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brass/50"
          aria-label="Break the wax seal to reveal your ticket code"
        >
          <span
            aria-hidden
            className="relative flex h-28 w-28 items-center justify-center rounded-full border-4 border-brass bg-gradient-to-br from-brass/30 via-brass/10 to-paper shadow-inner"
          >
            <span className="absolute inset-2 rounded-full border border-ink/20" />
            <span className="text-center text-[10px] font-bold uppercase tracking-[0.2em] text-ink/70">
              Hospi
            </span>
          </span>
          <span className="text-sm font-medium text-ink group-hover:text-brass">
            Tap to break the seal
          </span>
          <span className="text-xs text-ink/60">Your code stays hidden until you do</span>
        </button>
      ) : (
        <div className="space-y-6">
          <div className="rounded-xl border border-brass/30 bg-paper px-6 py-5 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brass">
              Your ticket code
            </p>
            <p
              className="font-mono text-3xl font-bold tracking-[0.35em] text-ink"
              data-testid="revealed-ticket-code"
            >
              {ticketCode}
            </p>
            <button
              type="button"
              onClick={handleCopy}
              className="mt-4 inline-flex items-center gap-2 rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink/5"
            >
              <Copy size={16} aria-hidden />
              {copied ? "Copied" : "Copy code"}
            </button>
          </div>

          {statusHref ? (
            <div className="rounded-xl border border-sage/25 bg-sage/10 p-5">
              <p className="mb-2 text-sm font-medium text-ink">Status link</p>
              <a
                href={statusHref}
                className="inline-flex items-center gap-2 break-all text-sm font-medium text-sage underline"
              >
                {statusHref}
                <ExternalLink size={14} aria-hidden />
              </a>
              <p className="mt-4 text-xs leading-relaxed text-ink/70">
                On a shared device, open this link in a private or incognito window. The
                code is in the URL and may remain in browser history on a normal tab.
              </p>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
