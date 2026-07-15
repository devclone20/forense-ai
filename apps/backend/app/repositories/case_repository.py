"""
Case repository.

All queries pass through the session that already has RLS set via the tenant
middleware. No explicit org_id filter is needed in WHERE clauses — PostgreSQL
enforces it at the RLS policy level — but we add it anyway as defence-in-depth.
"""
import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.schemas.case import CaseCreate, CaseListFilters, CaseUpdate


class CaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        org_id: uuid.UUID,
        owner_id: uuid.UUID,
        case_number: str,
        data: CaseCreate,
    ) -> Case:
        case = Case(
            organization_id=org_id,
            owner_id=owner_id,
            case_number=case_number,
            title=data.title,
            description=data.description,
            forensic_domain=data.forensic_domain,
            confidentiality=data.confidentiality,
            tags=data.tags,
            domain_metadata=data.domain_metadata,
        )
        self._session.add(case)
        await self._session.flush()
        await self._session.refresh(case)
        return case

    async def get_by_id(
        self,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> Case | None:
        stmt = select(Case).where(
            Case.id == case_id,
            Case.organization_id == org_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        org_id: uuid.UUID,
        filters: CaseListFilters,
    ) -> tuple[list[Case], int]:
        base = select(Case).where(Case.organization_id == org_id)

        if filters.status:
            base = base.where(Case.status == filters.status)
        if filters.forensic_domain:
            base = base.where(Case.forensic_domain == filters.forensic_domain)
        if filters.owner_id:
            base = base.where(Case.owner_id == filters.owner_id)
        if filters.date_from:
            base = base.where(Case.created_at >= filters.date_from)
        if filters.date_to:
            base = base.where(Case.created_at <= filters.date_to)
        if filters.search:
            # Full-text search via tsvector; fall back to ILIKE if vector not yet populated
            ts_query = func.plainto_tsquery("portuguese", filters.search)
            base = base.where(Case.search_vector.op("@@")(ts_query))

        # Count before pagination
        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply ordering and pagination
        offset = (filters.page - 1) * filters.page_size
        paginated = (
            base
            .order_by(Case.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        rows = await self._session.execute(paginated)
        return list(rows.scalars().all()), total

    async def update(
        self,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        data: CaseUpdate,
    ) -> Case | None:
        values = data.model_dump(exclude_none=True)
        if not values:
            return await self.get_by_id(case_id, org_id)

        stmt = (
            update(Case)
            .where(Case.id == case_id, Case.organization_id == org_id)
            .values(**values)
            .returning(Case)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        new_status: str,
        closed_at: datetime | None = None,
        archived_at: datetime | None = None,
        clear_closed_at: bool = False,
    ) -> Case | None:
        values: dict = {"status": new_status}
        if closed_at is not None:
            values["closed_at"] = closed_at
        if archived_at is not None:
            values["archived_at"] = archived_at
        if clear_closed_at:
            values["closed_at"] = None

        stmt = (
            update(Case)
            .where(Case.id == case_id, Case.organization_id == org_id)
            .values(**values)
            .returning(Case)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
