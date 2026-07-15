"""
CRITICAL: RLS isolation tests.

Verifies that an organisation cannot see another organisation's data,
even when using the same database session with different RLS contexts.

This test must pass before any deploy.
"""
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.organization import Organization
from app.models.user import User
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate, CaseListFilters


async def _set_org(session: AsyncSession, org_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_org_id', :v, true)"),
        {"v": str(org_id)},
    )


@pytest.mark.asyncio
async def test_org_a_cannot_see_org_b_cases(
    session: AsyncSession,
    org_a: Organization,
    org_b: Organization,
    user_a: User,
    user_b: User,
) -> None:
    """
    Core RLS test:
    1. Create a case in org_a context.
    2. Query with org_b context.
    3. Assert: zero results returned.
    """
    # --- Create case in org_a ---
    await _set_org(session, org_a.id)
    repo_a = CaseRepository(session)
    case = await repo_a.create(
        org_id=org_a.id,
        owner_id=user_a.id,
        case_number="FOR-2026-00001",
        data=CaseCreate(
            title="Secret case in Org A",
            forensic_domain="digital",
        ),
    )
    assert case.id is not None
    assert case.organization_id == org_a.id

    # --- Switch to org_b context ---
    await _set_org(session, org_b.id)
    repo_b = CaseRepository(session)

    # Direct lookup by ID should return None
    result = await repo_b.get_by_id(case.id, org_b.id)
    assert result is None, "Org B should not be able to retrieve Org A's case by ID"

    # List query should return zero results
    cases, total = await repo_b.list_with_filters(
        org_b.id, CaseListFilters()
    )
    ids = [c.id for c in cases]
    assert case.id not in ids, "Org A's case must not appear in Org B's list"
    assert total == 0, f"Expected 0 results for Org B, got {total}"


@pytest.mark.asyncio
async def test_org_b_can_see_own_cases(
    session: AsyncSession,
    org_b: Organization,
    user_b: User,
) -> None:
    """Positive test: org_b can see its own cases."""
    await _set_org(session, org_b.id)
    repo = CaseRepository(session)

    case = await repo.create(
        org_id=org_b.id,
        owner_id=user_b.id,
        case_number="FOR-2026-00001",
        data=CaseCreate(
            title="Org B's own case",
            forensic_domain="financeiro",
        ),
    )

    found = await repo.get_by_id(case.id, org_b.id)
    assert found is not None
    assert found.id == case.id

    cases, total = await repo.list_with_filters(org_b.id, CaseListFilters())
    assert total >= 1
    assert any(c.id == case.id for c in cases)


@pytest.mark.asyncio
async def test_audit_log_isolation(
    session: AsyncSession,
    org_a: Organization,
    org_b: Organization,
    user_a: User,
) -> None:
    """Audit log entries for org_a are not visible to org_b."""
    from app.repositories.audit_log_repository import AuditLogRepository

    await _set_org(session, org_a.id)
    audit = AuditLogRepository(session)

    log_entry = await audit.append(
        org_id=org_a.id,
        action="case_created",
        actor_id=user_a.id,
        actor_display_name="User Alpha",
        metadata={"test": True},
    )
    assert log_entry.id is not None

    # Switch to org_b — the audit log entry should be invisible
    await _set_org(session, org_b.id)
    entries = await audit.list_after(org_b.id, after=log_entry.occurred_at.replace(
        year=log_entry.occurred_at.year - 1
    ))
    entry_ids = [e.id for e in entries]
    assert log_entry.id not in entry_ids, "Org B must not see Org A's audit log entries"
