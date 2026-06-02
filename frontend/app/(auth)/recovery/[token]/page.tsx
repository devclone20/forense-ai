"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function RecoveryConfirmPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const mismatch = confirm.length > 0 && password !== confirm;
  const valid = password.length >= 8 && password === confirm;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid || loading) return;
    setError(null);
    setLoading(true);
    try {
      await api.post("/api/v1/auth/recovery/confirm", {
        token: params.token,
        new_password: password,
      });
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">
          Choose a new password
        </h1>
        <p className="text-[#666] text-sm">
          {done ? "Password updated — redirecting…" : "Minimum 8 characters"}
        </p>
      </div>

      {!done && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[#888] uppercase tracking-wider">
              New password
            </label>
            <input
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm placeholder:text-[#444] focus:outline-none focus:ring-1 focus:ring-[#333]"
              minLength={8}
              required
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[#888] uppercase tracking-wider">
              Confirm password
            </label>
            <input
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repeat password"
              className={[
                "w-full rounded-lg bg-[#0a0a0a] border px-3.5 py-2.5 text-white text-sm",
                "placeholder:text-[#444] focus:outline-none focus:ring-1 focus:ring-[#333]",
                mismatch ? "border-red-500/60" : "border-[#1f1f1f]",
              ].join(" ")}
              required
            />
            {mismatch && (
              <p className="text-xs text-red-400">Passwords do not match</p>
            )}
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!valid || loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
          >
            {loading ? "Updating…" : "Update password"}
          </button>
        </form>
      )}
    </div>
  );
}
