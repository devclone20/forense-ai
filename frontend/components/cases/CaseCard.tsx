import { Badge } from "@/components/ui/badge";
import {
  DOMAIN_LABELS,
  DOMAIN_STYLES,
  STATUS_LABELS,
  STATUS_STYLES,
  cn,
  formatDate,
} from "@/lib/utils";
import type { Case } from "@/lib/types";
import { Calendar, Hash, User } from "lucide-react";
import Link from "next/link";

interface CaseCardProps {
  case_: Case;
  className?: string;
}

export function CaseCard({ case_, className }: CaseCardProps) {
  return (
    <Link
      href={`/cases/${case_.id}`}
      className={cn(
        "group block rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))]",
        "p-4 transition-all duration-150",
        "hover:border-[hsl(var(--accent)/0.4)] hover:bg-[hsl(var(--surface-raised))]",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2",
        className,
      )}
    >
      {/* Top row: case number + badges */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-1.5 text-xs text-[hsl(var(--muted-foreground))]">
          <Hash size={11} strokeWidth={2.5} />
          <span className="font-mono tracking-wider">{case_.case_number}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge className={DOMAIN_STYLES[case_.forensic_domain]}>
            {DOMAIN_LABELS[case_.forensic_domain]}
          </Badge>
          <Badge className={STATUS_STYLES[case_.status]}>
            {STATUS_LABELS[case_.status]}
          </Badge>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-foreground leading-snug mb-3 line-clamp-2 group-hover:text-white transition-colors">
        {case_.title}
      </h3>

      {/* Description */}
      {case_.description && (
        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-3 line-clamp-2 leading-relaxed">
          {case_.description}
        </p>
      )}

      {/* Footer: meta */}
      <div className="flex items-center justify-between gap-2 mt-auto pt-2 border-t border-[hsl(var(--border-subtle))]">
        <div className="flex items-center gap-1 text-xs text-[hsl(var(--muted-foreground))]">
          <User size={11} strokeWidth={2} />
          <span className="truncate max-w-[120px]">{case_.owner_id.slice(0, 8)}</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-[hsl(var(--muted-foreground))]">
          <Calendar size={11} strokeWidth={2} />
          <span>{formatDate(case_.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}
