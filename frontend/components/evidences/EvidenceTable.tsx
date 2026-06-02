"use client";

import { useState } from "react";
import Link from "next/link";
import { type Evidence, type EvidenceType } from "@/lib/types";
import { IntegrityBadge } from "./IntegrityBadge";
import { Badge } from "@/components/ui/badge";

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

const TYPE_LABELS: Record<EvidenceType, string> = {
  ficheiro_sistema:          "Ficheiro de sistema",
  imagem_disco:              "Imagem de disco",
  dump_memoria:              "Dump memória",
  log_sistema:               "Log sistema",
  capture_rede:              "Captura rede",
  artefacto_browser:         "Artefacto browser",
  registo_so:                "Registo SO",
  email_mensagem:            "Email/Mensagem",
  relatorio_medico:          "Relatório médico",
  fotografia_forense:        "Fotografia forense",
  resultado_laboratorial:    "Resultado lab.",
  registo_hospitalar:        "Registo hospitalar",
  laudo_pericial:            "Laudo pericial",
  extrato_bancario:          "Extrato bancário",
  fatura_recibo:             "Fatura/Recibo",
  contrato:                  "Contrato",
  registo_transacao:         "Transação",
  comunicacao_financeira:    "Comunicação fin.",
  relatorio_contabilistico:  "Relatório contab.",
  outro:                     "Outro",
};

type IntegrityStatus = "intact" | "tampered" | "unverified";

function evidenceIntegrity(_ev: Evidence): IntegrityStatus {
  // Without loading events, we default to unverified.
  // The detail page shows the real status.
  return "unverified";
}

// ── Filters ────────────────────────────────────────────────────────────────────

interface FiltersState {
  type: string;
  integrityStatus: IntegrityStatus | "";
}

// ── Component ──────────────────────────────────────────────────────────────────

interface EvidenceTableProps {
  caseId: string;
  evidences: Evidence[];
  loading?: boolean;
}

export function EvidenceTable({ caseId, evidences, loading = false }: EvidenceTableProps) {
  const [filters, setFilters] = useState<FiltersState>({ type: "", integrityStatus: "" });

  const filtered = evidences.filter(ev => {
    if (filters.type && ev.evidence_type !== filters.type) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center text-neutral-500 text-sm">
        A carregar evidências…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <select
          value={filters.type}
          onChange={e => setFilters(f => ({ ...f, type: e.target.value }))}
          className="rounded-md border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-sm text-white focus:outline-none"
          aria-label="Filtrar por tipo"
        >
          <option value="">Todos os tipos</option>
          {Object.entries(TYPE_LABELS).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>
        <span className="text-xs text-neutral-500 ml-auto">
          {filtered.length} {filtered.length === 1 ? "evidência" : "evidências"}
        </span>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-10 text-center text-neutral-500 text-sm">
          Nenhuma evidência encontrada.
        </div>
      ) : (
        <div className="rounded-xl border border-neutral-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-800/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">N.º</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">Título</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">Tamanho</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">Registado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-neutral-400">Integridade</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/70">
              {filtered.map(ev => (
                <tr
                  key={ev.id}
                  className="bg-neutral-900 hover:bg-neutral-800/60 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-neutral-400">
                    {ev.evidence_number}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/cases/${caseId}/evidences/${ev.id}`}
                      className="text-white hover:text-blue-400 transition-colors font-medium"
                    >
                      {ev.title}
                    </Link>
                    <p className="text-xs text-neutral-500 mt-0.5 truncate max-w-xs">{ev.original_filename}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="text-xs text-neutral-400 border-neutral-700">
                      {TYPE_LABELS[ev.evidence_type] ?? ev.evidence_type}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {formatBytes(ev.size_bytes)}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {new Date(ev.ingested_at).toLocaleDateString("pt-PT")}
                  </td>
                  <td className="px-4 py-3">
                    <IntegrityBadge status={evidenceIntegrity(ev)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
