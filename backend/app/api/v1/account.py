"""
Account API endpoints — authenticated user's own profile.

GET   /api/v1/account/me
PATCH /api/v1/account/me
POST  /api/v1/account/password
POST  /api/v1/account/mfa/backup-codes/regenerate
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import AuthUser, DBSession
from app.domain import password as pwd_domain
from app.domain import totp as totp_domain
from app.repositories import auth_repository as repo
from app.services import auth_service

router = APIRouter(prefix="/account", tags=["account"])


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    global_role: str
    mfa_enabled: bool


class UpdateProfileRequest(BaseModel):
    display_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RegenerateBackupCodesRequest(BaseModel):
    totp_code: str


class RegenerateBackupCodesResponse(BaseModel):
    backup_codes: list[str]


@router.get("/me", response_model=ProfileResponse)
async def get_me(
    current_user: AuthUser,
    session: DBSession,
) -> ProfileResponse:
    user = await repo.get_user_by_id(session, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        global_role=user.global_role,
        mfa_enabled=user.mfa_enabled,
    )


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: AuthUser,
    session: DBSession,
) -> ProfileResponse:
    user = await repo.get_user_by_id(session, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.display_name = body.display_name
    await session.commit()
    return ProfileResponse(
        user_id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        global_role=user.global_role,
        mfa_enabled=user.mfa_enabled,
    )


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: AuthUser,
    session: DBSession,
) -> None:
    user = await repo.get_user_by_id(session, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.password_hash or not pwd_domain.verify_password(
        body.current_password, user.password_hash
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Current password is incorrect")

    user.password_hash = pwd_domain.hash_password(body.new_password)
    await repo.append_auth_log(session, "password_changed",
                               user_id=user.id, org_id=user.organization_id)
    await session.commit()


@router.post("/mfa/backup-codes/regenerate", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    body: RegenerateBackupCodesRequest,
    current_user: AuthUser,
    session: DBSession,
) -> RegenerateBackupCodesResponse:
    user = await repo.get_user_by_id(session, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="MFA is not enabled")

    from app.services.auth_service import _decrypt
    secret = _decrypt(user.mfa_secret)

    if not totp_domain.verify_code(secret, body.totp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid TOTP code")

    new_codes_plain = totp_domain.generate_backup_codes()
    user.mfa_backup_codes = [
        {"hash": totp_domain.hash_backup_code(c), "used_at": None}
        for c in new_codes_plain
    ]
    await repo.append_auth_log(session, "mfa_backup_regenerated",
                               user_id=user.id, org_id=user.organization_id)
    await session.commit()
    return RegenerateBackupCodesResponse(backup_codes=new_codes_plain)
