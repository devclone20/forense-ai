import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ForensicDomainEnum = Enum("digital", "medico_legal", "financeiro", name="forensic_domain")
CaseStatusEnum = Enum(
    "aberto", "em_investigacao", "em_revisao", "fechado", "arquivado",
    name="case_status",
)
ConfidentialityLevelEnum = Enum(
    "normal", "reservado", "confidencial", "secreto",
    name="confidentiality_level",
)
CaseRoleEnum = Enum(
    "responsavel", "investigador", "supervisor", "consultor",
    name="case_role",
)
AuditActionEnum = Enum(
    "case_created", "case_updated", "case_status_changed",
    "member_added", "member_removed",
    "evidence_added",
    name="audit_action",
    create_constraint=False,
)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    case_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    forensic_domain: Mapped[str] = mapped_column(ForensicDomainEnum, nullable=False)
    status: Mapped[str] = mapped_column(
        CaseStatusEnum, nullable=False, default="aberto"
    )
    confidentiality: Mapped[str] = mapped_column(
        ConfidentialityLevelEnum, nullable=False, default="normal"
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    domain_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="cases")  # type: ignore[name-defined]
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]
        back_populates="owned_cases", foreign_keys=[owner_id]
    )
    members: Mapped[list["CaseMember"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    state_transitions: Mapped[list["CaseStateTransition"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class CaseMember(Base):
    __tablename__ = "case_members"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(CaseRoleEnum, nullable=False)
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    removed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    removed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    case: Mapped["Case"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        back_populates="memberships", foreign_keys=[user_id]
    )


class CaseStateTransition(Base):
    __tablename__ = "case_state_transitions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str] = mapped_column(CaseStatusEnum, nullable=False)
    to_status: Mapped[str] = mapped_column(CaseStatusEnum, nullable=False)
    transitioned_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    case: Mapped["Case"] = relationship(back_populates="state_transitions")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(AuditActionEnum, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    actor_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    hmac_signature: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CaseNumberSequence(Base):
    __tablename__ = "case_number_sequences"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    year: Mapped[int] = mapped_column(primary_key=True)
    counter: Mapped[int] = mapped_column(nullable=False, default=0)
