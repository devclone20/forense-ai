"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function RecoveryPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || loading) return;
    setError(null);
    setLoading(true);
    try {
      await api.post("/api/v1/auth/recovery/request", { email: email.trim() });
      setSubmitted(true);
    } catch (err: unknown) {
      // Even on error, show the neutral message (rate limit is the only real error)
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("429") || msg.toLowerCase().includes("too many")) {
        setError("Too many attempts. Please wait a minute and try again.");
      } else {
        setSubmitted(true); // still neutral
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">
          Reset your password
        </h1>
        <p className="text-[#666] text-sm">
          {submitted
            ? "Check your inbox for a recovery link"
            : "We'll send you a link to reset your password"}
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[#888] uppercase tracking-wider">
              Email
            </label>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm placeholder:text-[#444] focus:outline-none focus:ring-1 focus:ring-[#333]"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!email.trim() || loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
          >
            {loading ? "Sending…" : "Send recovery link"}
          </button>
        </form>
      ) : (
        <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] px-4 py-4">
          <p className="text-sm text-[#888] text-center">
            If that address is registered, a recovery link has been sent.
            Check your spam folder if it doesn&apos;t arrive within a few minutes.
          </p>
        </div>
      )}
    </div>
  );
}
