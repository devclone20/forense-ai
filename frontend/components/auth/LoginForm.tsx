"use client";

import { useState } from "react";
import Link from "next/link";
import { login, type LoginResult } from "@/lib/auth";

interface LoginFormProps {
  onSuccess: (result: LoginResult) => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isValid = email.trim().length > 0 && password.length > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid || loading) return;

    setError(null);
    setLoading(true);

    try {
      const result = await login(email.trim(), password);
      onSuccess(result);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "An error occurred. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <div className="flex flex-col gap-1">
        <label
          htmlFor="email"
          className="text-xs font-medium text-[#888] uppercase tracking-wider"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={[
            "w-full rounded-lg bg-[#111] border px-3.5 py-2.5",
            "text-white text-sm placeholder:text-[#444]",
            "focus:outline-none focus:ring-1 focus:ring-[#333]",
            "transition-colors",
            error ? "border-red-500/60" : "border-[#1f1f1f]",
          ].join(" ")}
          placeholder="you@example.com"
          required
        />
      </div>

      <div className="flex flex-col gap-1">
        <label
          htmlFor="password"
          className="text-xs font-medium text-[#888] uppercase tracking-wider"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={[
            "w-full rounded-lg bg-[#111] border px-3.5 py-2.5",
            "text-white text-sm placeholder:text-[#444]",
            "focus:outline-none focus:ring-1 focus:ring-[#333]",
            "transition-colors",
            error ? "border-red-500/60" : "border-[#1f1f1f]",
          ].join(" ")}
          placeholder="••••••••"
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
        disabled={!isValid || loading}
        className={[
          "w-full py-2.5 rounded-lg text-sm font-medium",
          "transition-all duration-150",
          isValid && !loading
            ? "bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98]"
            : "bg-[#1f1f1f] text-[#555] cursor-not-allowed",
        ].join(" ")}
      >
        {loading ? (
          <span className="inline-flex items-center gap-2 justify-center">
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8H4z"
              />
            </svg>
            Signing in…
          </span>
        ) : (
          "Sign in"
        )}
      </button>

      <div className="text-center">
        <Link
          href="/recovery"
          className="text-xs text-[#555] hover:text-[#888] transition-colors"
        >
          Forgot your password?
        </Link>
      </div>
    </form>
  );
}
