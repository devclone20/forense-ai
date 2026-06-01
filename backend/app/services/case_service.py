"""
Case service — orchestrates creation, retrieval, update, and state transitions.

This is the primary application service for the Case Management module.
All domain rules flow through here.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.case_state_machine import TransitionError, validate_transition
from app.models.case import Case, CaseStateTransition
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.case_repository import CaseRepository
from app.schemas.case import (
    CaseCreate,
    CaseListFilters,
    CaseResponse,
    CaseTransitionRequest,
    CaseUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.case_number_service import CaseNumberService


class CaseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._case_repo = CaseRepository(session)
        self._audit = AuditLogRepository(session)
        self._number_svc = CaseNumberService(session)

    async def create_case(
        self,
        *,
        org_id: uuid.UUID,
        owner_id: uuid.UUID,
        owner_display_name: str,
        number_format: str,
        data: CaseCreate,
        ip_address: str | None = None,
    ) -> Case:
        case_number = await self._number_svc.generate_number(org_id, number_format)

        case = await self._case_repo.create(
            org_id=org_id,
            owner_id=owner_id,
            case_number=case_number,
            data=data,
        )

        await self._audit.append(
            org_id=org_id,
            action="case_created",
            actor_id=owner_id,
            actor_display_name=owner_display_name,
            metadata={
                "case_number": case_number,
                "title": data.title,
                "forensic_domain": data.forensic_domain,
            },
            case_id=case.id,
            ip_address=ip_address,
        )

        await self._session.commit()
        await self._session.refresh(case)
        return case

    async def get_case(
        self,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> Case:
        case = await self._case_repo.get_by_id(case_id, org_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found.",
            )
        return case

    async def list_cases(
        self,
        org_id: uuid.UUID,
        filters: CaseListFilters,
    ) -> PaginatedResponse[CaseResponse]:
        cases, total = await self._case_repo.list_with_filters(org_id, filters)
        pages = max(1, -(-total // filters.page_size))  # ceiling division
        return PaginatedResponse(
            items=[CaseResponse.model_validate(c) for c in cases],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )

    async def update_case(
        self,
        *,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_display_name: str,
        data: CaseUpdate,
        ip_address: str | None = None,
    ) -> Case:
        case = await self._case_repo.update(case_id, org_id, data)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found.",
            )

        await self._audit.append(
            org_id=org_id,
            action="case_updated",
            actor_id=actor_id,
            actor_display_name=actor_display_name,
            metadata=data.model_dump(exclude_none=True),
            case_id=case_id,
            ip_address=ip_address,
        )

        await self._session.commit()
        await self._session.refresh(case)
        return case

    async def transition_state(
        self,
        *,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_display_name: str,
        request: CaseTransitionRequest,
        is_admin: bool = False,
        ip_address: str | None = None,
    ) -> Case:
        case = await self.get_case(case_id, org_id)

        try:
            result = validate_transition(
                from_status=case.status,
                to_status=request.to_status,
                justification=request.justification,
                is_admin=is_admin,
            )
        except TransitionError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        now = datetime.now(timezone.utc)
        updated_case = await self._case_repo.update_status(
            case_id=case_id,
            org_id=org_id,
            new_status=result.to_status,
            closed_at=now if result.sets_closed_at else None,
            archived_at=now if result.sets_archived_at else None,
            clear_closed_at=result.clears_closed_at,
        )
        if not updated_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

        # Record transition history
        transition = CaseStateTransition(
            case_id=case_id,
            from_status=result.from_status,
            to_status=result.to_status,
            transitioned_by=actor_id,
            justification=request.justification,
        )
        self._session.add(transition)

        await self._audit.append(
            org_id=org_id,
            action="case_status_changed",
            actor_id=actor_id,
            actor_display_name=actor_display_name,
            metadata={
                "from_status": result.from_status,
                "to_status": result.to_status,
                "justification": request.justification,
            },
            case_id=case_id,
            ip_address=ip_address,
        )

        await self._session.commit()
        await self._session.refresh(updated_case)
        return updated_case
