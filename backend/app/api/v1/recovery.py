"""
Password recovery API endpoints.

POST /api/v1/auth/recovery/request
POST /api/v1/auth/recovery/confirm
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.middleware.rate_limit import check_rate_limit, get_client_ip
from app.services import recovery_service

router = APIRouter(prefix="/auth/recovery", tags=["auth"])


class RecoveryRequestBody(BaseModel):
    email: EmailStr


class RecoveryConfirmBody(BaseModel):
    token: str
    new_password: str


@router.post("/request", status_code=status.HTTP_200_OK)
async def request_recovery(
    body: RecoveryRequestBody,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ip = get_client_ip(request)
    if not check_rate_limit(ip, "/api/v1/auth/recovery/request"):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many requests — wait 60 seconds")

    await recovery_service.request_recovery(session=session, email=body.email)
    # Neutral message regardless of whether the email exists
    return {"message": "If that address is registered, a recovery link has been sent."}


@router.post("/confirm", status_code=status.HTTP_200_OK)
async def confirm_recovery(
    body: RecoveryConfirmBody,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await recovery_service.confirm_recovery(
        session=session,
        token=body.token,
        new_password=body.new_password,
    )
    return {"message": "Password updated successfully."}
