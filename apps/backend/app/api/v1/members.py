"""
Members API — GET/POST/DELETE /cases/:id/members
"""
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from app.api.v1.deps import AuthUser, DBSession
from app.schemas.case_member import CaseMemberAssign, CaseMemberRemove, CaseMemberResponse
from app.services.case_member_service import CaseMemberService

router = APIRouter(tags=["case-members"])


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get(
    "/cases/{case_id}/members",
    response_model=list[CaseMemberResponse],
    summary="List active case members",
)
async def list_members(
    case_id: uuid.UUID,
    session: DBSession,
    current_user: AuthUser,
) -> list[CaseMemberResponse]:
    svc = CaseMemberService(session)
    members = await svc.list_members(case_id)
    return [CaseMemberResponse.model_validate(m) for m in members]


@router.post(
    "/cases/{case_id}/members",
    response_model=CaseMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a member to a case",
)
async def assign_member(
    case_id: uuid.UUID,
    body: CaseMemberAssign,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> CaseMemberResponse:
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and peritos can assign case members.",
        )

    svc = CaseMemberService(session)
    member = await svc.assign(
        org_id=current_user.org_id,
        case_id=case_id,
        data=body,
        assigning_user_id=current_user.user_id,
        assigning_user_name=current_user.display_name,
        ip_address=_get_ip(request),
    )
    return CaseMemberResponse.model_validate(member)


@router.delete(
    "/cases/{case_id}/members",
    response_model=CaseMemberResponse,
    summary="Remove a member from a case",
)
async def remove_member(
    case_id: uuid.UUID,
    body: CaseMemberRemove,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> CaseMemberResponse:
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and peritos can remove case members.",
        )

    svc = CaseMemberService(session)
    member = await svc.remove(
        org_id=current_user.org_id,
        case_id=case_id,
        user_id=body.user_id,
        removing_user_id=current_user.user_id,
        removing_user_name=current_user.display_name,
        ip_address=_get_ip(request),
    )
    return CaseMemberResponse.model_validate(member)
