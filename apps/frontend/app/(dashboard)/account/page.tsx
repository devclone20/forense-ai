"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface ProfileData {
  user_id: string;
  email: string;
  display_name: string;
  global_role: string;
  mfa_enabled: boolean;
}

interface MFASetupData {
  qr_uri: string;
  backup_codes: string[];
}

export default function AccountPage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<ProfileData>("/api/v1/account/me")
      .then(setProfile)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-5 h-5 border-2 border-[#333] border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="flex flex-col gap-8 max-w-xl">
      <div>
        <h1 className="text-white text-2xl font-semibold tracking-tight">Account</h1>
        <p className="text-[#666] text-sm mt-1">Manage your profile and security settings</p>
      </div>

      <ProfileSection profile={profile} onUpdate={setProfile} />
      <PasswordSection />
      <MFASection mfaEnabled={profile.mfa_enabled} />
    </div>
  );
}

// ── Profile section ───────────────────────────────────────────────────────────

function ProfileSection({
  profile,
  onUpdate,
}: {
  profile: ProfileData;
  onUpdate: (p: ProfileData) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState(profile.display_name);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim() || saving) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.patch<ProfileData>("/api/v1/account/me", {
        display_name: displayName.trim(),
      });
      onUpdate(updated);
      setEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard title="Profile">
      {editing ? (
        <form onSubmit={handleSave} className="flex flex-col gap-4">
          <Field label="Display name">
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input"
            />
          </Field>
          <Field label="Email">
            <p className="text-sm text-[#666]">{profile.email}</p>
          </Field>
          {error && <ErrorMsg>{error}</ErrorMsg>}
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Saving…" : "Save changes"}
            </button>
            <button
              type="button"
              onClick={() => { setEditing(false); setDisplayName(profile.display_name); }}
              className="btn-ghost"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col gap-4">
          <Field label="Display name">
            <p className="text-sm text-white">{profile.display_name}</p>
          </Field>
          <Field label="Email">
            <p className="text-sm text-[#666]">{profile.email}</p>
          </Field>
          <Field label="Role">
            <RoleBadge role={profile.global_role} />
          </Field>
          <button type="button" onClick={() => setEditing(true)} className="btn-ghost w-fit">
            Edit profile
          </button>
        </div>
      )}
    </SectionCard>
  );
}

// ── Password section ──────────────────────────────────────────────────────────

function PasswordSection() {
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mismatch = form.confirm.length > 0 && form.next !== form.confirm;
  const valid = form.current && form.next.length >= 8 && form.next === form.confirm;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid || saving) return;
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await api.post("/api/v1/account/password", {
        current_password: form.current,
        new_password: form.next,
      });
      setSuccess(true);
      setForm({ current: "", next: "", confirm: "" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard title="Password">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Current password">
          <input
            type="password"
            value={form.current}
            onChange={(e) => setForm((f) => ({ ...f, current: e.target.value }))}
            className="input"
            autoComplete="current-password"
          />
        </Field>
        <Field label="New password">
          <input
            type="password"
            value={form.next}
            onChange={(e) => setForm((f) => ({ ...f, next: e.target.value }))}
            className="input"
            autoComplete="new-password"
            minLength={8}
          />
        </Field>
        <Field label="Confirm new password">
          <input
            type="password"
            value={form.confirm}
            onChange={(e) => setForm((f) => ({ ...f, confirm: e.target.value }))}
            className={["input", mismatch ? "border-red-500/60" : ""].join(" ")}
            autoComplete="new-password"
          />
          {mismatch && <p className="text-xs text-red-400 mt-1">Passwords do not match</p>}
        </Field>
        {error && <ErrorMsg>{error}</ErrorMsg>}
        {success && (
          <p className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
            Password updated successfully
          </p>
        )}
        <button type="submit" disabled={!valid || saving} className="btn-primary w-fit">
          {saving ? "Updating…" : "Update password"}
        </button>
      </form>
    </SectionCard>
  );
}

// ── MFA section ───────────────────────────────────────────────────────────────

