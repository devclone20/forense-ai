"""
Activity API — GET /cases/:id/activity, GET /cases/:id/activity/export
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime

from app.api.v1.deps import AuthUser, DBSession
from app.services.audit_log_service import AuditLogService

router = APIRouter(tags=["activity"])


class AuditLogEntryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    action: str
    actor_id: uuid.UUID
    actor_display_name: str
    metadata: dict
    occurred_at: datetime
    ip_address: str | None


@router.get(
    "/cases/{case_id}/activity",
    response_model=list[AuditLogEntryResponse],
    summary="Get case activity log",
)
async def get_activity(
    case_id: uuid.UUID,
    session: DBSession,
    current_user: AuthUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogEntryResponse]:
    svc = AuditLogService(session)
    entries = await svc.get_case_activity(
        current_user.org_id, case_id, limit=limit, offset=offset
    )
    return [AuditLogEntryResponse.model_validate(e) for e in entries]


@router.get(
    "/cases/{case_id}/activity/export",
    summary="Export case audit log as CSV",
    responses={200: {"content": {"text/csv": {}}}},
)
async def export_activity(
    case_id: uuid.UUID,
    session: DBSession,
    current_user: AuthUser,
) -> Response:
    # Only admin, owner, and supervisor can export
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export audit log.",
        )

    svc = AuditLogService(session)
    csv_content = await svc.export_case_log_csv(current_user.org_id, case_id)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="case_{case_id}_audit.csv"'
        },
    )
