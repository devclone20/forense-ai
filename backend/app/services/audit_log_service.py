import csv
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditLogRepository(session)

    async def log(
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
        return await self._repo.append(
            org_id=org_id,
            action=action,
            actor_id=actor_id,
            actor_display_name=actor_display_name,
            metadata=metadata,
            case_id=case_id,
            ip_address=ip_address,
        )

    async def get_case_activity(
        self,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        return await self._repo.list_for_case(
            org_id, case_id, limit=limit, offset=offset
        )

    async def export_case_log_csv(
        self,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
    ) -> str:
        """Export complete case audit log as CSV string."""
        entries = await self._repo.export_for_case(org_id, case_id)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "id", "occurred_at", "action", "actor_id", "actor_display_name",
            "ip_address", "metadata", "hmac_signature",
        ])
        for e in entries:
            writer.writerow([
                str(e.id),
                e.occurred_at.isoformat(),
                e.action,
                str(e.actor_id),
                e.actor_display_name,
                e.ip_address or "",
                str(e.metadata),
                e.hmac_signature or "",
            ])
        return buffer.getvalue()
