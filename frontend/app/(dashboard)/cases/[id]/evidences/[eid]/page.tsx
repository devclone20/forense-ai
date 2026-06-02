"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { type EvidenceDetail, type VerificationResult } from "@/lib/types";
import { IntegrityBadge } from "@/components/evidences/IntegrityBadge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function EventTypeLabel({ type }: { type: string }) {
  const map: Record<string, string> = {
    ingested:           "Registada",
    viewed:             "Consultada",
    downloaded:         "Descarregada",
    integrity_verified: "Integridade verificada",
    integrity_alert:    "ALERTA de integridade",
    chain_exported:     "Cadeia exportada",
  };
  const isAlert = type === "integrity_alert";
  return (
    <span className={["text-xs font-medium", isAlert ? "text-red-400" : "text-neutral-300"].join(" ")}>
      {map[type] ?? type}
    </span>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function EvidenceDetailPage() {
  const params = useParams<{ id: string; eid: string }>();
  const router = useRouter();
  const { id: caseId, eid: evidenceId } = params;

  const [evidence, setEvidence] = useState<EvidenceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.get<EvidenceDetail>(`/api/v1/cases/${caseId}/evidences/${evidenceId}`)
      .then(setEvidence)
      .catch(e => setError(e instanceof Error ? e.message : "Erro ao carregar evidência."))
      .finally(() => setLoading(false));
  }, [caseId, evidenceId]);

  async function handleVerify() {
    setVerifying(true);
    setError(null);
    try {
      const res = await api.post<VerificationResult>(
        `/api/v1/cases/${caseId}/evidences/${evidenceId}/verify`,
        {}
      );
      setVerificationResult(res);
      // Reload to get new event in timeline
      const fresh = await api.get<EvidenceDetail>(`/api/v1/cases/${caseId}/evidences/${evidenceId}`);
      setEvidence(fresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha na verificação.");
    } finally {
      setVerifying(false);
    }
  }

  function handleDownload() {
    const base = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";
    window.open(`${base}/api/v1/cases/${caseId}/evidences/${evidenceId}/download`, "_blank");
  }

  function handleExportChain() {
    const base = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";
    window.open(`${base}/api/v1/cases/${caseId}/evidences/chain-of-custody`, "_blank");
  }

  async function copyHash() {
    if (!evidence) return;
    await navigator.clipboard.writeText(evidence.sha256_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-neutral-500 text-sm">
        A carregar evidência…
      </div>
    );
  }

  if (error || !evidence) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <p className="text-red-400 text-sm">{error ?? "Evidência não encontrada."}</p>
        <Button variant="ghost" onClick={() => router.back()} className="mt-4 text-neutral-400">
          Voltar
        </Button>
      </div>
    );
  }

  // Determine integrity status from events
  const lastIntegrityEvent = [...evidence.events]
    .reverse()
    .find(e => e.event_type === "integrity_verified" || e.event_type === "integrity_alert");
  const integrityStatus =
    lastIntegrityEvent?.event_type === "integrity_alert"
      ? "tampered"
      : lastIntegrityEvent?.event_type === "integrity_verified"
        ? "intact"
        : "unverified";

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 flex flex-col gap-6">
      {/* Back link */}
      <Link
        href={`/cases/${caseId}/evidences`}
        className="text-sm text-neutral-400 hover:text-white transition-colors"
      >
        ← Evidências
      </Link>

      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-mono text-sm text-neutral-400">{evidence.evidence_number}</span>
          <Badge variant="outline" className="text-xs text-neutral-400 border-neutral-700">
            {evidence.evidence_type}
          </Badge>
          <IntegrityBadge status={integrityStatus} />
        </div>
        <h1 className="text-2xl font-bold text-white">{evidence.title}</h1>
        {evidence.description && (
          <p className="text-sm text-neutral-400">{evidence.description}</p>
        )}
      </div>

      {/* Verification banner */}
      {verificationResult && (
        <div className={[
          "rounded-lg px-4 py-3 text-sm border",
          verificationResult.match
            ? "bg-green-500/10 border-green-500/30 text-green-400"
            : "bg-red-500/10 border-red-500/30 text-red-400",
        ].join(" ")}>
          {verificationResult.match
            ? "Integridade confirmada — o ficheiro não foi alterado."
            : "ALERTA: O hash calculado diverge do hash registado. O ficheiro pode ter sido adulterado."}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          onClick={handleVerify}
          disabled={verifying}
          variant="outline"
          className="border-neutral-700 text-neutral-300 hover:text-white text-sm"
        >
          {verifying ? "A verificar…" : "Verificar integridade"}
        </Button>
        <Button
          onClick={handleDownload}
          variant="outline"
          className="border-neutral-700 text-neutral-300 hover:text-white text-sm"
        >
          Descarregar
        </Button>
        <Button
          onClick={handleExportChain}
          variant="outline"
          className="border-neutral-700 text-neutral-300 hover:text-white text-sm"
        >
          Exportar cadeia de custódia
        </Button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {/* Metadata grid */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-semibold text-white">Metadados</h2>
        </div>
        <dl className="divide-y divide-neutral-800/60">
          {[
            ["Ficheiro original", evidence.original_filename],
            ["Tamanho", formatBytes(evidence.size_bytes)],
            ["MIME type", evidence.mime_type],
            ["Fonte / Origem", evidence.source_origin ?? "—"],
            ["Data de recolha", evidence.collected_at
              ? new Date(evidence.collected_at).toLocaleString("pt-PT")
              : "—"],
            ["Registada em", new Date(evidence.ingested_at).toLocaleString("pt-PT")],
          ].map(([label, value]) => (
            <div key={label} className="flex px-5 py-3 gap-4">
              <dt className="text-xs text-neutral-500 w-36 flex-shrink-0">{label}</dt>
              <dd className="text-sm text-neutral-300">{value}</dd>
            </div>
          ))}
          {evidence.tags.length > 0 && (
            <div className="flex px-5 py-3 gap-4">
              <dt className="text-xs text-neutral-500 w-36 flex-shrink-0">Tags</dt>
              <dd className="flex gap-1 flex-wrap">
                {evidence.tags.map(t => (
                  <Badge key={t} variant="outline" className="text-xs border-neutral-700 text-neutral-400">
                    {t}
                  </Badge>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* SHA-256 */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-white">SHA-256</h2>
          <button
            onClick={copyHash}
            className="text-xs text-neutral-400 hover:text-white transition-colors"
          >
            {copied ? "Copiado!" : "Copiar"}
          </button>
        </div>
        <code className="block text-xs font-mono text-neutral-400 break-all">
          {evidence.sha256_hash}
        </code>
      </div>

      {/* Event timeline */}
      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-white">Timeline de acessos</h2>
        <div className="flex flex-col gap-1">
          {evidence.events.length === 0 && (
            <p className="text-xs text-neutral-500">Sem eventos registados.</p>
          )}
          {evidence.events.map(ev => (
            <div
              key={ev.id}
              className="flex items-start gap-3 rounded-lg px-4 py-3 bg-neutral-900 border border-neutral-800/70"
            >
              <div className="flex-1 flex flex-col gap-0.5">
                <EventTypeLabel type={ev.event_type} />
                <span className="text-xs text-neutral-500">
                  {ev.actor_name}
                  {ev.ip_address ? ` · ${ev.ip_address}` : ""}
                </span>
              </div>
              <time className="text-xs text-neutral-500 flex-shrink-0">
                {new Date(ev.occurred_at).toLocaleString("pt-PT")}
              </time>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
