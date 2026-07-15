"""
Auth API endpoints.

POST /api/v1/auth/login
POST /api/v1/auth/mfa/setup
POST /api/v1/auth/mfa/enable
POST /api/v1/auth/mfa/verify
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AuthUser, DBSession
from app.database import get_db
from app.middleware.rate_limit import check_rate_limit, get_client_ip
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response schemas ────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    requires_mfa: bool = False
    requires_mfa_setup: bool = False
    mfa_pending_token: str | None = None


class MFAVerifyRequest(BaseModel):
    mfa_token: str
    totp_code: str


class MFAEnableRequest(BaseModel):
    totp_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MFASetupResponse(BaseModel):
    qr_uri: str
    backup_codes: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> LoginResponse:
    ip = get_client_ip(request)
    if not check_rate_limit(ip, "/api/v1/auth/login"):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many login attempts — wait 60 seconds")

    result = await auth_service.login(
        session=session,
        email=body.email,
        password=body.password,
        ip=ip,
        ua=request.headers.get("User-Agent"),
    )

    if result.requires_mfa_setup:
        return LoginResponse(requires_mfa_setup=True)

    if result.requires_mfa:
        return LoginResponse(
            requires_mfa=True,
            mfa_pending_token=result.mfa_pending_token,
        )

    pair = result.token_pair
    assert pair is not None
    return LoginResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: AuthUser,
    session: DBSession,
) -> MFASetupResponse:
    data = await auth_service.setup_mfa(session=session, user_id=current_user.user_id)
    return MFASetupResponse(qr_uri=data.qr_uri, backup_codes=data.backup_codes)


@router.post("/mfa/enable", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_enable(
    body: MFAEnableRequest,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    await auth_service.enable_mfa(
        session=session,
        user_id=current_user.user_id,
        totp_code=body.totp_code,
    )


@router.post("/mfa/verify", response_model=TokenResponse)
async def mfa_verify(
    body: MFAVerifyRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    pair = await auth_service.verify_mfa(
        session=session,
        mfa_token=body.mfa_token,
        totp_code=body.totp_code,
        ip=get_client_ip(request),
        ua=request.headers.get("User-Agent"),
    )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def token_refresh(
    body: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    pair = await auth_service.refresh(
        session=session,
        refresh_token_plain=body.refresh_token,
        ip=get_client_ip(request),
        ua=request.headers.get("User-Agent"),
    )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    await auth_service.logout(
        session=session,
        user_id=current_user.user_id,
        refresh_token_plain=body.refresh_token,
    )
