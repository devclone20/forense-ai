"use client";

import { cn } from "@/lib/utils";
import { Briefcase, LayoutDashboard, Shield } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/cases", label: "Casos", icon: Briefcase },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r border-[hsl(var(--border))] bg-[hsl(var(--surface))] flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-4 h-14 flex items-center gap-2 border-b border-[hsl(var(--border))]">
        <Shield size={18} className="text-accent" strokeWidth={2} />
        <span className="text-sm font-semibold tracking-tight text-foreground">
          Forense AI
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent/10 text-accent"
                  : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-raised))] hover:text-foreground",
              )}
            >
              <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[hsl(var(--border))]">
        <p className="text-[10px] text-[hsl(var(--muted-foreground))] font-mono">
          v0.1.0 — Case Management
        </p>
      </div>
    </aside>
  );
}
