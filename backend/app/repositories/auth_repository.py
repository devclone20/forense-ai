"""
Auth repository — all DB operations for auth tables.

Follows the same pattern as case_repository: thin data-access layer,
no business logic, no HTTP concerns.
"""
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuthLog, Invitation, RefreshToken
from app.models.user import User


# ── Invitations ──────────────────────────────────────────────────────────────

async def create_invite(
    session: AsyncSession,
    org_id: uuid.UUID,
    email: str,
    role: str,
    token_hash: str,
    invited_by: uuid.UUID,
    expires_at: datetime,
) -> Invitation:
    invite = Invitation(
        organization_id=org_id,
        email=email,
        role=role,
        token_hash=token_hash,
        invited_by=invited_by,
        expires_at=expires_at,
    )
    session.add(invite)
    await session.flush()
    return invite


async def get_invite_by_hash(
    session: AsyncSession, token_hash: str
) -> Invitation | None:
    result = await session.execute(
        select(Invitation).where(Invitation.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def get_invite_by_id(
    session: AsyncSession, invite_id: uuid.UUID
) -> Invitation | None:
    return await session.get(Invitation, invite_id)


async def accept_invite(session: AsyncSession, invite_id: uuid.UUID) -> None:
    await session.execute(
        update(Invitation)
        .where(Invitation.id == invite_id)
        .values(accepted_at=datetime.now(UTC))
    )


async def revoke_invite(session: AsyncSession, invite_id: uuid.UUID) -> None:
    await session.execute(
        update(Invitation)
        .where(Invitation.id == invite_id)
        .values(revoked_at=datetime.now(UTC))
    )


# ── Refresh Tokens ────────────────────────────────────────────────────────────

async def create_refresh_token(
    session: AsyncSession,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    token_hash: str,
    family_id: uuid.UUID,
    expires_at: datetime,
    ip: str | None,
    ua: str | None,
) -> RefreshToken:
    rt = RefreshToken(
        user_id=user_id,
        organization_id=org_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=expires_at,
        ip_address=ip,
        user_agent=ua,
    )
    session.add(rt)
    await session.flush()
    return rt


async def get_refresh_token(
    session: AsyncSession, token_hash: str
) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(
    session: AsyncSession,
    token_id: uuid.UUID,
    replaced_by: uuid.UUID | None = None,
) -> None:
    values: dict[str, Any] = {"revoked_at": datetime.now(UTC)}
    if replaced_by is not None:
        values["replaced_by"] = replaced_by
    await session.execute(
        update(RefreshToken).where(RefreshToken.id == token_id).values(**values)
    )


async def revoke_family(session: AsyncSession, family_id: uuid.UUID) -> None:
    """Revoke ALL tokens in a refresh-token family (theft detection)."""
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )


async def revoke_all_user_tokens(
    session: AsyncSession, user_id: uuid.UUID
) -> None:
    """Revoke every active refresh token for a user (suspend / password reset)."""
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )


# ── Auth Log ──────────────────────────────────────────────────────────────────

async def append_auth_log(
    session: AsyncSession,
    event_type: str,
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    ip: str | None = None,
    ua: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Append an immutable auth event to the log.
    Never includes password hashes or MFA secrets in metadata.
    """
    entry = AuthLog(
        event_type=event_type,
        user_id=user_id,
        organization_id=org_id,
        ip_address=ip,
        user_agent=ua,
        metadata=metadata or {},
    )
    session.add(entry)
    await session.flush()


# ── User helpers ──────────────────────────────────────────────────────────────

async def get_user_by_email(
    session: AsyncSession, email: str
) -> User | None:
    """Lookup a user by email — bypasses RLS (called pre-auth)."""
    result = await session.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    return await session.get(User, user_id)
