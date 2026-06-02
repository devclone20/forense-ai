// Types aligned with Pydantic schemas in backend/app/schemas/

export type ForensicDomain = "digital" | "medico_legal" | "financeiro";
export type CaseStatus =
  | "aberto"
  | "em_investigacao"
  | "em_revisao"
  | "fechado"
  | "arquivado";
export type ConfidentialityLevel =
  | "normal"
  | "reservado"
  | "confidencial"
  | "secreto";
export type CaseRole =
  | "responsavel"
  | "investigador"
  | "supervisor"
  | "consultor";
export type AuditAction =
  | "case_created"
  | "case_updated"
  | "case_status_changed"
  | "member_added"
  | "member_removed";

export interface Case {
  id: string;
  organization_id: string;
  case_number: string;
  title: string;
  description: string | null;
  forensic_domain: ForensicDomain;
  status: CaseStatus;
  confidentiality: ConfidentialityLevel;
  owner_id: string;
  tags: string[];
  domain_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  archived_at: string | null;
}

export interface CaseMember {
  id: string;
  case_id: string;
  user_id: string;
  role: CaseRole;
  assigned_by: string;
  assigned_at: string;
  removed_at: string | null;
  removed_by: string | null;
}

export interface AuditLogEntry {
  id: string;
  action: AuditAction;
  actor_id: string;
  actor_display_name: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
  ip_address: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CaseCreate {
  title: string;
  description?: string;
  forensic_domain: ForensicDomain;
  confidentiality?: ConfidentialityLevel;
  tags?: string[];
  domain_metadata?: Record<string, unknown>;
}

export interface CaseUpdate {
  title?: string;
  description?: string;
  confidentiality?: ConfidentialityLevel;
  tags?: string[];
  domain_metadata?: Record<string, unknown>;
}

// ── Evidence ──────────────────────────────────────────────────────────────────

export type EvidenceType =
  | "ficheiro_sistema"
  | "imagem_disco"
  | "dump_memoria"
  | "log_sistema"
  | "capture_rede"
  | "artefacto_browser"
  | "registo_so"
  | "email_mensagem"
  | "relatorio_medico"
  | "fotografia_forense"
  | "resultado_laboratorial"
  | "registo_hospitalar"
  | "laudo_pericial"
  | "extrato_bancario"
  | "fatura_recibo"
  | "contrato"
  | "registo_transacao"
  | "comunicacao_financeira"
  | "relatorio_contabilistico"
  | "outro";

export interface EvidenceEvent {
  id: string;
  event_type: string;
  actor_id: string | null;
  actor_name: string;
  ip_address: string | null;
  metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface Evidence {
  id: string;
  organization_id: string;
  case_id: string;
  evidence_number: string;
  title: string;
  description: string | null;
  evidence_type: EvidenceType;
  original_filename: string;
  size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  source_origin: string | null;
  collected_at: string | null;
  ingested_by: string;
  ingested_at: string;
  tags: string[];
  domain_metadata: Record<string, unknown>;
}

export interface EvidenceDetail extends Evidence {
  events: EvidenceEvent[];
}

export interface EvidenceIngestMetadata {
  title: string;
  evidence_type: EvidenceType;
  description?: string;
  source_origin?: string;
  collected_at?: string;
  tags?: string[];
  domain_metadata?: Record<string, unknown>;
}

export interface VerificationResult {
  evidence_id: string;
  match: boolean;
  stored_hash: string;
  computed_hash: string;
  verified_at: string;
}

// ── Storage Config ─────────────────────────────────────────────────────────────

export type StorageBackend = "local" | "s3" | "minio" | "r2" | "wasabi";

export interface StorageConfig {
  id: string;
  organization_id: string;
  backend: StorageBackend;
  max_file_bytes: number | null;
  quota_bytes: number | null;
  used_bytes: number;
  configured_by: string;
  created_at: string;
  updated_at: string;
}

export interface QuotaStatus {
  used_bytes: number;
  quota_bytes: number | null;
  percentage: number | null;
  near_limit: boolean;
}
