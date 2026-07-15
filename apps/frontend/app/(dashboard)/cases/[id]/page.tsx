import { ActivityTimeline } from "@/components/cases/ActivityTimeline";
import { Badge } from "@/components/ui/badge";
import {
  DOMAIN_LABELS,
  DOMAIN_STYLES,
  STATUS_LABELS,
  STATUS_STYLES,
  formatDate,
} from "@/lib/utils";
import type { AuditLogEntry, Case } from "@/lib/types";
import { Calendar, Hash, Shield } from "lucide-react";

// In production, fetch these server-side using Next.js server components
// and the api client with a server-side token.
async function getCase(id: string): Promise<Case | null> {
  // TODO: replace with server-side fetch from API
  return {
    id,
    organization_id: "org-1",
    case_number: "FOR-2026-00001",
    title: "Análise forense — dispositivo Android recuperado em busca domiciliária",
    description:
      "Extracção e análise de artefactos digitais de smartphone Xiaomi apreendido durante operação policial. Inclui análise de mensagens, localização GPS e fotografias.",
    forensic_domain: "digital",
    status: "em_investigacao",
    confidentiality: "confidencial",
    owner_id: "user-abc123",
    tags: ["android", "apreensão", "mensagens"],
    domain_metadata: {},
    created_at: "2026-05-15T09:00:00Z",
    updated_at: "2026-05-20T14:30:00Z",
    closed_at: null,
    archived_at: null,
  };
}

async function getCaseActivity(id: string): Promise<AuditLogEntry[]> {
  // TODO: replace with server-side fetch
  void id;
  return [
    {
      id: "a1",
      action: "case_created",
      actor_id: "user-abc123",
      actor_display_name: "Inspector Silva",
      metadata: { title: "Análise forense..." },
      occurred_at: "2026-05-15T09:00:00Z",
      ip_address: null,
    },
    {
      id: "a2",
      action: "case_status_changed",
      actor_id: "user-abc123",
      actor_display_name: "Inspector Silva",
      metadata: { from_status: "aberto", to_status: "em_investigacao" },
      occurred_at: "2026-05-16T10:30:00Z",
      ip_address: null,
    },
  ];
}

const CONFIDENTIALITY_STYLES: Record<string, string> = {
  normal: "bg-neutral-500/10 text-neutral-400 border border-neutral-500/20",
  reservado: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  confidencial: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  secreto: "bg-red-500/10 text-red-400 border border-red-500/20",
};

export default async function CaseDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [case_, activity] = await Promise.all([
    getCase(params.id),
    getCaseActivity(params.id),
  ]);

  if (!case_) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Caso não encontrado.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-1.5 text-xs text-[hsl(var(--muted-foreground))] mb-2">
          <Hash size={11} strokeWidth={2.5} />
          <span className="font-mono tracking-wider">{case_.case_number}</span>
        </div>
        <h1 className="text-2xl font-semibold text-foreground leading-snug tracking-tight mb-3">
          {case_.title}
        </h1>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge className={DOMAIN_STYLES[case_.forensic_domain]}>
            {DOMAIN_LABELS[case_.forensic_domain]}
          </Badge>
          <Badge className={STATUS_STYLES[case_.status]}>
            {STATUS_LABELS[case_.status]}
          </Badge>
          <Badge className={CONFIDENTIALITY_STYLES[case_.confidentiality] ?? ""}>
            <Shield size={10} className="mr-1" />
            {case_.confidentiality.charAt(0).toUpperCase() +
              case_.confidentiality.slice(1)}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main content */}
        <div className="col-span-2 space-y-5">
          {/* Description */}
          <div className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-5">
            <h2 className="text-xs font-semibold text-[hsl(var(--muted))] uppercase tracking-wider mb-3">
              Descrição
            </h2>
            <p className="text-sm text-[hsl(var(--muted-foreground))] leading-relaxed">
              {case_.description ?? "Sem descrição."}
            </p>
          </div>

          {/* Tags */}
          {case_.tags.length > 0 && (
            <div className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-5">
              <h2 className="text-xs font-semibold text-[hsl(var(--muted))] uppercase tracking-wider mb-3">
                Tags
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {case_.tags.map((tag) => (
                  <Badge
                    key={tag}
                    className="bg-[hsl(var(--surface-raised))] text-[hsl(var(--muted))] border border-[hsl(var(--border))]"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: meta + activity */}
        <div className="col-span-1 space-y-5">
          {/* Meta */}
          <div className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-5">
            <h2 className="text-xs font-semibold text-[hsl(var(--muted))] uppercase tracking-wider mb-3">
              Detalhes
            </h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-[hsl(var(--muted-foreground))]">Criado</dt>
                <dd className="text-foreground">{formatDate(case_.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[hsl(var(--muted-foreground))]">Actualizado</dt>
                <dd className="text-foreground">{formatDate(case_.updated_at)}</dd>
              </div>
              {case_.closed_at && (
                <div className="flex justify-between">
                  <dt className="text-[hsl(var(--muted-foreground))]">Fechado</dt>
                  <dd className="text-foreground">{formatDate(case_.closed_at)}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Activity */}
          <div className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-5">
            <h2 className="text-xs font-semibold text-[hsl(var(--muted))] uppercase tracking-wider mb-4">
              Actividade
            </h2>
            <ActivityTimeline entries={activity} />
          </div>
        </div>
      </div>
    </div>
  );
}
