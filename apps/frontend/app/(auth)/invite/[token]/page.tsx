"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface ValidateResponse {
  valid: boolean;
  email?: string;
  role?: string;
  org_name?: string;
}

interface AcceptResponse {
  user_id: string;
  email: string;
}

export default function InviteAcceptPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const token = params.token;

  const [invite, setInvite] = useState<ValidateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<ValidateResponse>(`/api/v1/invites/${token}/validate`)
      .then(setInvite)
      .catch(() => setInvite({ valid: false }))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleAccept(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim() || password.length < 8 || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.post<AcceptResponse>(`/api/v1/invites/${token}/accept`, {
        display_name: displayName.trim(),
        password,
      });
      router.push("/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create account");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-[#333] border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!invite?.valid) {
    return (
      <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-3 text-center">
        <p className="text-white font-medium">Invitation not found</p>
        <p className="text-[#666] text-sm">
          This invitation may have expired, been revoked, or already accepted.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">
          Join {invite.org_name ?? "Forense AI"}
        </h1>
        <p className="text-[#666] text-sm">
          You&apos;ve been invited as{" "}
          <span className="text-[#aaa] font-medium">{invite.email}</span>
        </p>
      </div>

      <form onSubmit={handleAccept} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-[#888] uppercase tracking-wider">
            Display name
          </label>
          <input
            type="text"
            autoComplete="name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Your full name"
            className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm placeholder:text-[#444] focus:outline-none focus:ring-1 focus:ring-[#333]"
            required
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-[#888] uppercase tracking-wider">
            Password
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

        {error && (
          <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!displayName.trim() || password.length < 8 || submitting}
          className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>
    </div>
  );
}
