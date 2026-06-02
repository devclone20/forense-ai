"""
Invite service — organisation member invitation flows.
"""
import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import password as pwd_domain
from app.repositories import auth_repository as repo

logger = logging.getLogger(__name__)


@dataclass
class InviteCreated:
    invite_id: uuid.UUID
    accept_link: str  # frontend URL — placeholder until email service is wired


@dataclass
class InviteValidation:
    valid: bool
    email: str | None = None
    role: str | None = None
    org_name: str | None = None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_invite(
    session: AsyncSession,
    org_id: uuid.UUID,
    email: str,
    role: str,
    invited_by_id: uuid.UUID,
) -> InviteCreated:
    """
    Create an invitation and return the (hashed) token persisted to the DB.
    The plaintext token is embedded in the accept link for the UI to display.
    Email delivery is stubbed — see TODO below.
    """
    # Get org's invite expiry setting
    from sqlalchemy import select
    from app.models.organization import Organization

    result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Organisation not found")

    token_plain = secrets.token_urlsafe(32)
    token_hash = _hash_token(token_plain)
    expires_at = datetime.now(UTC) + timedelta(days=org.invite_expiry_days)

    invite = await repo.create_invite(
        session,
        org_id=org_id,
        email=email,
        role=role,
        token_hash=token_hash,
        invited_by=invited_by_id,
        expires_at=expires_at,
    )

    await repo.append_auth_log(
        session,
        "invite_created",
        user_id=invited_by_id,
        org_id=org_id,
        metadata={"email": email, "role": role},
    )
    await session.commit()

    # TODO: send email via transactional email provider (Resend / SendGrid)
    accept_link = f"/invite/{token_plain}/accept"
    logger.info("invite_created: org=%s email=%s", org_id, email)
    return InviteCreated(invite_id=invite.id, accept_link=accept_link)


async def validate_invite(
    session: AsyncSession, token_plain: str
) -> InviteValidation:
    """Public endpoint — check if an invite token is still usable."""
    token_hash = _hash_token(token_plain)
    invite = await repo.get_invite_by_hash(session, token_hash)

    if invite is None or not invite.is_valid:
        return InviteValidation(valid=False)

    # Load org name for display
    from sqlalchemy import select
    from app.models.organization import Organization

    result = await session.execute(
        select(Organization).where(Organization.id == invite.organization_id)
    )
    org = result.scalar_one_or_none()

    return InviteValidation(
        valid=True,
        email=invite.email,
        role=invite.role,
        org_name=org.name if org else None,
    )


async def accept_invite(
    session: AsyncSession,
    token_plain: str,
    display_name: str,
    password: str,
) -> "User":  # type: ignore[name-defined]
    """
    Validate the token, create the user account, and mark the invite accepted.
    """
    from app.models.user import User

    token_hash = _hash_token(token_plain)
    invite = await repo.get_invite_by_hash(session, token_hash)

    if invite is None or not invite.is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invitation is invalid, expired, or already used")

    pw_hash = pwd_domain.hash_password(password)
    user = User(
        organization_id=invite.organization_id,
        email=invite.email,
        display_name=display_name,
        password_hash=pw_hash,
        global_role=invite.role,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    await repo.accept_invite(session, invite.id)
    await repo.append_auth_log(
        session,
        "invite_accepted",
        user_id=user.id,
        org_id=invite.organization_id,
        metadata={"email": invite.email},
    )
    await session.commit()
    return user


async def revoke_invite(
    session: AsyncSession,
    invite_id: uuid.UUID,
    revoked_by: uuid.UUID,
    org_id: uuid.UUID,
) -> None:
    invite = await repo.get_invite_by_id(session, invite_id)
    if invite is None or invite.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invitation not found")
    if invite.revoked_at is not None or invite.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invitation already resolved")

    await repo.revoke_invite(session, invite_id)
    await repo.append_auth_log(
        session,
        "invite_revoked",
        user_id=revoked_by,
        org_id=org_id,
        metadata={"invite_id": str(invite_id)},
    )
    await session.commit()
