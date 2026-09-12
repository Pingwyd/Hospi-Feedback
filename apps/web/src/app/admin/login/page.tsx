"use client";

import { AlertCircle, Lock } from "lucide-react";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";
import { ApiError } from "@/lib/api/client";
import { loginAdmin } from "@/lib/api/admin-auth";

export default function AdminLoginPage() {
  const router = useRouter();
  const { refreshProfile } = useAdminSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [needsTotp, setNeedsTotp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginAdmin({
        email: email.trim(),
        password,
        totp_code: totpCode.trim() || undefined,
      });
      await refreshProfile();
      router.replace("/admin/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.message.toLowerCase().includes("second factor")) {
          setNeedsTotp(true);
        }
        setError(err.message);
      } else {
        setError("Sign in failed. Check your credentials and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6 py-10">
      <div className="w-full max-w-md rounded-2xl border border-ink/10 bg-surface/60 p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <Lock className="text-sage" size={22} />
          <div>
            <h1 className="text-xl font-semibold text-ink">Admin sign in</h1>
            <p className="text-sm text-ink/60">
              Use your Hospi Feedback admin account.
            </p>
          </div>
        </div>

        {error ? (
          <div
            role="alert"
            className="mb-4 flex items-start gap-2 rounded-lg border border-brass/30 bg-brass/10 p-3 text-sm text-ink"
          >
            <AlertCircle className="mt-0.5 shrink-0 text-brass" size={16} />
            <span>{error}</span>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-ink">
              Email <span className="text-brass">*</span>
            </span>
            <input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-ink">
              Password <span className="text-brass">*</span>
            </span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
            />
          </label>
          {needsTotp ? (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-ink">
                Authenticator code <span className="text-brass">*</span>
              </span>
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                value={totpCode}
                onChange={(event) => setTotpCode(event.target.value)}
                className="w-full rounded-lg border border-ink/15 bg-paper px-4 py-3 text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2"
              />
            </label>
          ) : null}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-semibold text-paper hover:bg-ink/90 disabled:opacity-60"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
