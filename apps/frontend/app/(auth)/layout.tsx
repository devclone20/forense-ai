/**
 * Auth layout — minimal, centred, dark-first.
 * No sidebar. No distractions. Brand mark only.
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center px-4">
      {/* Brand mark */}
      <div className="mb-10 flex flex-col items-center gap-2">
        <div className="w-10 h-10 rounded-xl bg-[#1f1f1f] border border-[#2a2a2a] flex items-center justify-center">
          <span className="text-white font-semibold text-sm tracking-tight">F</span>
        </div>
        <span className="text-[#888] text-xs tracking-widest uppercase">
          Forense AI
        </span>
      </div>

      {/* Page content */}
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
