"""
Invites API endpoints.

POST   /api/v1/invites
DELETE /api/v1/invites/:id
GET    /api/v1/invites/:token/validate
POST   /api/v1/invites/:token/accept
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.v1.deps import AuthUser, DBSession
from app.services import invite_service

router = APIRouter(prefix="/invites", tags=["invites"])


class CreateInviteRequest(BaseModel):
    email: EmailStr
    role: str


class CreateInviteResponse(BaseModel):
    invite_id: uuid.UUID
    accept_link: str


class ValidateInviteResponse(BaseModel):
    valid: bool
    email: str | None = None
    role: str | None = None
    org_name: str | None = None


class AcceptInviteRequest(BaseModel):
    display_name: str
    password: str


class AcceptInviteResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    message: str = "Account created successfully"


@router.post("", response_model=CreateInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    body: CreateInviteRequest,
    current_user: AuthUser,
    session: DBSession,
) -> CreateInviteResponse:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin role required")

    result = await invite_service.create_invite(
        session=session,
        org_id=current_user.org_id,
        email=body.email,
        role=body.role,
        invited_by_id=current_user.user_id,
    )
    return CreateInviteResponse(invite_id=result.invite_id, accept_link=result.accept_link)


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    invite_id: uuid.UUID,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin role required")

    await invite_service.revoke_invite(
        session=session,
        invite_id=invite_id,
        revoked_by=current_user.user_id,
        org_id=current_user.org_id,
    )


@router.get("/{token}/validate", response_model=ValidateInviteResponse)
async def validate_invite(token: str, session: DBSession) -> ValidateInviteResponse:
    result = await invite_service.validate_invite(session=session, token_plain=token)
    return ValidateInviteResponse(
        valid=result.valid,
        email=result.email,
        role=result.role,
        org_name=result.org_name,
    )


@router.post("/{token}/accept", response_model=AcceptInviteResponse,
             status_code=status.HTTP_201_CREATED)
async def accept_invite(
    token: str,
    body: AcceptInviteRequest,
    session: DBSession,
) -> AcceptInviteResponse:
    user = await invite_service.accept_invite(
        session=session,
        token_plain=token,
        display_name=body.display_name,
        password=body.password,
    )
    return AcceptInviteResponse(user_id=user.id, email=user.email)
