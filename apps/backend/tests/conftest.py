"""
Test configuration and fixtures.

Uses a real PostgreSQL test database (same container, separate DB).
Each test gets a fresh transaction rolled back at the end — no data leaks.
"""
import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User

# Test database — must be created before running tests:
# createdb forense_ai_test  (or use docker exec)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://forense_app:dev_only_password@localhost:5432/forense_ai_test"
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Each test gets a session with a savepoint, rolled back after."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as sess:
        async with sess.begin():
            yield sess
            await sess.rollback()


async def _set_org_context(session: AsyncSession, org_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_org_id', :v, true)"),
        {"v": str(org_id)},
    )


@pytest_asyncio.fixture
async def org_a(session: AsyncSession) -> Organization:
    org = Organization(name="Org Alpha", slug=f"org-alpha-{uuid.uuid4().hex[:6]}")
    session.add(org)
    await session.flush()
    return org


@pytest_asyncio.fixture
async def org_b(session: AsyncSession) -> Organization:
    org = Organization(name="Org Beta", slug=f"org-beta-{uuid.uuid4().hex[:6]}")
    session.add(org)
    await session.flush()
    return org


@pytest_asyncio.fixture
async def user_a(session: AsyncSession, org_a: Organization) -> User:
    await _set_org_context(session, org_a.id)
    user = User(
        organization_id=org_a.id,
        email=f"user-a-{uuid.uuid4().hex[:6]}@test.com",
        display_name="User Alpha",
        global_role="admin",
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def user_b(session: AsyncSession, org_b: Organization) -> User:
    await _set_org_context(session, org_b.id)
    user = User(
        organization_id=org_b.id,
        email=f"user-b-{uuid.uuid4().hex[:6]}@test.com",
        display_name="User Beta",
        global_role="perito",
    )
    session.add(user)
    await session.flush()
    return user
