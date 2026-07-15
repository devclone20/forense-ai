"use client";

import { useState } from "react";

interface MFASetupProps {
  qrUri: string;
  backupCodes: string[];
  onConfirm: (totpCode: string) => Promise<void>;
}

export function MFASetup({ qrUri, backupCodes, onConfirm }: MFASetupProps) {
  const [step, setStep] = useState<"qr" | "backup" | "verify">("qr");
  const [codesAcknowledged, setCodesAcknowledged] = useState(false);
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Chunk backup codes into pairs for 2-column layout
  const pairs: [string, string | undefined][] = [];
  for (let i = 0; i < backupCodes.length; i += 2) {
    pairs.push([backupCodes[i], backupCodes[i + 1]]);
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    if (totpCode.length !== 6 || loading) return;
    setError(null);
    setLoading(true);
    try {
      await onConfirm(totpCode);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid code");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Step indicators */}
      <div className="flex items-center gap-2 justify-center">
        {(["qr", "backup", "verify"] as const).map((s, idx) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={[
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                step === s
                  ? "bg-white text-black"
                  : "bg-[#1f1f1f] text-[#555]",
              ].join(" ")}
            >
              {idx + 1}
            </div>
            {idx < 2 && <div className="w-8 h-px bg-[#1f1f1f]" />}
          </div>
        ))}
      </div>

      {/* Step: scan QR */}
      {step === "qr" && (
        <div className="flex flex-col gap-5 items-center">
          <p className="text-sm text-[#888] text-center">
            Scan this QR code with your authenticator app
            (Google Authenticator, Authy, 1Password…)
          </p>

          {/* QR code rendered via <img> from the otpauth:// URI via Google Charts API */}
          {/* In production, render with qrcode.react to avoid external dependency */}
          <div className="p-3 bg-white rounded-xl">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrUri)}&size=160x160&margin=0`}
              alt="MFA QR code"
              width={160}
              height={160}
              className="block"
            />
          </div>

          <details className="w-full">
            <summary className="text-xs text-[#555] cursor-pointer hover:text-[#888] transition-colors text-center">
              Can&apos;t scan? Show secret key
            </summary>
            <p className="mt-2 text-xs font-mono text-[#666] bg-[#111] border border-[#1f1f1f] rounded-lg px-3 py-2 break-all text-center">
              {new URL(qrUri).searchParams.get("secret") ?? ""}
            </p>
          </details>

          <button
            type="button"
            onClick={() => setStep("backup")}
            className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all"
          >
            I&apos;ve scanned it
          </button>
        </div>
      )}

      {/* Step: backup codes */}
      {step === "backup" && (
        <div className="flex flex-col gap-5">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
            <p className="text-xs text-amber-400 font-medium">
              These codes are shown ONE TIME ONLY
            </p>
            <p className="text-xs text-[#888] mt-1">
              Store them somewhere safe. Each code can be used once to bypass MFA
              if you lose your device.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {pairs.map(([a, b], idx) => (
              <div key={idx} className="contents">
                <span className="font-mono text-xs text-white bg-[#111] border border-[#1f1f1f] rounded-lg px-3 py-2 tracking-wider text-center">
                  {a}
                </span>
                {b && (
                  <span className="font-mono text-xs text-white bg-[#111] border border-[#1f1f1f] rounded-lg px-3 py-2 tracking-wider text-center">
                    {b}
                  </span>
                )}
              </div>
            ))}
          </div>

          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={codesAcknowledged}
              onChange={(e) => setCodesAcknowledged(e.target.checked)}
              className="w-4 h-4 rounded border-[#333] bg-[#111] accent-white"
            />
            <span className="text-xs text-[#888] group-hover:text-[#aaa] transition-colors">
              I have saved my backup codes in a safe place
            </span>
          </label>

          <button
            type="button"
            disabled={!codesAcknowledged}
            onClick={() => setStep("verify")}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-all bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      )}

      {/* Step: verify code */}
      {step === "verify" && (
        <form onSubmit={handleVerify} className="flex flex-col gap-4">
          <p className="text-sm text-[#888] text-center">
            Enter the 6-digit code from your authenticator app to confirm setup
          </p>

          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
            placeholder="000000"
            className="w-full rounded-lg bg-[#111] border border-[#1f1f1f] px-3.5 py-2.5 text-white text-xl font-mono tracking-[0.5em] text-center focus:outline-none focus:ring-1 focus:ring-[#333]"
          />

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-center">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={totpCode.length !== 6 || loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:bg-[#f0f0f0] active:scale-[0.98] transition-all disabled:bg-[#1f1f1f] disabled:text-[#555] disabled:cursor-not-allowed"
          >
            {loading ? "Activating…" : "Activate two-factor authentication"}
          </button>
        </form>
      )}
    </div>
  );
}
