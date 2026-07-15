"""
Pure domain — JWT issuance/decoding and opaque refresh-token generation.
Zero I/O. Testable without a database.

Access token lifetime : 15 minutes  (scope=access)
MFA-pending lifetime  :  5 minutes  (scope=mfa_pending)
Refresh token         : opaque UUID, rotation + family-id tracked in DB

JWT payload fields:
  sub          — user_id (UUID string)
  org_id       — organization_id (UUID string)
  email        — user email
  display_name — user display name
  role         — global_role
  scope        — "access" | "mfa_pending"
  exp          — UNIX expiry
  iat          — UNIX issued-at
"""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config import settings

_ACCESS_TOKEN_EXPIRE_MINUTES = 15
_MFA_PENDING_EXPIRE_MINUTES = 5


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def issue_access_token(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    email: str,
    display_name: str,
    role: str,
) -> str:
    """Issue a signed JWT access token (15-minute lifetime)."""
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "email": email,
        "display_name": display_name,
        "role": role,
        "scope": "access",
        "iat": now,
        "exp": now + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return _encode(payload)


def issue_mfa_pending_token(user_id: uuid.UUID, org_id: uuid.UUID) -> str:
    """
    Issue a short-lived JWT for the MFA verification step (5-minute lifetime).
    Scope is 'mfa_pending' — must NOT be accepted by protected endpoints.
    """
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "scope": "mfa_pending",
        "iat": now,
        "exp": now + timedelta(minutes=_MFA_PENDING_EXPIRE_MINUTES),
    }
    return _encode(payload)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT, returning the payload dict.

    Raises jose.JWTError (or a subclass) if the token is expired,
    has an invalid signature, or is malformed.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise


def generate_refresh_token() -> tuple[str, str]:
    """
    Generate a cryptographically-secure opaque refresh token.

    Returns (token_plain, token_hash).
    Only token_hash is stored in the database.
    token_plain is returned to the client once and never persisted.
    """
    token_plain = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token_plain.encode()).hexdigest()
    return token_plain, token_hash
