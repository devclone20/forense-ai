"use client";

import { CaseCard } from "@/components/cases/CaseCard";
import { CaseFilters, type CaseFiltersValue } from "@/components/cases/CaseFilters";
import { CreateCaseModal } from "@/components/cases/CreateCaseModal";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import type { Case, CaseCreate } from "@/lib/types";
import { Plus } from "lucide-react";
import { useMemo, useState } from "react";

// Mock data — replace with API fetch using useEffect + api.get<PaginatedResponse<Case>>
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
    tags: ["óbito"],
    domain_metadata: {},
    created_at: "2026-05-28T08:00:00Z",
    updated_at: "2026-05-28T08:00:00Z",
    closed_at: null,
    archived_at: null,
  },
];

export default function CasesPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [filters, setFilters] = useState<CaseFiltersValue>({
    status: "",
    forensic_domain: "",
    search: "",
  });
  const [cases, setCases] = useState<Case[]>(MOCK_CASES);

  const filtered = useMemo(() => {
    return cases.filter((c) => {
      if (filters.status && c.status !== filters.status) return false;
      if (filters.forensic_domain && c.forensic_domain !== filters.forensic_domain) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        if (
          !c.title.toLowerCase().includes(q) &&
          !c.case_number.toLowerCase().includes(q) &&
          !(c.description ?? "").toLowerCase().includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [cases, filters]);

  async function handleCreate(data: CaseCreate): Promise<void> {
    // TODO: replace with api.post<Case>("/api/v1/cases", data)
    const mock: Case = {
      id: String(Date.now()),
      organization_id: "org-1",
      case_number: `FOR-2026-${String(cases.length + 1).padStart(5, "0")}`,
      title: data.title,
      description: data.description ?? null,
      forensic_domain: data.forensic_domain,
      status: "aberto",
      confidentiality: data.confidentiality ?? "normal",
      owner_id: "current-user",
      tags: data.tags ?? [],
      domain_metadata: data.domain_metadata ?? {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      closed_at: null,
      archived_at: null,
    };
    setCases((prev) => [mock, ...prev]);
  }

  return (
    <>
      <Header
        title="Casos"
        description={`${filtered.length} caso${filtered.length !== 1 ? "s" : ""}`}
        actions={
          <Button onClick={() => setCreateOpen(true)} size="md">
            <Plus size={14} strokeWidth={2.5} />
            Novo caso
          </Button>
        }
      />

      <div className="mb-5">
        <CaseFilters value={filters} onChange={setFilters} />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Nenhum caso encontrado com estes filtros.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((c) => (
            <CaseCard key={c.id} case_={c} />
          ))}
        </div>
      )}

      <CreateCaseModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreate}
      />
    </>
  );
}
