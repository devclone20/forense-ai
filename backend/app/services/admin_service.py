"""
Admin service — user management operations available to the admin role.
"""
import logging
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import auth_repository as repo

logger = logging.getLogger(__name__)


@dataclass
class UserSummary:
    id: uuid.UUID
    email: str
    display_name: str
    global_role: str
    is_active: bool
    mfa_enabled: bool
    last_login_at: str | None


async def list_users(session: AsyncSession, org_id: uuid.UUID) -> list[UserSummary]:
    result = await session.execute(
        select(User).where(User.organization_id == org_id).order_by(User.created_at)
    )
    users = result.scalars().all()
    return [
        UserSummary(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            global_role=u.global_role,
            is_active=u.is_active,
            mfa_enabled=u.mfa_enabled,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        )
        for u in users
    ]


async def change_role(
    session: AsyncSession,
    admin_id: uuid.UUID,
    target_user_id: uuid.UUID,
    new_role: str,
    org_id: uuid.UUID,
) -> None:
    target = await repo.get_user_by_id(session, target_user_id)
    if target is None or target.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Admins cannot change their own role")

    old_role = target.global_role
    target.global_role = new_role
    await repo.append_auth_log(
        session,
        "role_changed",
        user_id=admin_id,
        org_id=org_id,
        metadata={"target_user_id": str(target_user_id),
                  "old_role": old_role, "new_role": new_role},
    )
    await session.commit()


async def suspend_user(
    session: AsyncSession,
    admin_id: uuid.UUID,
    target_user_id: uuid.UUID,
    org_id: uuid.UUID,
) -> None:
    target = await repo.get_user_by_id(session, target_user_id)
    if target is None or target.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Admins cannot suspend themselves")

    target.is_active = False
    await repo.revoke_all_user_tokens(session, target_user_id)
    await repo.append_auth_log(
        session,
        "user_suspended",
        user_id=admin_id,
        org_id=org_id,
        metadata={"target_user_id": str(target_user_id)},
    )
    await session.commit()
    logger.info("user_suspended: target=%s by admin=%s", target_user_id, admin_id)
