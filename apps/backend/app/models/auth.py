"""
SQLAlchemy ORM models for auth-related tables:
  - Invitation
  - RefreshToken
  - AuthLog
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Mirror the SQL enum — SQLAlchemy will use the existing DB type
AuthEventEnum = Enum(
    "login_success",
    "login_failed",
    "login_locked",
    "logout",
    "mfa_setup",
    "mfa_success",
    "mfa_failed",
    "mfa_backup_used",
    "mfa_backup_regenerated",
    "token_refreshed",
    "token_revoked_all",
    "invite_created",
    "invite_accepted",
    "invite_revoked",
    "password_changed",
    "recovery_requested",
    "recovery_completed",
    "user_suspended",
    "role_changed",
    name="auth_event",
    create_type=False,  # already created by migration
)

GlobalRoleEnumRef = Enum(
    "admin", "perito", "investigador", "supervisor",
    "advogado", "consultor", "viewer",
    name="global_role",
    create_type=False,
)


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(GlobalRoleEnumRef, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    invited_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    organization: Mapped["Organization"] = relationship(foreign_keys=[organization_id])  # type: ignore[name-defined]
    inviter: Mapped["User"] = relationship(foreign_keys=[invited_by])  # type: ignore[name-defined]

    @property
    def is_valid(self) -> bool:
        from datetime import UTC
        now = datetime.now(UTC)
        exp = self.expires_at
        if exp.tzinfo is None:
            from datetime import timezone
            exp = exp.replace(tzinfo=timezone.utc)
        return (
            self.accepted_at is None
            and self.revoked_at is None
            and exp > now
        )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    family_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id"), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])  # type: ignore[name-defined]

    @property
    def is_active(self) -> bool:
        from datetime import UTC
        now = datetime.now(UTC)
        exp = self.expires_at
        if exp.tzinfo is None:
            from datetime import timezone
            exp = exp.replace(tzinfo=timezone.utc)
        return self.revoked_at is None and exp > now


class AuthLog(Base):
    __tablename__ = "auth_log"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    event_type: Mapped[str] = mapped_column(AuthEventEnum, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), nullable=False
    )
