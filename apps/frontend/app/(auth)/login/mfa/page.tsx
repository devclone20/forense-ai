"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { MFAForm } from "@/components/auth/MFAForm";
import { MFASetup } from "@/components/auth/MFASetup";
import { api } from "@/lib/api";
import { verifyMfa } from "@/lib/auth";

function MFAPageContent() {
  const router = useRouter();
  const params = useSearchParams();
  const isSetup = params.get("setup") === "true";

  async function handleVerify(code: string) {
    const pending = sessionStorage.getItem("forense_mfa_pending");
    if (!pending) {
      router.push("/login");
      return;
    }
    await verifyMfa(pending, code);
    sessionStorage.removeItem("forense_mfa_pending");
    router.push("/");
  }

  if (isSetup) {
    return <MFASetupFlow />;
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">
          Two-factor authentication
        </h1>
        <p className="text-[#666] text-sm">Verify your identity to continue</p>
      </div>

      <MFAForm onSubmit={handleVerify} />
    </div>
  );
}

function MFASetupFlow() {
  const router = useRouter();

  async function loadSetupData() {
    const data = await api.post<{ qr_uri: string; backup_codes: string[] }>(
      "/api/v1/auth/mfa/setup",
      {},
    );
    return data;
  }

  async function handleConfirm(totpCode: string) {
    await api.post("/api/v1/auth/mfa/enable", { totp_code: totpCode });
    router.push("/");
  }

  // Use a simple state machine since Suspense-based data fetching would
  // require a full data library — keeping this minimal and dependency-free.
  const [data, setData] = useState<{
    qr_uri: string;
    backup_codes: string[];
  } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    loadSetupData()
      .then(setData)
      .catch((err: unknown) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load MFA setup"),
      );
  }, []);

  if (loadError) {
    return (
      <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9">
        <p className="text-red-400 text-sm text-center">{loadError}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-[#333] border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">
          Set up two-factor authentication
        </h1>
        <p className="text-[#666] text-sm">
          MFA is required for admin accounts
        </p>
      </div>

      <MFASetup
        qrUri={data.qr_uri}
        backupCodes={data.backup_codes}
        onConfirm={handleConfirm}
      />
    </div>
  );
}

export default function MFAPage() {
  return (
    <Suspense
      fallback={
        <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-[#333] border-t-white rounded-full animate-spin" />
        </div>
      }
    >
      <MFAPageContent />
    </Suspense>
  );
}
