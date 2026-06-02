"use client";

import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/auth/LoginForm";
import type { LoginResult } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();

  function handleSuccess(result: LoginResult) {
    if (result.requires_mfa_setup) {
      // Admin must configure MFA before accessing the app
      router.push("/login/mfa?setup=true");
      return;
    }
    if (result.requires_mfa && result.mfa_pending_token) {
      // Store mfa_pending_token temporarily for the MFA step
      sessionStorage.setItem("forense_mfa_pending", result.mfa_pending_token);
      router.push("/login/mfa");
      return;
    }
    // Full token pair — already stored by auth.ts login()
    router.push("/");
  }

  return (
    <div className="bg-[#111111] border border-[#1f1f1f] rounded-2xl px-8 py-9 flex flex-col gap-7">
      <div className="flex flex-col gap-1">
        <h1 className="text-white text-xl font-semibold tracking-tight">Sign in</h1>
        <p className="text-[#666] text-sm">Continue to your workspace</p>
      </div>

      <LoginForm onSuccess={handleSuccess} />
    </div>
  );
}
