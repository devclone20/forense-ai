"use client";

import { useState } from "react";
import { api } from "@/lib/api";

const ROLES = [
  { value: "perito", label: "Perito" },
  { value: "investigador", label: "Investigador" },
  { value: "supervisor", label: "Supervisor" },
  { value: "advogado", label: "Advogado" },
  { value: "consultor", label: "Consultor" },
  { value: "viewer", label: "Viewer" },
];

interface InviteModalProps {
  onClose: () => void;
  onSuccess: (link: string) => void;
}

export function InviteModal({ onClose, onSuccess }: InviteModalProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("perito");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || loading) return;
    setError(null);
    setLoading(true);
    try {
      const result = await api.post<{ invite_id: string; accept_link: string }>(
        "/api/v1/invites",
        { email: email.trim(), role },
      );
      onSuccess(result.accept_link);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        className="absolute inset-0"
        onClick={onClose}
        role="button"
        aria-label="Close modal"
        tabIndex={-1}
        onKeyDown={(e) => e.key === "Escape" && onClose()}
      />
      <div className="relative bg-[#111] border border-[#1f1f1f] rounded-2xl px-8 py-7 w-full max-w-sm flex flex-col gap-6 shadow-2xl">
        <div>
          <h2 className="text-white text-lg font-semibold tracking-tight">Invite team member</h2>
          <p className="text-[#666] text-sm mt-0.5">
            They&apos;ll receive an email with a link to join your workspace
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[#888] uppercase tracking-wider">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="colleague@example.com"
              className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm placeholder:text-[#444] focus:outline-none focus:ring-1 focus:ring-[#333]"
              required
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-[#888] uppercase tracking-wider">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-lg bg-[#0a0a0a] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-1 focus:ring-[#333]"
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={!email.trim() || loading}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
            >
              {loading ? "Sending…" : "Send invitation"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="py-2.5 px-4 rounded-lg text-sm font-medium border border-[#1f1f1f] text-[#888] hover:text-white hover:border-[#333] transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
