"use client";

import { useRef, useState } from "react";

interface MFAFormProps {
  onSubmit: (code: string) => Promise<void>;
  onUseBackupCode?: (code: string) => Promise<void>;
}

export function MFAForm({ onSubmit, onUseBackupCode }: MFAFormProps) {
  const [digits, setDigits] = useState<string[]>(Array(6).fill(""));
  const [useBackup, setUseBackup] = useState(false);
  const [backupCode, setBackupCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);

  const totpComplete = digits.every((d) => d.length === 1);

  function handleDigitChange(idx: number, value: string) {
    const cleaned = value.replace(/\D/g, "");

    if (cleaned.length > 1) {
      // Handle paste of full code
      const chars = cleaned.slice(0, 6).split("");
      const next = [...digits];
      chars.forEach((c, i) => {
        if (i < 6) next[i] = c;
      });
      setDigits(next);
      inputRefs.current[Math.min(chars.length, 5)]?.focus();
      return;
    }

    const next = [...digits];
    next[idx] = cleaned;
    setDigits(next);

    if (cleaned && idx < 5) {
      inputRefs.current[idx + 1]?.focus();
    }
  }

  function handleKeyDown(idx: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[idx] && idx > 0) {
      inputRefs.current[idx - 1]?.focus();
    }
  }

  async function handleTotpSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!totpComplete || loading) return;
    setError(null);
    setLoading(true);
    try {
      await onSubmit(digits.join(""));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid code");
      setDigits(Array(6).fill(""));
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  }

  async function handleBackupSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!backupCode.trim() || loading || !onUseBackupCode) return;
    setError(null);
    setLoading(true);
    try {
      await onUseBackupCode(backupCode.trim());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid backup code");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="text-center">
        <p className="text-sm text-[#888]">
          {useBackup
            ? "Enter one of your backup recovery codes"
            : "Enter the 6-digit code from your authenticator app"}
        </p>
      </div>

      {!useBackup ? (
        <form onSubmit={handleTotpSubmit} className="flex flex-col gap-4">
          <div className="flex gap-2 justify-center">
            {digits.map((d, idx) => (
              <input
                key={idx}
                ref={(el) => { inputRefs.current[idx] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={d}
                onChange={(e) => handleDigitChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                className={[
                  "w-10 h-12 text-center rounded-lg border bg-[#111]",
                  "text-white text-lg font-mono",
                  "focus:outline-none focus:ring-1 focus:ring-[#333]",
                  error ? "border-red-500/60" : "border-[#1f1f1f]",
                ].join(" ")}
              />
            ))}
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-center">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!totpComplete || loading}
            className={[
              "w-full py-2.5 rounded-lg text-sm font-medium transition-all",
              totpComplete && !loading
                ? "bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98]"
                : "bg-[#1f1f1f] text-[#555] cursor-not-allowed",
            ].join(" ")}
          >
            {loading ? "Verifying…" : "Verify"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleBackupSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            autoComplete="off"
            value={backupCode}
            onChange={(e) => setBackupCode(e.target.value)}
            placeholder="XXXX-XXXXXX"
            className="w-full rounded-lg bg-[#111] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-sm font-mono tracking-widest focus:outline-none focus:ring-1 focus:ring-[#333]"
          />

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-center">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!backupCode.trim() || loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
          >
            {loading ? "Verifying…" : "Use backup code"}
          </button>
        </form>
      )}

      <button
        type="button"
        onClick={() => {
          setUseBackup((v) => !v);
          setError(null);
        }}
        className="text-xs text-[#555] hover:text-[#888] transition-colors text-center"
      >
        {useBackup
          ? "Use authenticator app instead"
          : "Use a backup recovery code"}
      </button>
    </div>
  );
}
