"""
FastAPI dependencies: authentication, RLS session, current user injection.

Auth strategy for this phase: JWT decode only (no full auth service yet —
that is scoped to the platform-foundation spec). The JWT must contain:
  - sub: user_id (UUID)
  - org_id: organisation UUID
  - email: user email
  - display_name: user display name
  - role: global_role (admin | perito | viewer)
"""
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.tenant import CurrentUser, extract_claims, set_rls_context


async def get_db_with_rls(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session with PostgreSQL RLS context set.
    The org_id is extracted from the JWT and set via set_config.
    """
    claims = extract_claims(request)
    org_id = uuid.UUID(claims["org_id"])
    await set_rls_context(session, org_id)
    yield session


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_with_rls),
) -> CurrentUser:
    """Extract and return the authenticated user from JWT claims."""
    claims = extract_claims(request)
    return CurrentUser(
        user_id=uuid.UUID(claims["sub"]),
        org_id=uuid.UUID(claims["org_id"]),
        email=claims["email"],
        display_name=claims["display_name"],
        global_role=claims.get("role", "viewer"),
    )


# Convenience type aliases
DBSession = Annotated[AsyncSession, Depends(get_db_with_rls)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
