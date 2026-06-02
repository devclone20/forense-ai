"""
Evidence API — file upload, listing, download, integrity verification,
and chain-of-custody export.

All routes sit under /cases/{case_id}/evidences and are protected by RLS.
"""
from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.v1.deps import AuthUser, DBSession
from app.schemas.common import PaginatedResponse
from app.schemas.evidence import (
    EvidenceDetailResponse,
    EvidenceListFilters,
    EvidenceResponse,
    VerificationResult,
)
from app.services.evidence_service import EvidenceService
from app.schemas.evidence import EvidenceIngestMetadata

router = APIRouter(prefix="/cases/{case_id}/evidences", tags=["evidences"])


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ──────────────────────────────────────────────────────────────────────────────
# POST /cases/{case_id}/evidences  — ingest a new evidence file
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest an evidence file",
)
async def ingest_evidence(
    case_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
    file: Annotated[UploadFile, File(description="The evidence file to ingest.")],
    metadata_json: Annotated[
        str, Form(description="JSON-encoded EvidenceIngestMetadata")
    ],
) -> EvidenceResponse:
    if not current_user.is_perito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and peritos can ingest evidence.",
        )
    try:
        metadata = EvidenceIngestMetadata.model_validate(json.loads(metadata_json))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metadata: {exc}",
        ) from exc

    svc = EvidenceService(session)
    evidence = await svc.ingest(
        case_id=case_id,
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        user_display_name=current_user.display_name,
        file=file,
        metadata=metadata,
        ip_address=_get_ip(request),
    )
    return EvidenceResponse.model_validate(evidence)


# ──────────────────────────────────────────────────────────────────────────────
# GET /cases/{case_id}/evidences  — list with filters
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[EvidenceResponse],
    summary="List evidences for a case",
)
async def list_evidences(
    case_id: uuid.UUID,
    session: DBSession,
    current_user: AuthUser,
    evidence_type: Annotated[str | None, Query()] = None,
    date_from: Annotated[str | None, Query()] = None,
    date_to: Annotated[str | None, Query()] = None,
    ingested_by: Annotated[uuid.UUID | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=500)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[EvidenceResponse]:
    from datetime import datetime

    def _parse_dt(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    filters = EvidenceListFilters(
        evidence_type=evidence_type,
        date_from=_parse_dt(date_from),
        date_to=_parse_dt(date_to),
        ingested_by=ingested_by,
        search=search,
        page=page,
        page_size=page_size,
    )
    svc = EvidenceService(session)
    return await svc.list_evidences(
        case_id=case_id,
        org_id=current_user.org_id,
        filters=filters,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /cases/{case_id}/evidences/chain-of-custody  — CSV export
# (must be before /{ev_id} to avoid routing conflict)
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/chain-of-custody",
    summary="Export chain of custody as a signed CSV",
)
async def export_chain_of_custody(
    case_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> StreamingResponse:
    svc = EvidenceService(session)
    csv_bytes, hmac_hex = await svc.export_chain_of_custody(
        case_id=case_id,
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        user_display_name=current_user.display_name,
        ip_address=_get_ip(request),
    )
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="chain-of-custody-{case_id}.csv"',
            "X-Chain-HMAC-SHA256": hmac_hex,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /cases/{case_id}/evidences/{ev_id}  — detail
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{ev_id}",
    response_model=EvidenceDetailResponse,
    summary="Get evidence detail with event timeline",
)
async def get_evidence(
    case_id: uuid.UUID,
    ev_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> EvidenceDetailResponse:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.evidence import Evidence

    # Use selectinload to fetch events in the same query
    result = await session.execute(
        select(Evidence)
        .options(selectinload(Evidence.events))
        .where(
            Evidence.id == ev_id,
            Evidence.case_id == case_id,
            Evidence.organization_id == current_user.org_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")

    # Log view event without needing the full service
    from app.models.evidence import EvidenceEvent
    session.add(
        EvidenceEvent(
            organization_id=current_user.org_id,
            evidence_id=ev_id,
            event_type="viewed",
            actor_id=current_user.user_id,
            actor_name=current_user.display_name,
            ip_address=_get_ip(request),
            metadata={},
        )
    )
    await session.commit()
    await session.refresh(evidence)

    return EvidenceDetailResponse.model_validate(evidence)


# ──────────────────────────────────────────────────────────────────────────────
# GET /cases/{case_id}/evidences/{ev_id}/download  — streaming download
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{ev_id}/download",
    summary="Download evidence file (streaming)",
)
async def download_evidence(
    case_id: uuid.UUID,
    ev_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> StreamingResponse:
    svc = EvidenceService(session)
    stream, evidence = await svc.download_stream(
        evidence_id=ev_id,
        case_id=case_id,
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        user_display_name=current_user.display_name,
        ip_address=_get_ip(request),
    )
    filename = f"{evidence.evidence_number}_{evidence.original_filename}"
    return StreamingResponse(
        stream,
        media_type=evidence.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(evidence.size_bytes),
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /cases/{case_id}/evidences/{ev_id}/verify  — integrity check
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{ev_id}/verify",
    response_model=VerificationResult,
    summary="Verify evidence SHA-256 integrity",
)
async def verify_integrity(
    case_id: uuid.UUID,
    ev_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: AuthUser,
) -> VerificationResult:
    svc = EvidenceService(session)
    return await svc.verify_integrity(
        evidence_id=ev_id,
        case_id=case_id,
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        user_display_name=current_user.display_name,
        ip_address=_get_ip(request),
    )
