"""
Admin users API endpoints.

GET   /api/v1/admin/users
PATCH /api/v1/admin/users/:id/role
POST  /api/v1/admin/users/:id/suspend
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import AuthUser, DBSession
from app.services import admin_service

router = APIRouter(prefix="/admin/users", tags=["admin"])


class UserSummaryResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    global_role: str
    is_active: bool
    mfa_enabled: bool
    last_login_at: str | None


class ChangeRoleRequest(BaseModel):
    role: str


def _require_admin(current_user: AuthUser) -> None:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin role required")


@router.get("", response_model=list[UserSummaryResponse])
async def list_users(
    current_user: AuthUser,
    session: DBSession,
) -> list[UserSummaryResponse]:
    _require_admin(current_user)
    summaries = await admin_service.list_users(session, current_user.org_id)
    return [UserSummaryResponse(**s.__dict__) for s in summaries]


@router.patch("/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def change_role(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    _require_admin(current_user)
    await admin_service.change_role(
        session=session,
        admin_id=current_user.user_id,
        target_user_id=user_id,
        new_role=body.role,
        org_id=current_user.org_id,
    )


@router.post("/{user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_user(
    user_id: uuid.UUID,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    _require_admin(current_user)
    await admin_service.suspend_user(
        session=session,
        admin_id=current_user.user_id,
        target_user_id=user_id,
        org_id=current_user.org_id,
    )