function MFASection({ mfaEnabled }: { mfaEnabled: boolean }) {
  const [showSetup, setShowSetup] = useState(false);
  const [setupData, setSetupData] = useState<MFASetupData | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regenCodes, setRegenCodes] = useState<string[] | null>(null);
  const [regenTotp, setRegenTotp] = useState("");

  async function startSetup() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<MFASetupData>("/api/v1/auth/mfa/setup", {});
      setSetupData(data);
      setShowSetup(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start MFA setup");
    } finally {
      setLoading(false);
    }
  }

  async function enableMfa(e: React.FormEvent) {
    e.preventDefault();
    if (totpCode.length !== 6 || loading) return;
    setLoading(true);
    setError(null);
    try {
      await api.post("/api/v1/auth/mfa/enable", { totp_code: totpCode });
      window.location.reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid code");
    } finally {
      setLoading(false);
    }
  }

  async function regenerateCodes(e: React.FormEvent) {
    e.preventDefault();
    if (regenTotp.length !== 6 || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.post<{ backup_codes: string[] }>(
        "/api/v1/account/mfa/backup-codes/regenerate",
        { totp_code: regenTotp },
      );
      setRegenCodes(result.backup_codes);
      setRegenTotp("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to regenerate codes");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard title="Two-factor authentication">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div
            className={[
              "w-2 h-2 rounded-full",
              mfaEnabled ? "bg-emerald-400" : "bg-[#444]",
            ].join(" ")}
          />
          <span className="text-sm text-[#888]">
            {mfaEnabled ? "MFA is active" : "MFA is not configured"}
          </span>
        </div>

        {!mfaEnabled && !showSetup && (
          <button type="button" onClick={startSetup} disabled={loading} className="btn-primary w-fit">
            {loading ? "Loading…" : "Set up authenticator app"}
          </button>
        )}

        {showSetup && setupData && !mfaEnabled && (
          <div className="flex flex-col gap-4 p-4 bg-[#0a0a0a] rounded-xl border border-[#1f1f1f]">
            <div className="p-3 bg-white rounded-lg w-fit">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(setupData.qr_uri)}&size=128x128&margin=0`}
                alt="MFA QR code"
                width={128}
                height={128}
              />
            </div>
            <form onSubmit={enableMfa} className="flex flex-col gap-3">
              <p className="text-xs text-[#888]">
                Scan the QR code then enter the 6-digit code to activate MFA
              </p>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
                placeholder="000000"
                className="input font-mono tracking-[0.5em] text-center w-32"
              />
              {error && <ErrorMsg>{error}</ErrorMsg>}
              <button
                type="submit"
                disabled={totpCode.length !== 6 || loading}
                className="btn-primary w-fit"
              >
                {loading ? "Activating…" : "Activate"}
              </button>
            </form>
          </div>
        )}

        {mfaEnabled && !regenCodes && (
          <form onSubmit={regenerateCodes} className="flex flex-col gap-3">
            <p className="text-xs text-[#888]">
              Regenerate backup codes — current codes will be invalidated
            </p>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={regenTotp}
              onChange={(e) => setRegenTotp(e.target.value.replace(/\D/g, ""))}
              placeholder="TOTP code to confirm"
              className="input font-mono w-48"
            />
            {error && <ErrorMsg>{error}</ErrorMsg>}
            <button
              type="submit"
              disabled={regenTotp.length !== 6 || loading}
              className="btn-ghost w-fit text-amber-400 border-amber-500/30 hover:border-amber-500/60"
            >
              {loading ? "Regenerating…" : "Regenerate backup codes"}
            </button>
          </form>
        )}

        {regenCodes && (
          <div className="flex flex-col gap-3 p-4 bg-[#0a0a0a] rounded-xl border border-amber-500/20">
            <p className="text-xs text-amber-400 font-medium">
              New backup codes — save these now, they will not be shown again
            </p>
            <div className="grid grid-cols-2 gap-2">
              {regenCodes.map((c) => (
                <span key={c} className="font-mono text-xs text-white bg-[#111] border border-[#1f1f1f] rounded-lg px-3 py-2 tracking-wider text-center">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </SectionCard>
  );
}

// ── Design primitives ─────────────────────────────────────────────────────────

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-6 py-5 flex flex-col gap-5">
      <h2 className="text-white text-sm font-semibold uppercase tracking-wider">{title}</h2>
      {children}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-[#666] uppercase tracking-wider">
        {label}
      </label>
      {children}
    </div>
  );
}

function ErrorMsg({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
      {children}
    </p>
  );
}

function RoleBadge({ role }: { role: string }) {
  const colours: Record<string, string> = {
    admin: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    perito: "bg-blue-500/15 text-blue-300 border-blue-500/30",
    supervisor: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    investigador: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    advogado: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    consultor: "bg-orange-500/15 text-orange-300 border-orange-500/30",
    viewer: "bg-[#1f1f1f] text-[#888] border-[#2a2a2a]",
  };
  const cls = colours[role] ?? colours["viewer"];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}
    >
      {role}
    </span>
  );
}
