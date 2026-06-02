"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { type EvidenceIngestMetadata, type EvidenceType } from "@/lib/types";

// ── Evidence type groups ──────────────────────────────────────────────────────

const TYPE_GROUPS: { label: string; types: { value: EvidenceType; label: string }[] }[] = [
  {
    label: "Digital",
    types: [
      { value: "ficheiro_sistema",   label: "Ficheiro de sistema" },
      { value: "imagem_disco",       label: "Imagem de disco" },
      { value: "dump_memoria",       label: "Dump de memória" },
      { value: "log_sistema",        label: "Log de sistema" },
      { value: "capture_rede",       label: "Captura de rede" },
      { value: "artefacto_browser",  label: "Artefacto de browser" },
      { value: "registo_so",         label: "Registo de SO" },
      { value: "email_mensagem",     label: "Email / Mensagem" },
    ],
  },
  {
    label: "Médico-legal",
    types: [
      { value: "relatorio_medico",        label: "Relatório médico" },
      { value: "fotografia_forense",      label: "Fotografia forense" },
      { value: "resultado_laboratorial",  label: "Resultado laboratorial" },
      { value: "registo_hospitalar",      label: "Registo hospitalar" },
      { value: "laudo_pericial",          label: "Laudo pericial" },
    ],
  },
  {
    label: "Financeiro",
    types: [
      { value: "extrato_bancario",         label: "Extrato bancário" },
      { value: "fatura_recibo",            label: "Fatura / Recibo" },
      { value: "contrato",                 label: "Contrato" },
      { value: "registo_transacao",        label: "Registo de transação" },
      { value: "comunicacao_financeira",   label: "Comunicação financeira" },
      { value: "relatorio_contabilistico", label: "Relatório contabilístico" },
    ],
  },
  {
    label: "Outro",
    types: [{ value: "outro", label: "Outro" }],
  },
];

// ── Domain-specific extra fields ──────────────────────────────────────────────

function ExtraFields({
  type,
  extra,
  onChange,
}: {
  type: EvidenceType;
  extra: Record<string, string>;
  onChange: (k: string, v: string) => void;
}) {
  const field = (k: string, label: string, placeholder?: string) => (
    <div key={k} className="flex flex-col gap-1">
      <label className="text-xs text-neutral-400">{label}</label>
      <Input
        placeholder={placeholder ?? label}
        value={extra[k] ?? ""}
        onChange={e => onChange(k, e.target.value)}
        className="bg-neutral-800 border-neutral-700 text-white text-sm placeholder:text-neutral-500"
      />
    </div>
  );

  if (type === "imagem_disco") {
    return (
      <>
        {field("acquisition_tool", "Ferramenta de aquisição", "ex: FTK Imager")}
        {field("filesystem", "Filesystem", "ex: NTFS")}
      </>
    );
  }
  if (type === "capture_rede") {
    return <>{field("interface", "Interface de rede", "ex: eth0")}</>;
  }
  return null;
}

// ── Component ──────────────────────────────────────────────────────────────────

interface MetadataFormProps {
  filename: string;
  onSubmit: (metadata: EvidenceIngestMetadata) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function MetadataForm({ filename, onSubmit, onCancel, loading = false }: MetadataFormProps) {
  const [title, setTitle] = useState(filename);
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("outro");
  const [description, setDescription] = useState("");
  const [sourceOrigin, setSourceOrigin] = useState("");
  const [collectedAt, setCollectedAt] = useState("");
  const [tags, setTags] = useState("");
  const [extra, setExtra] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) { setError("O título é obrigatório."); return; }

    const metadata: EvidenceIngestMetadata = {
      title: title.trim(),
      evidence_type: evidenceType,
      description: description || undefined,
      source_origin: sourceOrigin || undefined,
      collected_at: collectedAt || undefined,
      tags: tags.split(",").map(t => t.trim()).filter(Boolean),
      domain_metadata: extra,
    };

    setError(null);
    try {
      await onSubmit(metadata);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar metadados.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="px-1 py-0.5 bg-neutral-800 rounded text-xs text-neutral-400 font-mono truncate">
        {filename}
      </div>

      {/* Title */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-neutral-300">
          Título <span className="text-red-400">*</span>
        </label>
        <Input
          value={title}
          onChange={e => setTitle(e.target.value)}
          className="bg-neutral-800 border-neutral-700 text-white"
        />
      </div>

      {/* Type */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-neutral-300">
          Tipo <span className="text-red-400">*</span>
        </label>
        <select
          value={evidenceType}
          onChange={e => { setEvidenceType(e.target.value as EvidenceType); setExtra({}); }}
          className="w-full rounded-md border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {TYPE_GROUPS.map(g => (
            <optgroup key={g.label} label={g.label}>
              {g.types.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Domain-specific fields */}
      <ExtraFields type={evidenceType} extra={extra} onChange={(k, v) => setExtra(p => ({ ...p, [k]: v }))} />

      {/* Description */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-neutral-300">Descrição</label>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white placeholder:text-neutral-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Source + collected at */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-neutral-300">Fonte / Origem</label>
          <Input
            value={sourceOrigin}
            onChange={e => setSourceOrigin(e.target.value)}
            placeholder="ex: Disco apreendido"
            className="bg-neutral-800 border-neutral-700 text-white text-sm placeholder:text-neutral-500"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-neutral-300">Data de recolha</label>
          <Input
            type="datetime-local"
            value={collectedAt}
            onChange={e => setCollectedAt(e.target.value)}
            className="bg-neutral-800 border-neutral-700 text-white text-sm"
          />
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-neutral-300">Tags (separadas por vírgula)</label>
        <Input
          value={tags}
          onChange={e => setTags(e.target.value)}
          placeholder="ex: suspeito-a, disco-principal"
          className="bg-neutral-800 border-neutral-700 text-white text-sm placeholder:text-neutral-500"
        />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="ghost" onClick={onCancel} className="text-neutral-400 hover:text-white">
          Cancelar
        </Button>
        <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-500 text-white">
          {loading ? "A enviar…" : "Registar evidência"}
        </Button>
      </div>
    </form>
  );
}
