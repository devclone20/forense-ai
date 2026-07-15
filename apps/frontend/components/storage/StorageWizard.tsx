"use client";

import { useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type StorageBackend } from "@/lib/types";
import { api } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────────

interface BackendCard {
  id: StorageBackend;
  label: string;
  description: string;
}

const BACKENDS: BackendCard[] = [
  { id: "local",  label: "Local",          description: "Disco ou volume montado no servidor" },
  { id: "s3",     label: "AWS S3",          description: "Amazon Simple Storage Service" },
  { id: "r2",     label: "Cloudflare R2",  description: "Zero egress fees, S3-compatible" },
  { id: "minio",  label: "MinIO",           description: "Self-hosted, S3-compatible" },
  { id: "wasabi", label: "Wasabi",          description: "Hot cloud storage, low cost" },
];

interface StorageWizardProps {
  open: boolean;
  onClose: () => void;
  onConfigured: () => void;
}

type Step = 1 | 2 | 3;

// ── Credential form fields per backend ────────────────────────────────────────

function CredentialFields({
  backend,
  creds,
  onChange,
}: {
  backend: StorageBackend;
  creds: Record<string, string>;
  onChange: (key: string, value: string) => void;
}) {
  const field = (key: string, label: string, placeholder?: string, type = "text") => (
    <div key={key} className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-neutral-300">{label}</label>
      <Input
        type={type}
        placeholder={placeholder ?? label}
        value={creds[key] ?? ""}
        onChange={(e) => onChange(key, e.target.value)}
        className="bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500"
      />
    </div>
  );

  if (backend === "local") {
    return <>{field("base_path", "Caminho base", "/data/evidences")}</>;
  }

  const s3Fields = (
    <>
      {field("bucket", "Bucket")}
      {field("aws_access_key_id", "Access Key ID")}
      {field("aws_secret_access_key", "Secret Access Key", "", "password")}
      {field("region_name", "Região", "us-east-1")}
    </>
  );

  if (backend === "s3") return <>{s3Fields}</>;

  return (
    <>
      {s3Fields}
      {field("endpoint_url", "Endpoint URL", backend === "r2"
        ? "https://<account>.r2.cloudflarestorage.com"
        : backend === "minio"
          ? "http://localhost:9000"
          : `https://s3.us-east-1.wasabisys.com`)}
    </>
  );
}

// ── Component ──────────────────────────────────────────────────────────────────

