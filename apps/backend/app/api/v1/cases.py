"""
Cases API — POST /cases, GET /cases, GET /cases/:id, PATCH /cases/:id
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.v1.deps import AuthUser, DBSession
from app.models.organization import Organization
from app.schemas.case import (
    CaseCreate,
    CaseListFilters,
    CaseResponse,
    CaseUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.case_service import CaseService
from sqlalchemy import select

router = APIRouter(prefix="/cases", tags=["cases"])


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
)
async def create_case(
    body: CaseCreate,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> CaseResponse:
    # Only admin or perito can create cases
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and peritos can create cases.",
        )

    # Fetch org to get number_format
    org_result = await session.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found.")

    svc = CaseService(session)
    case = await svc.create_case(
        org_id=current_user.org_id,
        owner_id=current_user.user_id,
        owner_display_name=current_user.display_name,
        number_format=org.number_format,
        data=body,
        ip_address=_get_ip(request),
    )
    return CaseResponse.model_validate(case)


@router.get(
    "",
    response_model=PaginatedResponse[CaseResponse],
    summary="List cases with filters",
)
async def list_cases(
    session: DBSession,
    current_user: AuthUser,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    domain: Annotated[str | None, Query()] = None,
    owner_id: Annotated[uuid.UUID | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=500)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[CaseResponse]:
    filters = CaseListFilters(
        status=status_filter,  # type: ignore[arg-type]
        forensic_domain=domain,  # type: ignore[arg-type]
        owner_id=owner_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    svc = CaseService(session)
    return await svc.list_cases(current_user.org_id, filters)


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Get a case by ID",
)
async def get_case(
    case_id: uuid.UUID,
    session: DBSession,
    current_user: AuthUser,
) -> CaseResponse:
    svc = CaseService(session)
    case = await svc.get_case(case_id, current_user.org_id)
    return CaseResponse.model_validate(case)


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Update a case",
)
async def update_case(
    case_id: uuid.UUID,
    body: CaseUpdate,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> CaseResponse:
    # Only admin or owner can edit — owner check happens at service/DB level
    # For this phase we require admin or perito at minimum
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this case.",
        )

    svc = CaseService(session)
    case = await svc.update_case(
        case_id=case_id,
        org_id=current_user.org_id,
        actor_id=current_user.user_id,
        actor_display_name=current_user.display_name,
        data=body,
        ip_address=_get_ip(request),
    )
    return CaseResponse.model_validate(case)
