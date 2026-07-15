"use client";

import { useEffect, useState } from "react";
import { StorageWizard } from "@/components/storage/StorageWizard";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { type StorageConfig, type QuotaStatus } from "@/lib/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

const BACKEND_LABELS: Record<string, string> = {
  local:   "Local (disco)",
  s3:      "AWS S3",
  r2:      "Cloudflare R2",
  minio:   "MinIO",
  wasabi:  "Wasabi",
  replicated: "Replicado",
};

export default function StorageAdminPage() {
  const [config, setConfig] = useState<StorageConfig | null>(null);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [wizardOpen, setWizardOpen] = useState(false);

  async function fetchData() {
    setLoading(true);
    try {
      const [cfgRes, qRes] = await Promise.allSettled([
        api.get<StorageConfig>("/api/v1/admin/storage/config"),
        api.get<QuotaStatus>("/api/v1/admin/storage/quota"),
      ]);
      setConfig(cfgRes.status === "fulfilled" ? cfgRes.value : null);
      setQuota(qRes.status === "fulfilled" ? qRes.value : null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void fetchData(); }, []);

  // Open wizard automatically if not configured
  useEffect(() => {
    if (!loading && !config) {
      setWizardOpen(true);
    }
  }, [loading, config]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 text-neutral-500 text-sm">
        A carregar configuração de armazenamento…
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Armazenamento</h1>
          <p className="text-sm text-neutral-400 mt-0.5">Configuração do backend de evidências</p>
        </div>
        {config && (
          <Button
            onClick={() => setWizardOpen(true)}
            variant="outline"
            className="border-neutral-700 text-neutral-300 hover:text-white"
          >
            Alterar configuração
          </Button>
        )}
      </div>

      {!config ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center flex flex-col items-center gap-4">
          <div className="text-3xl" aria-hidden="true">🗄️</div>
          <p className="text-neutral-300 font-medium">Armazenamento não configurado</p>
          <p className="text-sm text-neutral-500">
            Configure o backend para começar a ingrir evidências.
          </p>
          <Button
            onClick={() => setWizardOpen(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white"
          >
            Configurar agora
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Current backend */}
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
            <div className="px-5 py-4 border-b border-neutral-800">
              <h2 className="text-sm font-semibold text-white">Backend activo</h2>
            </div>
            <dl className="divide-y divide-neutral-800/60">
              {[
                ["Backend", BACKEND_LABELS[config.backend] ?? config.backend],
                ["Configurado em", new Date(config.updated_at).toLocaleString("pt-PT")],
                ["Limite por ficheiro", config.max_file_bytes ? formatBytes(config.max_file_bytes) : "Sem limite"],
                ["Quota total", config.quota_bytes ? formatBytes(config.quota_bytes) : "Sem limite"],
              ].map(([label, value]) => (
                <div key={label} className="flex px-5 py-3 gap-4">
                  <dt className="text-xs text-neutral-500 w-40 flex-shrink-0">{label}</dt>
                  <dd className="text-sm text-neutral-300">{value}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Quota usage */}
          {quota && (
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-4">
              <h2 className="text-sm font-semibold text-white mb-3">Utilização de quota</h2>
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-neutral-400">
                  {formatBytes(quota.used_bytes)}
                  {quota.quota_bytes ? ` / ${formatBytes(quota.quota_bytes)}` : " utilizado"}
                </span>
                {quota.percentage !== null && (
                  <span className={quota.near_limit ? "text-amber-400 font-medium" : "text-neutral-500"}>
                    {quota.percentage.toFixed(0)}%
                  </span>
                )}
              </div>
              {quota.quota_bytes && (
                <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                  <div
                    className={[
                      "h-full rounded-full transition-all",
                      quota.near_limit ? "bg-amber-500" : "bg-blue-500",
                    ].join(" ")}
                    style={{ width: `${Math.min(quota.percentage ?? 0, 100)}%` }}
                  />
                </div>
              )}
              {quota.near_limit && (
                <p className="text-xs text-amber-400 mt-2">
                  Atenção: quota quase esgotada. Considere aumentar o limite ou arquivar casos antigos.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <StorageWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onConfigured={() => {
          setWizardOpen(false);
          void fetchData();
        }}
      />
    </div>
  );
}
