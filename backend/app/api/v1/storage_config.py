"""
Storage config admin API.

GET  /api/v1/admin/storage/config     — current config (no credentials)
POST /api/v1/admin/storage/config     — create or update config
POST /api/v1/admin/storage/config/test — probe connectivity
GET  /api/v1/admin/storage/quota      — quota status
"""
from fastapi import APIRouter, HTTPException, status

from app.api.v1.deps import AuthUser, DBSession
from app.schemas.evidence import (
    QuotaStatus,
    StorageConfigCreate,
    StorageConfigResponse,
)
from app.services.storage_config_service import StorageConfigService

router = APIRouter(prefix="/admin/storage", tags=["storage-admin"])


def _require_admin(user: AuthUser) -> None:
    if user.global_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org admins can manage storage configuration.",
        )


@router.get(
    "/config",
    response_model=StorageConfigResponse,
    summary="Get current storage configuration",
)
async def get_storage_config(
    session: DBSession,
    current_user: AuthUser,
) -> StorageConfigResponse:
    _require_admin(current_user)
    svc = StorageConfigService(session)
    config = await svc.get_config(current_user.org_id)
    return StorageConfigResponse.model_validate(config)


@router.post(
    "/config",
    response_model=StorageConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update storage configuration",
)
async def configure_storage(
    body: StorageConfigCreate,
    session: DBSession,
    current_user: AuthUser,
) -> StorageConfigResponse:
    _require_admin(current_user)
    svc = StorageConfigService(session)
    config = await svc.configure(
        org_id=current_user.org_id,
        admin_id=current_user.user_id,
        data=body,
    )
    return StorageConfigResponse.model_validate(config)


@router.post(
    "/config/test",
    summary="Test storage backend connectivity",
)
async def test_storage_connection(
    session: DBSession,
    current_user: AuthUser,
) -> dict:
    _require_admin(current_user)
    svc = StorageConfigService(session)
    ok = await svc.test_connection(current_user.org_id)
    return {"connected": ok}


@router.get(
    "/quota",
    response_model=QuotaStatus,
    summary="Get current storage quota status",
)
async def get_quota(
    session: DBSession,
    current_user: AuthUser,
) -> QuotaStatus:
    _require_admin(current_user)
    svc = StorageConfigService(session)
    return await svc.get_quota_status(current_user.org_id)
