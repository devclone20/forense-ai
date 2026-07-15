import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

GlobalRoleEnum = Enum(
    "admin",
    "perito",
    "investigador",
    "supervisor",
    "advogado",
    "consultor",
    "viewer",   # mantido para retrocompatibilidade — migração 009 fará rename gradual
    name="global_role",
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    global_role: Mapped[str] = mapped_column(
        GlobalRoleEnum, nullable=False, default="perito"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # MFA fields (added in migration 009)
    mfa_secret: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    mfa_backup_codes: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    # Account lockout
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    organization: Mapped["Organization"] = relationship(back_populates="users")  # type: ignore[name-defined]
    owned_cases: Mapped[list["Case"]] = relationship(  # type: ignore[name-defined]
        back_populates="owner", foreign_keys="Case.owner_id"
    )
    memberships: Mapped[list["CaseMember"]] = relationship(back_populates="user")  # type: ignore[name-defined]