export function StorageWizard({ open, onClose, onConfigured }: StorageWizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [backend, setBackend] = useState<StorageBackend | null>(null);
  const [creds, setCreds] = useState<Record<string, string>>({});
  const [maxFileGb, setMaxFileGb] = useState("");
  const [quotaGb, setQuotaGb] = useState("");
  const [noFileLimit, setNoFileLimit] = useState(false);
  const [noQuota, setNoQuota] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function resetAll() {
    setStep(1);
    setBackend(null);
    setCreds({});
    setMaxFileGb("");
    setQuotaGb("");
    setNoFileLimit(false);
    setNoQuota(false);
    setTestResult(null);
    setError(null);
  }

  async function handleTest() {
    if (!backend) return;
    setTesting(true);
    setTestResult(null);
    try {
      // Save config first (test requires it to exist)
      await api.post("/api/v1/admin/storage/config", {
        backend,
        credentials: creds,
        max_file_bytes: noFileLimit ? null : maxFileGb ? Math.round(parseFloat(maxFileGb) * 1e9) : null,
        quota_bytes: noQuota ? null : quotaGb ? Math.round(parseFloat(quotaGb) * 1e9) : null,
      });
      const res = await api.post<{ connected: boolean }>("/api/v1/admin/storage/config/test", {});
      setTestResult(res.connected);
    } catch {
      setTestResult(false);
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await api.post("/api/v1/admin/storage/config", {
        backend,
        credentials: creds,
        max_file_bytes: noFileLimit ? null : maxFileGb ? Math.round(parseFloat(maxFileGb) * 1e9) : null,
        quota_bytes: noQuota ? null : quotaGb ? Math.round(parseFloat(quotaGb) * 1e9) : null,
      });
      resetAll();
      onConfigured();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao guardar configuração.");
    } finally {
      setSaving(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-neutral-800">
          <div>
            <h2 className="text-lg font-semibold text-white">Configurar armazenamento</h2>
            <p className="text-sm text-neutral-400 mt-0.5">Passo {step} de 3</p>
          </div>
          <button
            onClick={() => { resetAll(); onClose(); }}
            className="text-neutral-400 hover:text-white transition-colors"
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-0.5 bg-neutral-800">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        {/* Body */}
        <div className="px-6 py-6 min-h-[280px]">

          {/* Step 1 — choose backend */}
          {step === 1 && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-neutral-400 mb-1">Onde guardar as evidências?</p>
              <div className="grid grid-cols-1 gap-2">
                {BACKENDS.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => setBackend(b.id)}
                    className={[
                      "flex items-start gap-3 p-3 rounded-lg border text-left transition-all",
                      backend === b.id
                        ? "border-blue-500 bg-blue-500/10"
                        : "border-neutral-700 hover:border-neutral-500 bg-neutral-800/50",
                    ].join(" ")}
                  >
                    <div className={[
                      "mt-0.5 h-4 w-4 rounded-full border-2 flex-shrink-0 transition-colors",
                      backend === b.id ? "border-blue-500 bg-blue-500" : "border-neutral-600",
                    ].join(" ")} />
                    <div>
                      <p className="text-sm font-medium text-white">{b.label}</p>
                      <p className="text-xs text-neutral-500">{b.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2 — credentials */}
          {step === 2 && backend && (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-neutral-400">Credenciais para <span className="text-white font-medium">{BACKENDS.find(b => b.id === backend)?.label}</span></p>
              <CredentialFields
                backend={backend}
                creds={creds}
                onChange={(k, v) => setCreds(prev => ({ ...prev, [k]: v }))}
              />
            </div>
          )}

          {/* Step 3 — limits */}
          {step === 3 && (
            <div className="flex flex-col gap-5">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-neutral-300">Limite por ficheiro (GB)</label>
                  <label className="flex items-center gap-1.5 text-xs text-neutral-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={noFileLimit}
                      onChange={e => setNoFileLimit(e.target.checked)}
                      className="accent-blue-500"
                    />
                    Sem limite
                  </label>
                </div>
                <Input
                  type="number"
                  placeholder="ex: 2"
                  value={noFileLimit ? "" : maxFileGb}
                  onChange={e => setMaxFileGb(e.target.value)}
                  disabled={noFileLimit}
                  className="bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 disabled:opacity-40"
                />
                <p className="text-xs text-neutral-500 mt-1">Sugestão: 2 GB para imagens de disco, 500 MB para documentos</p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-neutral-300">Quota total (GB)</label>
                  <label className="flex items-center gap-1.5 text-xs text-neutral-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={noQuota}
                      onChange={e => setNoQuota(e.target.checked)}
                      className="accent-blue-500"
                    />
                    Sem limite
                  </label>
                </div>
                <Input
                  type="number"
                  placeholder="ex: 500"
                  value={noQuota ? "" : quotaGb}
                  onChange={e => setQuotaGb(e.target.value)}
                  disabled={noQuota}
                  className="bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 disabled:opacity-40"
                />
                <p className="text-xs text-neutral-500 mt-1">Sugestão: 500 GB para casos pequenos, 5 TB para grandes investigações</p>
              </div>

              {/* Test connection */}
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTest}
                  disabled={testing}
                  className="border-neutral-700 text-neutral-300 hover:text-white"
                >
                  {testing ? "A testar…" : "Testar ligação"}
                </Button>
                {testResult === true && (
                  <span className="text-sm text-green-400">Ligação estabelecida com sucesso</span>
                )}
                {testResult === false && (
                  <span className="text-sm text-red-400">Falha na ligação — verifique as credenciais</span>
                )}
              </div>

              {error && <p className="text-sm text-red-400">{error}</p>}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-neutral-800">
          <Button
            variant="ghost"
            onClick={() => step > 1 ? setStep((s) => (s - 1) as Step) : (resetAll(), onClose())}
            className="text-neutral-400 hover:text-white"
          >
            {step === 1 ? "Cancelar" : "Voltar"}
          </Button>
          {step < 3 ? (
            <Button
              onClick={() => setStep((s) => (s + 1) as Step)}
              disabled={step === 1 && !backend}
              className="bg-blue-600 hover:bg-blue-500 text-white"
            >
              Continuar
            </Button>
          ) : (
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-500 text-white"
            >
              {saving ? "A guardar…" : "Confirmar"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
