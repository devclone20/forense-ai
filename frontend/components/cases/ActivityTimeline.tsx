import type { AuditLogEntry } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import {
  ArrowRight,
  FileText,
  UserPlus,
  UserMinus,
  Edit3,
  Plus,
} from "lucide-react";

const ACTION_ICONS: Record<AuditLogEntry["action"], React.ElementType> = {
  case_created: Plus,
  case_updated: Edit3,
  case_status_changed: ArrowRight,
  member_added: UserPlus,
  member_removed: UserMinus,
};

const ACTION_LABELS: Record<AuditLogEntry["action"], string> = {
  case_created: "Caso criado",
  case_updated: "Caso actualizado",
  case_status_changed: "Estado alterado",
  member_added: "Membro adicionado",
  member_removed: "Membro removido",
};

interface ActivityTimelineProps {
  entries: AuditLogEntry[];
}

export function ActivityTimeline({ entries }: ActivityTimelineProps) {
  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText size={24} className="text-[hsl(var(--muted-foreground))] mb-3" />
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Sem actividade registada.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {entries.map((entry, idx) => {
        const Icon = ACTION_ICONS[entry.action] ?? FileText;
        const isLast = idx === entries.length - 1;

        return (
          <div key={entry.id} className="flex gap-3">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              <div className="w-7 h-7 rounded-full bg-[hsl(var(--surface-raised))] border border-[hsl(var(--border))] flex items-center justify-center shrink-0 mt-0.5">
                <Icon size={12} className="text-[hsl(var(--muted))]" />
              </div>
              {!isLast && (
                <div className="w-px flex-1 bg-[hsl(var(--border))] my-1" />
              )}
            </div>

            {/* Content */}
            <div className={`pb-4 ${isLast ? "" : ""} pt-0.5`}>
              <p className="text-sm text-foreground font-medium">
                {ACTION_LABELS[entry.action]}
              </p>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
                {entry.actor_display_name} &middot;{" "}
                {formatDateTime(entry.occurred_at)}
              </p>
              {entry.metadata &&
                Object.keys(entry.metadata).length > 0 &&
                entry.action === "case_status_changed" && (
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                    {String(entry.metadata["from_status"])} &rarr;{" "}
                    {String(entry.metadata["to_status"])}
                  </p>
                )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
