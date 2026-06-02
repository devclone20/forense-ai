"use client";

interface IntegrityBadgeProps {
  status: "intact" | "tampered" | "unverified";
  className?: string;
}

const CONFIG = {
  intact: {
    label: "Íntegra",
    icon: "✓",
    className: "bg-green-500/15 text-green-400 border border-green-500/30",
  },
  tampered: {
    label: "ADULTERADA",
    icon: "✕",
    className: "bg-red-500/15 text-red-400 border border-red-500/30 font-semibold",
  },
  unverified: {
    label: "Não verificada",
    icon: "—",
    className: "bg-neutral-700/50 text-neutral-400 border border-neutral-700",
  },
} as const;

export function IntegrityBadge({ status, className = "" }: IntegrityBadgeProps) {
  const cfg = CONFIG[status];
  return (
    <span
      className={[
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs",
        cfg.className,
        className,
      ].join(" ")}
    >
      <span aria-hidden="true">{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}
