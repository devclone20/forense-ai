import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseMember


class CaseMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign(
        self,
        *,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        assigned_by: uuid.UUID,
    ) -> CaseMember:
        member = CaseMember(
            case_id=case_id,
            user_id=user_id,
            role=role,
            assigned_by=assigned_by,
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def get_active_membership(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CaseMember | None:
        stmt = select(CaseMember).where(
            CaseMember.case_id == case_id,
            CaseMember.user_id == user_id,
            CaseMember.removed_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self, case_id: uuid.UUID) -> list[CaseMember]:
        stmt = (
            select(CaseMember)
            .where(CaseMember.case_id == case_id, CaseMember.removed_at.is_(None))
            .order_by(CaseMember.assigned_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def remove(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        removed_by: uuid.UUID,
    ) -> CaseMember | None:
        member = await self.get_active_membership(case_id, user_id)
        if not member:
            return None
        member.removed_at = datetime.now(timezone.utc)
        member.removed_by = removed_by
        await self._session.flush()
        return member
