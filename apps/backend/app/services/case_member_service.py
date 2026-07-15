import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseMember
from app.repositories.case_member_repository import CaseMemberRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.case_member import CaseMemberAssign


class CaseMemberService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CaseMemberRepository(session)
        self._audit = AuditLogRepository(session)

    async def assign(
        self,
        *,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
        data: CaseMemberAssign,
        assigning_user_id: uuid.UUID,
        assigning_user_name: str,
        ip_address: str | None = None,
    ) -> CaseMember:
        # Idempotency: if already an active member, return existing
        existing = await self._repo.get_active_membership(case_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already an active member of this case.",
            )

        member = await self._repo.assign(
            case_id=case_id,
            user_id=data.user_id,
            role=data.role,
            assigned_by=assigning_user_id,
        )

        await self._audit.append(
            org_id=org_id,
            action="member_added",
            actor_id=assigning_user_id,
            actor_display_name=assigning_user_name,
            metadata={"user_id": str(data.user_id), "role": data.role},
            case_id=case_id,
            ip_address=ip_address,
        )

        return member

    async def remove(
        self,
        *,
        org_id: uuid.UUID,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        removing_user_id: uuid.UUID,
        removing_user_name: str,
        ip_address: str | None = None,
    ) -> CaseMember:
        member = await self._repo.remove(case_id, user_id, removed_by=removing_user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active membership found for this user in this case.",
            )

        await self._audit.append(
            org_id=org_id,
            action="member_removed",
            actor_id=removing_user_id,
            actor_display_name=removing_user_name,
            metadata={"user_id": str(user_id)},
            case_id=case_id,
            ip_address=ip_address,
        )

        return member

    async def list_members(self, case_id: uuid.UUID) -> list[CaseMember]:
        return await self._repo.list_active(case_id)
