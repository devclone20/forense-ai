"""
StorageConfigService — manages an organisation's storage backend configuration.

Responsibilities:
  - Create / update the storage_configs row for an org
  - Encrypt credentials before writing to the DB
  - Test connectivity (write + read + delete a probe object)
  - Return quota status
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import StorageConfig
from app.schemas.evidence import QuotaStatus, StorageConfigCreate, StorageConfigResponse
from app.storage.factory import encrypt_credentials, get_storage_provider


class StorageConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def configure(
        self,
        *,
        org_id: uuid.UUID,
        admin_id: uuid.UUID,
        data: StorageConfigCreate,
    ) -> StorageConfig:
        """
        Upsert the storage configuration for an org.
        Credentials are encrypted with Fernet before being stored.
        """
        encrypted = encrypt_credentials(data.credentials)

        stmt = (
            pg_insert(StorageConfig)
            .values(
                organization_id=org_id,
                backend=data.backend,
                credentials_encrypted=encrypted,
                max_file_bytes=data.max_file_bytes,
                quota_bytes=data.quota_bytes,
                configured_by=admin_id,
            )
            .on_conflict_do_update(
                index_elements=["organization_id"],
                set_={
                    "backend": data.backend,
                    "credentials_encrypted": encrypted,
                    "max_file_bytes": data.max_file_bytes,
                    "quota_bytes": data.quota_bytes,
                    "configured_by": admin_id,
                    "updated_at": __import__("sqlalchemy").func.now(),
                },
            )
            .returning(StorageConfig)
        )
        result = await self._session.execute(stmt)
        config = result.scalar_one()
        await self._session.commit()
        await self._session.refresh(config)
        return config

    async def test_connection(self, org_id: uuid.UUID) -> bool:
        """
        Probe the storage backend: write a 1-byte object, read it back, delete it.
        Raises HTTPException if the config doesn't exist or the probe fails.
        """
        config = await self._get_config(org_id)
        provider = get_storage_provider(config.backend, config.credentials_encrypted)

        probe_id = f"_probe/{uuid.uuid4()}"

        async def _one_byte():
            yield b"\x00"

        try:
            ref = await provider.store(probe_id, "probe.bin", _one_byte())
            if not await provider.exists(ref):
                return False
            # read back
            stream = await provider.retrieve(ref)
            async for _ in stream:
                pass
            await provider.delete(ref)
            return True
        except Exception:
            return False

    async def get_quota_status(self, org_id: uuid.UUID) -> QuotaStatus:
        config = await self._get_config(org_id)
        used = config.used_bytes or 0
        quota = config.quota_bytes

        if quota:
            pct = round((used / quota) * 100, 2)
            near_limit = pct >= 90.0
        else:
            pct = None
            near_limit = False

        return QuotaStatus(
            used_bytes=used,
            quota_bytes=quota,
            percentage=pct,
            near_limit=near_limit,
        )

    async def get_config(self, org_id: uuid.UUID) -> StorageConfig:
        return await self._get_config(org_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_config(self, org_id: uuid.UUID) -> StorageConfig:
        result = await self._session.execute(
            select(StorageConfig).where(StorageConfig.organization_id == org_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage not configured for this organisation.",
            )
        return config
