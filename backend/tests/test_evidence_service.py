"""
Evidence service tests.

Requires a live PostgreSQL test database with migrations applied.
Run: pytest tests/test_evidence_service.py -v
"""
from __future__ import annotations

import asyncio
import io
import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence, EvidenceNumberSequence, StorageConfig
from app.schemas.evidence import EvidenceIngestMetadata
from app.services.evidence_service import EvidenceService
from app.storage import StorageRef
from app.storage.factory import encrypt_credentials


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _set_org(session: AsyncSession, org_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_org_id', :v, true)"),
        {"v": str(org_id)},
    )


def _make_upload_file(content: bytes, filename: str = "test.bin") -> MagicMock:
    """Build a minimal UploadFile mock that streams content."""
    pos = [0]

    async def _read(size: int = -1) -> bytes:
        if size == -1:
            chunk = content[pos[0]:]
            pos[0] = len(content)
        else:
            chunk = content[pos[0]:pos[0] + size]
            pos[0] += len(chunk)
        return chunk

    mock = MagicMock()
    mock.filename = filename
    mock.content_type = "application/octet-stream"
    mock.size = len(content)
    mock.read = _read
    return mock


def _meta(title: str = "Test Evidence") -> EvidenceIngestMetadata:
    return EvidenceIngestMetadata(
        title=title,
        evidence_type="ficheiro_sistema",
    )


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def with_storage(session: AsyncSession, org_a, user_a) -> StorageConfig:
    """Insert a local storage config for org_a."""
    await _set_org(session, org_a.id)
    creds = encrypt_credentials({"base_path": "/tmp/forense-test"})
    config = StorageConfig(
        organization_id=org_a.id,
        backend="local",
        credentials_encrypted=creds,
        max_file_bytes=10 * 1024 * 1024,   # 10 MB
        quota_bytes=100 * 1024 * 1024,     # 100 MB
        used_bytes=0,
        configured_by=user_a.id,
    )
    session.add(config)
    await session.flush()
    return config


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestIngest:
    async def test_upload_creates_evidence_with_correct_hash(
        self, session: AsyncSession, org_a, user_a, with_storage, tmp_path
    ):
        """A successful ingest stores the SHA-256 hash correctly."""
        import hashlib
        content = b"Hello, forensic world!" * 100
        expected_hash = hashlib.sha256(content).hexdigest()

        await _set_org(session, org_a.id)

        # Patch LocalStorageProvider so it writes to tmp_path
        base = str(tmp_path)
        with patch("app.services.evidence_service.get_storage_provider") as mock_factory:
            from app.storage.local import LocalStorageProvider
            mock_factory.return_value = LocalStorageProvider(base_path=base)

            svc = EvidenceService(session)
            file_mock = _make_upload_file(content)

            # We need a real case_id that exists — use org_a.id as a placeholder
            # In a full integration test this would be a real case UUID
            case_id = uuid.uuid4()
            # Insert a minimal case row for FK satisfaction
            await session.execute(
                text("""
                    INSERT INTO cases (id, organization_id, case_number, title,
                                       forensic_domain, status, confidentiality, owner_id)
                    VALUES (:id, :org_id, 'TC-001', 'Test Case',
                            'digital', 'aberto', 'normal', :owner_id)
                """),
                {"id": str(case_id), "org_id": str(org_a.id), "owner_id": str(user_a.id)},
            )
            await session.flush()

            evidence = await svc.ingest(
                case_id=case_id,
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
                file=file_mock,
                metadata=_meta(),
            )

        assert evidence.sha256_hash == expected_hash
        assert evidence.size_bytes == len(content)
        assert evidence.evidence_number.startswith("EV-")

    async def test_upload_rejected_when_exceeds_max_file_bytes(
        self, session: AsyncSession, org_a, user_a, with_storage
    ):
        """File larger than max_file_bytes must be rejected BEFORE touching storage."""
        from fastapi import HTTPException

        await _set_org(session, org_a.id)
        # 11 MB — exceeds 10 MB limit
        content = b"x" * (11 * 1024 * 1024)
        file_mock = _make_upload_file(content)

        svc = EvidenceService(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.ingest(
                case_id=uuid.uuid4(),
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
                file=file_mock,
                metadata=_meta(),
            )
        assert exc_info.value.status_code == 413

    async def test_upload_rejected_when_quota_exceeded(
        self, session: AsyncSession, org_a, user_a, with_storage
    ):
        """Upload that would exceed the org quota is rejected before touching storage."""
        from fastapi import HTTPException

        # Set used_bytes close to quota
        with_storage.used_bytes = 99 * 1024 * 1024  # 99 MB used of 100 MB quota
        await session.flush()
        await _set_org(session, org_a.id)

        content = b"x" * (2 * 1024 * 1024)  # 2 MB — would push to 101 MB
        file_mock = _make_upload_file(content)

        svc = EvidenceService(session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.ingest(
                case_id=uuid.uuid4(),
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
                file=file_mock,
                metadata=_meta(),
            )
        assert exc_info.value.status_code == 413

    async def test_duplicate_in_same_case_is_rejected(
        self, session: AsyncSession, org_a, user_a, with_storage, tmp_path
    ):
        """Uploading the same file content twice in the same case returns 409."""
        from fastapi import HTTPException

        content = b"unique-content-for-duplicate-test"
        await _set_org(session, org_a.id)

        case_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cases (id, organization_id, case_number, title,
                                   forensic_domain, status, confidentiality, owner_id)
                VALUES (:id, :org_id, 'TC-DUP', 'Dup Test Case',
                        'digital', 'aberto', 'normal', :owner_id)
            """),
            {"id": str(case_id), "org_id": str(org_a.id), "owner_id": str(user_a.id)},
        )
        await session.flush()

        base = str(tmp_path / "dup")
        with patch("app.services.evidence_service.get_storage_provider") as mf:
            from app.storage.local import LocalStorageProvider
            mf.return_value = LocalStorageProvider(base_path=base)

            svc = EvidenceService(session)
            # First upload
            await svc.ingest(
                case_id=case_id,
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
                file=_make_upload_file(content),
                metadata=_meta("First"),
            )

            # Second upload — same content, same case
            with pytest.raises(HTTPException) as exc_info:
                await svc.ingest(
                    case_id=case_id,
                    org_id=org_a.id,
                    user_id=user_a.id,
                    user_display_name="User Alpha",
                    file=_make_upload_file(content),
                    metadata=_meta("Duplicate"),
                )
            assert exc_info.value.status_code == 409


class TestIntegrityVerification:
    async def _ingest_evidence(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        user_display_name: str,
        case_id: uuid.UUID,
        content: bytes,
        storage_base: str,
    ) -> Evidence:
        from app.storage.local import LocalStorageProvider
        with patch("app.services.evidence_service.get_storage_provider") as mf:
            mf.return_value = LocalStorageProvider(base_path=storage_base)
            svc = EvidenceService(session)
            return await svc.ingest(
                case_id=case_id,
                org_id=org_id,
                user_id=user_id,
                user_display_name=user_display_name,
                file=_make_upload_file(content),
                metadata=_meta(),
            )

    async def test_integrity_match_returns_true(
        self, session: AsyncSession, org_a, user_a, with_storage, tmp_path
    ):
        """compute_hash on un-tampered file must match stored hash."""
        await _set_org(session, org_a.id)
        case_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cases (id, organization_id, case_number, title,
                                   forensic_domain, status, confidentiality, owner_id)
                VALUES (:id, :org_id, 'TC-IV1', 'Integrity Test',
                        'digital', 'aberto', 'normal', :owner_id)
            """),
            {"id": str(case_id), "org_id": str(org_a.id), "owner_id": str(user_a.id)},
        )
        await session.flush()

        base = str(tmp_path / "integrity")
        evidence = await self._ingest_evidence(
            session, org_a.id, user_a.id, "User Alpha", case_id, b"clean-data", base
        )

        from app.storage.local import LocalStorageProvider
        with patch("app.services.evidence_service.get_storage_provider") as mf:
            mf.return_value = LocalStorageProvider(base_path=base)
            svc = EvidenceService(session)
            result = await svc.verify_integrity(
                evidence_id=evidence.id,
                case_id=case_id,
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
            )

        assert result.match is True

    async def test_integrity_tampered_file_returns_false(
        self, session: AsyncSession, org_a, user_a, with_storage, tmp_path
    ):
        """If the stored file is modified, verify_integrity must return match=False."""
        import aiofiles
        import aiofiles.os

        await _set_org(session, org_a.id)
        case_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cases (id, organization_id, case_number, title,
                                   forensic_domain, status, confidentiality, owner_id)
                VALUES (:id, :org_id, 'TC-IV2', 'Tamper Test',
                        'digital', 'aberto', 'normal', :owner_id)
            """),
            {"id": str(case_id), "org_id": str(org_a.id), "owner_id": str(user_a.id)},
        )
        await session.flush()

        base = str(tmp_path / "tamper")
        content = b"original-content"
        evidence = await self._ingest_evidence(
            session, org_a.id, user_a.id, "User Alpha", case_id, content, base
        )

        # Tamper: overwrite stored file
        from app.storage import StorageRef as SR
        from app.storage.local import LocalStorageProvider
        provider = LocalStorageProvider(base_path=base)
        stored_path = provider._resolve(SR(value=evidence.storage_ref))
        async with aiofiles.open(str(stored_path), "wb") as f:
            await f.write(b"tampered-content")

        with patch("app.services.evidence_service.get_storage_provider") as mf:
            mf.return_value = provider
            svc = EvidenceService(session)
            result = await svc.verify_integrity(
                evidence_id=evidence.id,
                case_id=case_id,
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
            )

        assert result.match is False


class TestRLS:
    async def test_evidence_not_visible_in_other_org_context(
        self, session: AsyncSession, org_a, org_b, user_a, with_storage, tmp_path
    ):
        """
        An evidence ingested in org_a must not be visible when the RLS
        context is set to org_b.
        """
        from sqlalchemy import select

        await _set_org(session, org_a.id)
        case_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO cases (id, organization_id, case_number, title,
                                   forensic_domain, status, confidentiality, owner_id)
                VALUES (:id, :org_id, 'TC-RLS', 'RLS Test',
                        'digital', 'aberto', 'normal', :owner_id)
            """),
            {"id": str(case_id), "org_id": str(org_a.id), "owner_id": str(user_a.id)},
        )
        await session.flush()

        base = str(tmp_path / "rls")
        from app.storage.local import LocalStorageProvider
        with patch("app.services.evidence_service.get_storage_provider") as mf:
            mf.return_value = LocalStorageProvider(base_path=base)
            svc = EvidenceService(session)
            ev = await svc.ingest(
                case_id=case_id,
                org_id=org_a.id,
                user_id=user_a.id,
                user_display_name="User Alpha",
                file=_make_upload_file(b"rls-test-data"),
                metadata=_meta(),
            )

        # Switch RLS context to org_b — evidence must be invisible
        await _set_org(session, org_b.id)
        result = await session.execute(
            select(Evidence).where(Evidence.id == ev.id)
        )
        assert result.scalar_one_or_none() is None
