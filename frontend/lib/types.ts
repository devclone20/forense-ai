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
