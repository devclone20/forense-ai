"use client";

import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { CaseStatus, ForensicDomain } from "@/lib/types";
import { Search } from "lucide-react";

export interface CaseFiltersValue {
  status: CaseStatus | "";
  forensic_domain: ForensicDomain | "";
  search: string;
}

interface CaseFiltersProps {
  value: CaseFiltersValue;
  onChange: (v: CaseFiltersValue) => void;
}

export function CaseFilters({ value, onChange }: CaseFiltersProps) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search
          size={14}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]"
        />
        <Input
          value={value.search}
          onChange={(e) => onChange({ ...value, search: e.target.value })}
          placeholder="Pesquisar casos..."
          className="pl-8"
        />
      </div>

      {/* Status */}
      <div className="w-44">
        <Select
          value={value.status}
          onChange={(e) =>
            onChange({ ...value, status: e.target.value as CaseStatus | "" })
          }
        >
          <option value="">Todos os estados</option>
          <option value="aberto">Aberto</option>
          <option value="em_investigacao">Em Investigação</option>
          <option value="em_revisao">Em Revisão</option>
          <option value="fechado">Fechado</option>
          <option value="arquivado">Arquivado</option>
        </Select>
      </div>

      {/* Domain */}
      <div className="w-44">
        <Select
          value={value.forensic_domain}
          onChange={(e) =>
            onChange({
              ...value,
              forensic_domain: e.target.value as ForensicDomain | "",
            })
          }
        >
          <option value="">Todos os domínios</option>
          <option value="digital">Digital</option>
          <option value="medico_legal">Médico-Legal</option>
          <option value="financeiro">Financeiro</option>
        </Select>
      </div>
    </div>
  );
}
