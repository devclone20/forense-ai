"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { EvidenceTable } from "@/components/evidences/EvidenceTable";
import { EvidenceDropzone } from "@/components/evidences/EvidenceDropzone";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { type Evidence, type PaginatedResponse, type QuotaStatus } from "@/lib/types";

function QuotaIndicator({ quota }: { quota: QuotaStatus }) {
  if (!quota.quota_bytes) {
    return (
      <div className="text-xs text-neutral-500">
        Armazenamento utilizado: <span className="text-neutral-300">{formatBytes(quota.used_bytes)}</span> · Sem limite de quota
      </div>
    );
  }
  const pct = quota.percentage ?? 0;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-neutral-400">
          {formatBytes(quota.used_bytes)} / {formatBytes(quota.quota_bytes)}
        </span>
        <span className={quota.near_limit ? "text-amber-400 font-medium" : "text-neutral-500"}>
          {pct.toFixed(0)}%
        </span>
      </div>
      <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
        <div
          className={[
            "h-full rounded-full transition-all",
            quota.near_limit ? "bg-amber-500" : "bg-blue-500",
          ].join(" ")}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export default function EvidencesPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [evidences, setEvidences] = useState<Evidence[]>([]);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  async function fetchData() {
    setLoading(true);
    try {
      const [evRes, qRes] = await Promise.all([
        api.get<PaginatedResponse<Evidence>>(`/api/v1/cases/${caseId}/evidences`),
        api.get<QuotaStatus>("/api/v1/admin/storage/quota").catch(() => null),
      ]);
      setEvidences(evRes.items);
      setQuota(qRes);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void fetchData(); }, [caseId]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Evidências</h1>
          <p className="text-sm text-neutral-400 mt-0.5">Gestão e cadeia de custódia</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const url = `/api/v1/cases/${caseId}/evidences/chain-of-custody`;
              window.open(`${process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000"}${url}`, "_blank");
            }}
            className="border-neutral-700 text-neutral-300 hover:text-white text-sm"
          >
            Exportar cadeia de custódia
          </Button>
          <Button
            onClick={() => setShowUpload(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white text-sm"
          >
            + Adicionar evidência
          </Button>
        </div>
      </div>

      {/* Quota indicator */}
      {quota && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3">
          <p className="text-xs font-medium text-neutral-400 mb-2">Quota de armazenamento</p>
          <QuotaIndicator quota={quota} />
        </div>
      )}

      {/* Table */}
      <EvidenceTable caseId={caseId} evidences={evidences} loading={loading} />

      {/* Upload modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-5 border-b border-neutral-800">
              <h2 className="text-lg font-semibold text-white">Adicionar evidência</h2>
              <button
                onClick={() => setShowUpload(false)}
                className="text-neutral-400 hover:text-white transition-colors"
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-5">
              <EvidenceDropzone
                caseId={caseId}
                quota={quota}
                onUploaded={() => {
                  setShowUpload(false);
                  void fetchData();
                }}
                onCancel={() => setShowUpload(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
