"""
Pydantic schemas for the Evidence Ingestion module.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────────
# Evidence
# ──────────────────────────────────────────────────────────────────────────────

EVIDENCE_TYPES = [
    "ficheiro_sistema", "imagem_disco", "dump_memoria", "log_sistema",
    "capture_rede", "artefacto_browser", "registo_so", "email_mensagem",
    "relatorio_medico", "fotografia_forense", "resultado_laboratorial",
    "registo_hospitalar", "laudo_pericial",
    "extrato_bancario", "fatura_recibo", "contrato",
    "registo_transacao", "comunicacao_financeira", "relatorio_contabilistico",
    "outro",
]


class EvidenceIngestMetadata(BaseModel):
    """Metadata submitted alongside the file upload."""
    title: str = Field(..., min_length=1, max_length=500)
    evidence_type: str = Field(...)
    description: str | None = None
    source_origin: str | None = None
    collected_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    domain_metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    actor_id: uuid.UUID | None
    actor_name: str
    ip_address: str | None
    metadata: dict[str, Any]
    occurred_at: datetime


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    case_id: uuid.UUID
    evidence_number: str
    title: str
    description: str | None
    evidence_type: str
    original_filename: str
    size_bytes: int
    mime_type: str
    sha256_hash: str
    source_origin: str | None
    collected_at: datetime | None
    ingested_by: uuid.UUID
    ingested_at: datetime
    tags: list[str]
    domain_metadata: dict[str, Any]


class EvidenceDetailResponse(EvidenceResponse):
    events: list[EvidenceEventResponse] = Field(default_factory=list)


class EvidenceListFilters(BaseModel):
    evidence_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    ingested_by: uuid.UUID | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class VerificationResult(BaseModel):
    evidence_id: uuid.UUID
    match: bool
    stored_hash: str
    computed_hash: str
    verified_at: datetime


# ──────────────────────────────────────────────────────────────────────────────
# Storage Config
# ──────────────────────────────────────────────────────────────────────────────

STORAGE_BACKENDS = ["local", "s3", "minio", "r2", "wasabi", "replicated"]


class StorageConfigCreate(BaseModel):
    backend: str
    credentials: dict[str, Any]  # plain — service encrypts before DB write
    max_file_bytes: int | None = None
    quota_bytes: int | None = None


class StorageConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    backend: str
    max_file_bytes: int | None
    quota_bytes: int | None
    used_bytes: int
    configured_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # credentials_encrypted is NEVER included in responses


class QuotaStatus(BaseModel):
    used_bytes: int
    quota_bytes: int | None
    percentage: float | None  # None when quota_bytes is None
    near_limit: bool  # True when percentage >= 90
