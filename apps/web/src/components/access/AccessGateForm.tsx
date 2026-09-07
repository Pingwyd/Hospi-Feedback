"use client";

import { AlertCircle, Lock } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { verifyAccessCode } from "@/lib/api/access";

export function AccessGateForm() {
  const router = useRouter();
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await verifyAccessCode(accessCode.trim());
      router.push("/report");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Could not verify access code. Try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-ink/10 bg-white/60 p-8 shadow-sm"
    >
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-sage/15 text-sage">
          <Lock size={20} aria-hidden />
        </span>
        <div>
          <h1 className="text-xl font-semibold text-ink">Unit access</h1>
          <p className="text-sm text-ink/70">
            Enter the shared access code once per browser session.
          </p>
        </div>
      </div>

      <label htmlFor="access-code" className="mb-2 block text-sm font-medium text-ink">
        Access code <span className="text-brass">*</span>
      </label>
      <input
        id="access-code"
        name="accessCode"
        type="password"
        autoComplete="off"
        required
        value={accessCode}
        onChange={(event) => setAccessCode(event.target.value)}
        className="mb-4 w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-ink outline-none ring-sage/30 transition focus:border-sage focus:ring-2"
        placeholder="Access code"
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
        disabled={submitting}
        className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Verifying..." : "Continue"}
      </button>
    </form>
  );
}
