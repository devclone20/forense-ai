"""
SQLAlchemy ORM models for the Evidence Ingestion module.

Tables: storage_configs, evidences, evidence_events, evidence_number_sequences
"""
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

StorageBackendEnum = Enum(
    "local", "s3", "minio", "r2", "wasabi", "replicated",
    name="storage_backend",
    create_constraint=False,   # constraint lives in the DB already via migration
)

EvidenceTypeEnum = Enum(
    "ficheiro_sistema", "imagem_disco", "dump_memoria", "log_sistema",
    "capture_rede", "artefacto_browser", "registo_so", "email_mensagem",
    "relatorio_medico", "fotografia_forense", "resultado_laboratorial",
    "registo_hospitalar", "laudo_pericial",
    "extrato_bancario", "fatura_recibo", "contrato",
    "registo_transacao", "comunicacao_financeira", "relatorio_contabilistico",
    "outro",
    name="evidence_type",
    create_constraint=False,
)

EvidenceEventTypeEnum = Enum(
    "ingested", "viewed", "downloaded",
    "integrity_verified", "integrity_alert", "chain_exported",
    name="evidence_event_type",
    create_constraint=False,
)


# ──────────────────────────────────────────────────────────────────────────────
# StorageConfig
# ──────────────────────────────────────────────────────────────────────────────

class StorageConfig(Base):
    __tablename__ = "storage_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    backend: Mapped[str] = mapped_column(Text, nullable=False)
    credentials_encrypted: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    max_file_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    quota_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    used_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    quota_alert_sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    configured_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )


# ──────────────────────────────────────────────────────────────────────────────
# Evidence
# ──────────────────────────────────────────────────────────────────────────────

class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    evidence_number: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[str] = mapped_column(EvidenceTypeEnum, nullable=False)
    storage_ref: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_origin: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ingested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    domain_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    events: Mapped[list["EvidenceEvent"]] = relationship(
        back_populates="evidence",
        order_by="EvidenceEvent.occurred_at",
    )


# ──────────────────────────────────────────────────────────────────────────────
# EvidenceEvent (append-only)
# ──────────────────────────────────────────────────────────────────────────────

class EvidenceEvent(Base):
    __tablename__ = "evidence_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidences.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(EvidenceEventTypeEnum, nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    evidence: Mapped["Evidence"] = relationship(back_populates="events")


# ──────────────────────────────────────────────────────────────────────────────
# EvidenceNumberSequence
# ──────────────────────────────────────────────────────────────────────────────

class EvidenceNumberSequence(Base):
    __tablename__ = "evidence_number_sequences"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    counter: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
