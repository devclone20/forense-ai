"""
Tenant middleware: extracts org_id from JWT and sets PostgreSQL session config
`app.current_org_id` so RLS policies are enforced automatically.
"""
import uuid
from typing import Any

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def _decode_jwt(token: str) -> dict[str, Any]:
    """Decode and validate JWT, returning payload."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def extract_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header.removeprefix("Bearer ").strip()


def extract_claims(request: Request) -> dict[str, Any]:
    """Decode JWT and return claims. Caches on request state."""
    if not hasattr(request.state, "jwt_claims"):
        token = extract_token(request)
        request.state.jwt_claims = _decode_jwt(token)
    return request.state.jwt_claims


async def set_rls_context(session: AsyncSession, org_id: uuid.UUID) -> None:
    """Set PostgreSQL session variable for RLS enforcement."""
    await session.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": str(org_id)},
    )


class CurrentUser:
    """Value object injected by the auth dependency."""

    def __init__(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        email: str,
        display_name: str,
        global_role: str,
    ) -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.display_name = display_name
        self.global_role = global_role

    @property
    def is_admin(self) -> bool:
        return self.global_role == "admin"

    @property
    def is_perito(self) -> bool:
        return self.global_role in ("admin", "perito")
