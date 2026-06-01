"""
State transitions API — POST /cases/:id/transitions
"""
import uuid

from fastapi import APIRouter, Request

from app.api.v1.deps import AuthUser, DBSession
from app.schemas.case import CaseResponse, CaseTransitionRequest
from app.services.case_service import CaseService

router = APIRouter(tags=["cases"])


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/cases/{case_id}/transitions",
    response_model=CaseResponse,
    summary="Transition case to a new state",
)
async def transition_case(
    case_id: uuid.UUID,
    body: CaseTransitionRequest,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> CaseResponse:
    svc = CaseService(session)
    case = await svc.transition_state(
        case_id=case_id,
        org_id=current_user.org_id,
        actor_id=current_user.user_id,
        actor_display_name=current_user.display_name,
        request=body,
        is_admin=current_user.is_admin,
        ip_address=_get_ip(request),
    )
    return CaseResponse.model_validate(case)
