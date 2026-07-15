"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { MetadataForm } from "./MetadataForm";
import { type EvidenceIngestMetadata, type QuotaStatus } from "@/lib/types";
// api is available via direct fetch in this component (XHR for progress tracking)

interface FileUploadState {
  file: File;
  progress: number;
  error: string | null;
  done: boolean;
}

interface EvidenceDropzoneProps {
  caseId: string;
  quota: QuotaStatus | null;
  onUploaded: () => void;
  onCancel: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function EvidenceDropzone({ caseId, quota, onUploaded, onCancel }: EvidenceDropzoneProps) {
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<FileUploadState | null>(null);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length === 0) return;
      const file = accepted[0];

      // Client-side size guard
      if (quota?.quota_bytes && quota.used_bytes + file.size > quota.quota_bytes) {
        alert("Quota de armazenamento excedida. Não é possível enviar este ficheiro.");
        return;
      }

      setPendingFile(file);
      setUploadState(null);
    },
    [quota]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: !!pendingFile || uploading,
  });

  async function handleIngest(metadata: EvidenceIngestMetadata) {
    if (!pendingFile) return;
    setUploading(true);
    setUploadState({ file: pendingFile, progress: 0, error: null, done: false });

    const formData = new FormData();
    formData.append("file", pendingFile);
    formData.append("metadata_json", JSON.stringify(metadata));

    try {
      // We use fetch directly here so we can track upload progress via XHR
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const token = typeof window !== "undefined"
          ? localStorage.getItem("forense_token")
          : null;

        const apiBase = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";
        xhr.open("POST", `${apiBase}/api/v1/cases/${caseId}/evidences`);
        if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            setUploadState(s => s ? { ...s, progress: pct } : s);
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            setUploadState(s => s ? { ...s, progress: 100, done: true } : s);
            resolve();
          } else {
            reject(new Error(xhr.responseText || "Upload falhou."));
          }
        });

        xhr.addEventListener("error", () => reject(new Error("Erro de rede.")));
        xhr.send(formData);
      });

      onUploaded();
    } catch (e) {
      setUploadState(s => s
        ? { ...s, error: e instanceof Error ? e.message : "Erro desconhecido." }
        : s
      );
    } finally {
      setUploading(false);
    }
  }

  // — Quota warning bar —
  const quotaWarning = quota?.near_limit
    ? `Atenção: ${quota.percentage?.toFixed(0)}% da quota utilizada`
    : null;

  return (
    <div className="flex flex-col gap-4">
      {quotaWarning && (
        <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 px-4 py-2.5 text-sm text-amber-400">
          {quotaWarning}
        </div>
      )}

      {!pendingFile && (
        <div
          {...getRootProps()}
          className={[
            "rounded-xl border-2 border-dashed px-8 py-12 text-center cursor-pointer transition-colors",
            isDragActive
              ? "border-blue-500 bg-blue-500/10"
              : "border-neutral-700 hover:border-neutral-500 bg-neutral-800/40",
          ].join(" ")}
          role="button"
          aria-label="Área de drag-and-drop para upload de ficheiros"
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3" aria-hidden="true">
            {isDragActive ? "⬇" : "📁"}
          </div>
          <p className="text-sm font-medium text-neutral-300">
            {isDragActive ? "Soltar aqui…" : "Arrastar ficheiro ou clicar para seleccionar"}
          </p>
          <p className="text-xs text-neutral-500 mt-1">
            Qualquer tipo de ficheiro aceite
          </p>
        </div>
      )}

      {uploadState && (
        <div className="rounded-lg bg-neutral-800 border border-neutral-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-300 font-medium truncate max-w-xs">
              {uploadState.file.name}
            </span>
            <span className="text-xs text-neutral-500">{formatBytes(uploadState.file.size)}</span>
          </div>
          <div className="h-1.5 bg-neutral-700 rounded-full overflow-hidden">
            <div
              className={[
                "h-full rounded-full transition-all duration-200",
                uploadState.done ? "bg-green-500" : "bg-blue-500",
              ].join(" ")}
              style={{ width: `${uploadState.progress}%` }}
            />
          </div>
          {uploadState.error && (
            <p className="text-xs text-red-400 mt-2">{uploadState.error}</p>
          )}
        </div>
      )}

      {pendingFile && !uploading && !uploadState?.done && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Metadados da evidência</h3>
          <MetadataForm
            filename={pendingFile.name}
            onSubmit={handleIngest}
            onCancel={() => { setPendingFile(null); setUploadState(null); onCancel(); }}
            loading={uploading}
          />
        </div>
      )}
    </div>
  );
}
