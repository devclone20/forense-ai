import { Header } from "@/components/layout/Header";
import { CaseCard } from "@/components/cases/CaseCard";
import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS, STATUS_STYLES } from "@/lib/utils";
import type { Case, CaseStatus } from "@/lib/types";

// Mock data — replace with real API calls once auth is wired
const MOCK_CASES: Case[] = [
  {
    id: "1",
    organization_id: "org-1",
    case_number: "FOR-2026-00001",
    title: "Análise forense — dispositivo Android recuperado em busca domiciliária",
    description: "Extracção e análise de artefactos digitais de smartphone Xiaomi apreendido.",
    forensic_domain: "digital",
    status: "em_investigacao",
    confidentiality: "confidencial",
    owner_id: "user-abc123",
    tags: ["android", "apreensão"],
    domain_metadata: {},
    created_at: "2026-05-15T09:00:00Z",
    updated_at: "2026-05-20T14:30:00Z",
    closed_at: null,
    archived_at: null,
  },
  {
    id: "2",
    organization_id: "org-1",
    case_number: "FOR-2026-00002",
    title: "Perícia financeira — fraude em sociedade anónima",
    description: "Análise de movimentos bancários suspeitos e detecção de transferências irregulares.",
    forensic_domain: "financeiro",
    status: "em_revisao",
    confidentiality: "secreto",
    owner_id: "user-def456",
    tags: ["fraude", "banking"],
    domain_metadata: {},
    created_at: "2026-05-18T11:00:00Z",
    updated_at: "2026-05-29T16:00:00Z",
    closed_at: null,
    archived_at: null,
  },
  {
    id: "3",
    organization_id: "org-1",
    case_number: "FOR-2026-00003",
    title: "Autopsia digital — óbito suspeito",
    description: "Recolha e análise de evidências digitais associadas a morte em investigação.",
    forensic_domain: "medico_legal",
    status: "aberto",
    confidentiality: "reservado",
    owner_id: "user-ghi789",
    tags: ["óbito", "médico-legal"],
    domain_metadata: {},
    created_at: "2026-05-28T08:00:00Z",
    updated_at: "2026-05-28T08:00:00Z",
    closed_at: null,
    archived_at: null,
  },
];

const STATUS_ORDER: CaseStatus[] = [
  "aberto",
  "em_investigacao",
  "em_revisao",
  "fechado",
  "arquivado",
];

function countByStatus(cases: Case[], status: CaseStatus): number {
  return cases.filter((c) => c.status === status).length;
}

export default function DashboardPage() {
  return (
    <>
      <Header
        title="Dashboard"
        description="Visão geral dos casos activos e actividade recente"
      />

      {/* Status counters */}
      <div className="grid grid-cols-5 gap-3 mb-8">
        {STATUS_ORDER.map((status) => (
          <div
            key={status}
            className="rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4"
          >
            <p className="text-2xl font-semibold text-foreground tabular-nums">
              {countByStatus(MOCK_CASES, status)}
            </p>
            <div className="mt-2">
              <Badge className={STATUS_STYLES[status]}>
                {STATUS_LABELS[status]}
              </Badge>
            </div>
          </div>
        ))}
      </div>

      {/* Recent cases */}
      <div>
        <h2 className="text-sm font-semibold text-[hsl(var(--muted))] uppercase tracking-wider mb-3">
          Casos recentes
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {MOCK_CASES.slice(0, 5).map((c) => (
            <CaseCard key={c.id} case_={c} />
          ))}
        </div>
      </div>
    </>
  );
}
