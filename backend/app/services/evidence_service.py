"""
EvidenceService — orchestrates evidence ingest, integrity verification,
streaming download, and chain-of-custody export.

Every operation that touches an evidence file is append-logged to
evidence_events (immutable at the DB level).

Memory contract: no file is ever fully buffered in the service layer.
All I/O is streamed chunk-by-chunk.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.evidence import Evidence, EvidenceEvent, EvidenceNumberSequence
from app.models.case import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.evidence import (
    EvidenceDetailResponse,
    EvidenceIngestMetadata,
    EvidenceListFilters,
    EvidenceResponse,
    VerificationResult,
)
from app.schemas.common import PaginatedResponse
from app.storage.factory import get_storage_provider
from app.storage.hashing import hash_stream, tee_stream
from app.services.storage_config_service import StorageConfigService

try:
    import magic as _magic  # python-magic
    _HAS_MAGIC = True
except ImportError:
    _HAS_MAGIC = False


def _detect_mime(filename: str, content_type: str | None) -> str:
    """
    Use python-magic if available; fall back to the browser-supplied content-type
    or a safe default.  Never trust the file extension alone.
    """
    if content_type and content_type not in ("application/octet-stream", ""):
        return content_type
    return "application/octet-stream"


def _detect_mime_from_bytes(sample: bytes, filename: str, content_type: str | None) -> str:
    if _HAS_MAGIC and sample:
        try:
            detected = _magic.from_buffer(sample, mime=True)
            if detected:
                return detected
        except Exception:
            pass
    return _detect_mime(filename, content_type)


class EvidenceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditLogRepository(session)
        self._storage_svc = StorageConfigService(session)

    # ──────────────────────────────────────────────────────────────────
    # Ingest
    # ──────────────────────────────────────────────────────────────────

    async def ingest(
        self,
        *,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        file: UploadFile,
        metadata: EvidenceIngestMetadata,
        ip_address: str | None = None,
    ) -> Evidence:
        # 1. Load storage config + instantiate provider
        config = await self._storage_svc.get_config(org_id)
        provider = get_storage_provider(config.backend, config.credentials_encrypted)

        # 2. Pre-flight quota checks (size guard before touching storage)
        if config.max_file_bytes and file.size and file.size > config.max_file_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File exceeds the per-file limit of "
                    f"{config.max_file_bytes:,} bytes."
                ),
            )
        if config.quota_bytes and file.size:
            used = config.used_bytes or 0
            if used + file.size > config.quota_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Organisation storage quota exceeded.",
                )

        # 3. Generate evidence UUID
        evidence_id = uuid.uuid4()
        storage_key = f"{org_id}/{case_id}/{evidence_id}"
        original_filename = file.filename or "unknown"

        # 4. Stream the upload: tee into (hash_stream, provider.store) simultaneously
        async def _upload_stream() -> AsyncIterator[bytes]:
            # Read in chunks — never hold the whole file in RAM
            while True:
                chunk = await file.read(65_536)
                if not chunk:
                    return
                yield chunk

        stream_for_hash, stream_for_store = await tee_stream(_upload_stream())

        # Collect a small sample for MIME detection from the hash stream copy
        # We do this by wrapping the hash stream to capture the first chunk.
        mime_sample: list[bytes] = []

        async def _hash_stream_with_sample() -> AsyncIterator[bytes]:
            first = True
            async for chunk in stream_for_hash:
                if first and chunk:
                    mime_sample.append(chunk[:4096])
                    first = False
                yield chunk

        import asyncio
        hash_task = asyncio.create_task(hash_stream(_hash_stream_with_sample()))
        ref = await provider.store(storage_key, original_filename, stream_for_store)
        sha256_hex, size_bytes = await hash_task

        # 5. MIME detection using the sample we captured
        mime_type = _detect_mime_from_bytes(
            mime_sample[0] if mime_sample else b"",
            original_filename,
            file.content_type,
        )

        # 6. Duplicate detection within the same case
        dup_result = await self._session.execute(
            select(Evidence.id).where(
                Evidence.case_id == case_id,
                Evidence.sha256_hash == sha256_hex,
            )
        )
        existing = dup_result.scalar_one_or_none()
        if existing:
            # Clean up the just-stored file
            try:
                await provider.delete(ref)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A file with this content already exists in this case "
                    f"(evidence {existing})."
                ),
            )

        # 7. Atomic counter increment — generates EV-001, EV-002 …
        evidence_number = await self._next_evidence_number(case_id)

        # 8. Persist the Evidence row
        evidence = Evidence(
            id=evidence_id,
            organization_id=org_id,
            case_id=case_id,
            evidence_number=evidence_number,
            title=metadata.title,
            description=metadata.description,
            evidence_type=metadata.evidence_type,
            storage_ref=str(ref),
            original_filename=original_filename,
            size_bytes=size_bytes,
            mime_type=mime_type,
            sha256_hash=sha256_hex,
            source_origin=metadata.source_origin,
            collected_at=metadata.collected_at,
            ingested_by=user_id,
            tags=metadata.tags,
            domain_metadata=metadata.domain_metadata,
        )
        self._session.add(evidence)
        await self._session.flush()

        # 9. Append chain-of-custody event
        self._session.add(
            EvidenceEvent(
                organization_id=org_id,
                evidence_id=evidence_id,
                event_type="ingested",
                actor_id=user_id,
                actor_name=user_display_name,
                ip_address=ip_address,
                metadata={
                    "original_filename": original_filename,
                    "size_bytes": size_bytes,
                    "sha256_hash": sha256_hex,
                    "mime_type": mime_type,
                },
            )
        )

        # 10. Case-level audit log
        await self._audit.append(
            org_id=org_id,
            action="evidence_added",
            actor_id=user_id,
            actor_display_name=user_display_name,
            metadata={
                "evidence_number": evidence_number,
                "title": metadata.title,
                "evidence_type": metadata.evidence_type,
                "sha256_hash": sha256_hex,
            },
            case_id=case_id,
            ip_address=ip_address,
        )

        await self._session.commit()
        await self._session.refresh(evidence)
        return evidence

    # ──────────────────────────────────────────────────────────────────
    # Listing + retrieval
    # ──────────────────────────────────────────────────────────────────

    async def list_evidences(
        self,
        *,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        filters: EvidenceListFilters,
    ) -> PaginatedResponse[EvidenceResponse]:
        stmt = select(Evidence).where(
            Evidence.case_id == case_id,
            Evidence.organization_id == org_id,
        )

        if filters.evidence_type:
            stmt = stmt.where(Evidence.evidence_type == filters.evidence_type)
        if filters.date_from:
            stmt = stmt.where(Evidence.ingested_at >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Evidence.ingested_at <= filters.date_to)
        if filters.ingested_by:
            stmt = stmt.where(Evidence.ingested_by == filters.ingested_by)
        if filters.search:
            stmt = stmt.where(
                Evidence.search_vector.op("@@")(
                    text("plainto_tsquery('portuguese', :q)")
                ).bindparams(q=filters.search)
            )

        count_stmt = select(__import__("sqlalchemy").func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            stmt
            .order_by(Evidence.ingested_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        rows = await self._session.execute(stmt)
        items = list(rows.scalars().all())
        pages = max(1, -(-total // filters.page_size))

        return PaginatedResponse(
            items=[EvidenceResponse.model_validate(e) for e in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )

    async def get_evidence(
        self,
        *,
        evidence_id: uuid.UUID,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        ip_address: str | None = None,
    ) -> Evidence:
        evidence = await self._load_evidence(evidence_id, case_id, org_id)

        self._session.add(
            EvidenceEvent(
                organization_id=org_id,
                evidence_id=evidence_id,
                event_type="viewed",
                actor_id=user_id,
                actor_name=user_display_name,
                ip_address=ip_address,
                metadata={},
            )
        )
        await self._session.commit()
        await self._session.refresh(evidence)
        return evidence

    # ──────────────────────────────────────────────────────────────────
    # Download (streaming)
    # ──────────────────────────────────────────────────────────────────

    async def download_stream(
        self,
        *,
        evidence_id: uuid.UUID,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        ip_address: str | None = None,
    ) -> tuple[AsyncIterator[bytes], Evidence]:
        evidence = await self._load_evidence(evidence_id, case_id, org_id)

        config = await self._storage_svc.get_config(org_id)
        provider = get_storage_provider(config.backend, config.credentials_encrypted)
        stream = await provider.retrieve(
            __import__("app.storage", fromlist=["StorageRef"]).StorageRef(
                value=evidence.storage_ref
            )
        )

        download_filename = f"{evidence.evidence_number}_{evidence.original_filename}"
        self._session.add(
            EvidenceEvent(
                organization_id=org_id,
                evidence_id=evidence_id,
                event_type="downloaded",
                actor_id=user_id,
                actor_name=user_display_name,
                ip_address=ip_address,
                metadata={"download_filename": download_filename},
            )
        )
        await self._session.commit()

        return stream, evidence

    # ──────────────────────────────────────────────────────────────────
    # Integrity verification
    # ──────────────────────────────────────────────────────────────────

    async def verify_integrity(
        self,
        *,
        evidence_id: uuid.UUID,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        ip_address: str | None = None,
    ) -> VerificationResult:
        from app.storage import StorageRef

        evidence = await self._load_evidence(evidence_id, case_id, org_id)
        config = await self._storage_svc.get_config(org_id)
        provider = get_storage_provider(config.backend, config.credentials_encrypted)

        computed = await provider.compute_hash(StorageRef(value=evidence.storage_ref))
        match = computed == evidence.sha256_hash

        if not match:
            self._session.add(
                EvidenceEvent(
                    organization_id=org_id,
                    evidence_id=evidence_id,
                    event_type="integrity_alert",
                    actor_id=user_id,
                    actor_name=user_display_name,
                    ip_address=ip_address,
                    metadata={
                        "stored_hash": evidence.sha256_hash,
                        "computed_hash": computed,
                    },
                )
            )

        self._session.add(
            EvidenceEvent(
                organization_id=org_id,
                evidence_id=evidence_id,
                event_type="integrity_verified",
                actor_id=user_id,
                actor_name=user_display_name,
                ip_address=ip_address,
                metadata={
                    "match": match,
                    "stored_hash": evidence.sha256_hash,
                    "computed_hash": computed,
                },
            )
        )
        await self._session.commit()

        return VerificationResult(
            evidence_id=evidence_id,
            match=match,
            stored_hash=evidence.sha256_hash,
            computed_hash=computed,
            verified_at=datetime.now(timezone.utc),
        )

    # ──────────────────────────────────────────────────────────────────
    # Chain of custody export
    # ──────────────────────────────────────────────────────────────────

    async def export_chain_of_custody(
        self,
        *,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        ip_address: str | None = None,
    ) -> tuple[bytes, str]:
        """
        Export all evidence events for a case as a HMAC-signed CSV.

        Returns (csv_bytes, hmac_hex).
        The HMAC header allows the recipient to verify the CSV was not
        tampered with after export.
        """
        from app.models.evidence import EvidenceEvent as EE

        stmt = (
            select(EE)
            .join(Evidence, Evidence.id == EE.evidence_id)
            .where(
                Evidence.case_id == case_id,
                Evidence.organization_id == org_id,
            )
            .order_by(EE.occurred_at.asc())
        )
        result = await self._session.execute(stmt)
        events = list(result.scalars().all())

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "event_id", "evidence_id", "event_type",
            "actor_id", "actor_name", "ip_address",
            "metadata", "occurred_at",
        ])
        for ev in events:
            writer.writerow([
                str(ev.id),
                str(ev.evidence_id),
                ev.event_type,
                str(ev.actor_id) if ev.actor_id else "",
                ev.actor_name,
                str(ev.ip_address) if ev.ip_address else "",
                __import__("json").dumps(ev.metadata, default=str),
                ev.occurred_at.isoformat(),
            ])

        csv_bytes = buf.getvalue().encode("utf-8")
        hmac_hex = hmac.new(
            settings.audit_hmac_key.encode(),
            csv_bytes,
            hashlib.sha256,
        ).hexdigest()

        # Log the export event on each evidence in the case
        for ev in events:
            already = {e.evidence_id for e in events if e.event_type == "chain_exported"}
            if ev.evidence_id not in already:
                self._session.add(
                    EvidenceEvent(
                        organization_id=org_id,
                        evidence_id=ev.evidence_id,
                        event_type="chain_exported",
                        actor_id=user_id,
                        actor_name=user_display_name,
                        ip_address=ip_address,
                        metadata={"hmac": hmac_hex[:16] + "…"},
                    )
                )
                already.add(ev.evidence_id)

        await self._session.commit()
        return csv_bytes, hmac_hex

    # ──────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────

    async def _load_evidence(
        self,
        evidence_id: uuid.UUID,
        case_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> Evidence:
        result = await self._session.execute(
            select(Evidence).where(
                Evidence.id == evidence_id,
                Evidence.case_id == case_id,
                Evidence.organization_id == org_id,
            )
        )
        evidence = result.scalar_one_or_none()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found.",
            )
        return evidence

    async def _next_evidence_number(self, case_id: uuid.UUID) -> str:
        """
        Atomically increment the per-case counter and return EV-NNN.
        Uses PostgreSQL's ON CONFLICT … UPDATE to avoid race conditions.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = (
            pg_insert(EvidenceNumberSequence)
            .values(case_id=case_id, counter=1)
            .on_conflict_do_update(
                index_elements=["case_id"],
                set_={"counter": EvidenceNumberSequence.counter + 1},
            )
            .returning(EvidenceNumberSequence.counter)
        )
        result = await self._session.execute(stmt)
        counter = result.scalar_one()
        return f"EV-{counter:03d}"
