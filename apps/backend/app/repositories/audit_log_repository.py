"""
Audit log repository — append-only.

The REVOKE UPDATE, DELETE at the DB level enforces immutability.
This repository intentionally exposes NO update/delete methods.
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.case import AuditLog


def _compute_hmac(entry_data: dict) -> str:
    """Compute HMAC-SHA256 over the log entry for tamper detection."""
    payload = json.dumps(entry_data, sort_keys=True, default=str)
    return hmac.new(
        settings.audit_hmac_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        org_id: uuid.UUID,
        action: str,
        actor_id: uuid.UUID,
        actor_display_name: str,
        metadata: dict,
        case_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry_data = {
            "org_id": str(org_id),
            "case_id": str(case_id) if case_id else None,
            "action": action,
            "actor_id": str(actor_id),
            "metadata": metadata,
        }
        signature = _compute_hmac(entry_data)

        log = AuditLog(
            organization_id=org_id,
            case_id=case_id,
            action=action,
            actor_id=actor_id,
            actor_display_name=actor_display_name,
            metadata=metadata,
            ip_address=ip_address,
            hmac_signature=signature,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def list_for_case(
        self,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.organization_id == org_id,
                AuditLog.case_id == case_id,
            )
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def export_for_case(
        self,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
    ) -> list[AuditLog]:
        """Return all audit log entries for a case, ordered ascending (chronological)."""
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.organization_id == org_id,
                AuditLog.case_id == case_id,
            )
            .order_by(AuditLog.occurred_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_after(
        self,
        org_id: uuid.UUID,
        after: datetime,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.organization_id == org_id,
                AuditLog.occurred_at > after,
            )
            .order_by(AuditLog.occurred_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
