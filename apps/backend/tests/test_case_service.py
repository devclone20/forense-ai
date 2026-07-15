"""
Integration tests for CaseService.

Uses a real test database session with RLS context set.
"""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.case_state_machine import JustificationRequired
from app.models.organization import Organization
from app.models.user import User
from app.schemas.case import CaseCreate, CaseTransitionRequest, CaseUpdate
from app.services.case_service import CaseService


async def _set_org(session: AsyncSession, org_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_org_id', :v, true)"),
        {"v": str(org_id)},
    )


@pytest.mark.asyncio
async def test_create_case(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    await _set_org(session, org_a.id)
    svc = CaseService(session)

    case = await svc.create_case(
        org_id=org_a.id,
        owner_id=user_a.id,
        owner_display_name=user_a.display_name,
        number_format="FOR-{YYYY}-{NNNNN}",
        data=CaseCreate(
            title="Test Case Alpha",
            forensic_domain="digital",
            description="Test description",
        ),
    )

    assert case.id is not None
    assert case.title == "Test Case Alpha"
    assert case.status == "aberto"
    assert case.forensic_domain == "digital"
    assert case.case_number.startswith("FOR-")
    assert case.organization_id == org_a.id
    assert case.owner_id == user_a.id


@pytest.mark.asyncio
async def test_case_number_increments_atomically(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    await _set_org(session, org_a.id)
    svc = CaseService(session)

    data = CaseCreate(title="Case", forensic_domain="digital")
    c1 = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}", data=data,
    )
    c2 = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}", data=data,
    )

    # Numbers must be different and incrementing
    assert c1.case_number != c2.case_number


@pytest.mark.asyncio
async def test_update_case(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    await _set_org(session, org_a.id)
    svc = CaseService(session)

    case = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}",
        data=CaseCreate(title="Original Title", forensic_domain="digital"),
    )

    updated = await svc.update_case(
        case_id=case.id,
        org_id=org_a.id,
        actor_id=user_a.id,
        actor_display_name=user_a.display_name,
        data=CaseUpdate(title="Updated Title"),
    )

    assert updated.title == "Updated Title"


@pytest.mark.asyncio
async def test_valid_state_transition(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    await _set_org(session, org_a.id)
    svc = CaseService(session)

    case = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}",
        data=CaseCreate(title="State Test", forensic_domain="medico_legal"),
    )
    assert case.status == "aberto"

    transitioned = await svc.transition_state(
        case_id=case.id,
        org_id=org_a.id,
        actor_id=user_a.id,
        actor_display_name=user_a.display_name,
        request=CaseTransitionRequest(to_status="em_investigacao"),
        is_admin=True,
    )
    assert transitioned.status == "em_investigacao"


@pytest.mark.asyncio
async def test_invalid_transition_raises(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    from fastapi import HTTPException

    await _set_org(session, org_a.id)
    svc = CaseService(session)

    case = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}",
        data=CaseCreate(title="Bad Transition", forensic_domain="financeiro"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.transition_state(
            case_id=case.id,
            org_id=org_a.id,
            actor_id=user_a.id,
            actor_display_name="x",
            request=CaseTransitionRequest(to_status="arquivado"),
        )
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_backward_transition_requires_justification(
    session: AsyncSession,
    org_a: Organization,
    user_a: User,
) -> None:
    from fastapi import HTTPException

    await _set_org(session, org_a.id)
    svc = CaseService(session)

    case = await svc.create_case(
        org_id=org_a.id, owner_id=user_a.id,
        owner_display_name="x", number_format="FOR-{YYYY}-{NNNNN}",
        data=CaseCreate(title="Justify Test", forensic_domain="digital"),
    )

    # Move to em_investigacao first
    await svc.transition_state(
        case_id=case.id, org_id=org_a.id, actor_id=user_a.id,
        actor_display_name="x",
        request=CaseTransitionRequest(to_status="em_investigacao"),
    )

    # Try backward without justification
    with pytest.raises(HTTPException) as exc_info:
        await svc.transition_state(
            case_id=case.id, org_id=org_a.id, actor_id=user_a.id,
            actor_display_name="x",
            request=CaseTransitionRequest(to_status="aberto"),
        )
    assert exc_info.value.status_code == 422

    # With justification — should succeed
    result = await svc.transition_state(
        case_id=case.id, org_id=org_a.id, actor_id=user_a.id,
        actor_display_name="x",
        request=CaseTransitionRequest(
            to_status="aberto",
            justification="Reopening for reclassification",
        ),
    )
    assert result.status == "aberto"
