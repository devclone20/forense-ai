"""
Auth service — core authentication flows.

All business logic lives here. No HTTP concerns.
Domain modules (password, totp, tokens) are pure functions — injected by import.
Database access is via the auth_repository.
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain import password as pwd_domain
from app.domain import tokens as token_domain
from app.domain import totp as totp_domain
from app.repositories import auth_repository as repo

logger = logging.getLogger(__name__)

_LOCKOUT_THRESHOLD = 5
_LOCKOUT_DURATION_MINUTES = 15
_REFRESH_TOKEN_EXPIRE_DAYS = 30


def _fernet() -> Fernet:
    key = settings.encryption_key.encode()
    return Fernet(key)


def _encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def _decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt MFA secret") from exc


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class LoginResult:
    token_pair: TokenPair | None = None
    requires_mfa: bool = False
    requires_mfa_setup: bool = False
    mfa_pending_token: str | None = None


@dataclass
class MFASetupData:
    qr_uri: str
    backup_codes: list[str]  # plaintext — shown ONCE, never re-readable


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _issue_token_pair(
    session: AsyncSession,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    email: str,
    display_name: str,
    role: str,
    ip: str | None,
    ua: str | None,
) -> TokenPair:
    access = token_domain.issue_access_token(user_id, org_id, email, display_name, role)
    rt_plain, rt_hash = token_domain.generate_refresh_token()
    family_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    await repo.create_refresh_token(session, user_id, org_id, rt_hash,
                                    family_id, expires_at, ip, ua)
    return TokenPair(access_token=access, refresh_token=rt_plain)


# ── Public API ────────────────────────────────────────────────────────────────

async def login(
    session: AsyncSession,
    email: str,
    password: str,
    ip: str | None = None,
    ua: str | None = None,
) -> LoginResult:
    """
    Validate credentials and return the appropriate result:
      - admin without MFA configured → requires_mfa_setup
      - admin with MFA enabled       → requires_mfa + mfa_pending_token
      - everyone else                → full token pair
    """
    user = await repo.get_user_by_email(session, email)

    # Constant-time failure path (user not found → same flow as wrong password)
    if user is None:
        logger.info("login_failed: unknown email")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")

    # Lockout check
    if user.locked_until is not None:
        locked = user.locked_until
        if locked.tzinfo is None:
            locked = locked.replace(tzinfo=UTC)
        if locked > datetime.now(UTC):
            await repo.append_auth_log(session, "login_locked",
                                       user_id=user.id,
                                       org_id=user.organization_id,
                                       ip=ip, ua=ua)
            await session.commit()
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Account temporarily locked")

    if not user.password_hash or not pwd_domain.verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= _LOCKOUT_THRESHOLD:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=_LOCKOUT_DURATION_MINUTES)
            await repo.append_auth_log(session, "login_locked",
                                       user_id=user.id,
                                       org_id=user.organization_id,
                                       ip=ip, ua=ua)
        else:
            await repo.append_auth_log(session, "login_failed",
                                       user_id=user.id,
                                       org_id=user.organization_id,
                                       ip=ip, ua=ua,
                                       metadata={"attempt": user.failed_login_attempts})
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")

    # Rehash if parameters are outdated
    if pwd_domain.needs_rehash(user.password_hash):
        user.password_hash = pwd_domain.hash_password(password)

    # Reset lockout state on success
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(UTC)

    if user.global_role == "admin":
        if not user.mfa_enabled:
            await session.commit()
            return LoginResult(requires_mfa_setup=True)
        mfa_token = token_domain.issue_mfa_pending_token(user.id, user.organization_id)
        await repo.append_auth_log(session, "login_success",
                                   user_id=user.id,
                                   org_id=user.organization_id,
                                   ip=ip, ua=ua,
                                   metadata={"mfa_required": True})
        await session.commit()
        return LoginResult(requires_mfa=True, mfa_pending_token=mfa_token)

    pair = await _issue_token_pair(session, user.id, user.organization_id,
                                   user.email, user.display_name,
                                   user.global_role, ip, ua)
    await repo.append_auth_log(session, "login_success",
                               user_id=user.id,
                               org_id=user.organization_id,
                               ip=ip, ua=ua)
    await session.commit()
    return LoginResult(token_pair=pair)


async def verify_mfa(
    session: AsyncSession,
    mfa_token: str,
    totp_code: str,
    ip: str | None = None,
    ua: str | None = None,
) -> TokenPair:
    """Verify TOTP code from mfa_pending token and issue full token pair."""
    try:
        claims = token_domain.decode_token(mfa_token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired MFA token") from exc

    if claims.get("scope") != "mfa_pending":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token scope invalid")

    user_id = uuid.UUID(claims["sub"])
    user = await repo.get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found")

    if not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="MFA not configured")

    secret = _decrypt(user.mfa_secret)
    if not totp_domain.verify_code(secret, totp_code):
        await repo.append_auth_log(session, "mfa_failed",
                                   user_id=user.id,
                                   org_id=user.organization_id,
                                   ip=ip, ua=ua)
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid MFA code")

    pair = await _issue_token_pair(session, user.id, user.organization_id,
                                   user.email, user.display_name,
                                   user.global_role, ip, ua)
    await repo.append_auth_log(session, "mfa_success",
                               user_id=user.id,
                               org_id=user.organization_id,
                               ip=ip, ua=ua)
    await session.commit()
    return pair


async def refresh(
    session: AsyncSession,
    refresh_token_plain: str,
    ip: str | None = None,
    ua: str | None = None,
) -> TokenPair:
    """
    Rotate a refresh token.

    If the presented token has already been revoked but the family is still active,
    this indicates theft — all family tokens are revoked immediately.
    """
    import hashlib
    token_hash = hashlib.sha256(refresh_token_plain.encode()).hexdigest()
    rt = await repo.get_refresh_token(session, token_hash)

    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token")

    if rt.revoked_at is not None:
        # Reuse of a revoked token → potential theft, invalidate the whole family
        await repo.revoke_family(session, rt.family_id)
        user = await repo.get_user_by_id(session, rt.user_id)
        if user:
            await repo.append_auth_log(session, "token_revoked_all",
                                       user_id=user.id,
                                       org_id=user.organization_id,
                                       ip=ip, ua=ua,
                                       metadata={"reason": "reuse_detected"})
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token reuse detected — all sessions invalidated")

    if not rt.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Refresh token expired")

    user = await repo.get_user_by_id(session, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found or suspended")

    # Issue new token in the same family
    new_rt_plain, new_rt_hash = token_domain.generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    new_rt = await repo.create_refresh_token(
        session, rt.user_id, rt.organization_id,
        new_rt_hash, rt.family_id, expires_at, ip, ua,
    )
    await repo.revoke_refresh_token(session, rt.id, replaced_by=new_rt.id)

    access = token_domain.issue_access_token(
        user.id, user.organization_id,
        user.email, user.display_name, user.global_role,
    )
    await repo.append_auth_log(session, "token_refreshed",
                               user_id=user.id,
                               org_id=user.organization_id,
                               ip=ip, ua=ua)
    await session.commit()
    return TokenPair(access_token=access, refresh_token=new_rt_plain)


async def logout(
    session: AsyncSession,
    user_id: uuid.UUID,
    refresh_token_plain: str,
) -> None:
    import hashlib
    token_hash = hashlib.sha256(refresh_token_plain.encode()).hexdigest()
    rt = await repo.get_refresh_token(session, token_hash)
    if rt and rt.user_id == user_id:
        await repo.revoke_refresh_token(session, rt.id)
    await repo.append_auth_log(session, "logout", user_id=user_id)
    await session.commit()


async def setup_mfa(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> MFASetupData:
    """
    Generate and persist an encrypted MFA secret + hashed backup codes.
    Returns the QR URI and plaintext backup codes (shown ONCE).
    mfa_enabled remains False until enable_mfa() is called.
    """
    user = await repo.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    secret_plain = totp_domain.generate_secret()
    user.mfa_secret = _encrypt(secret_plain)

    org = user.organization  # may trigger lazy load — use eager if needed
    org_name = org.name if org else "Forense AI"

    qr_uri = totp_domain.get_qr_uri(secret_plain, user.email, org_name)

    backup_codes_plain = totp_domain.generate_backup_codes()
    user.mfa_backup_codes = [
        {"hash": totp_domain.hash_backup_code(c), "used_at": None}
        for c in backup_codes_plain
    ]
    # mfa_enabled stays False until enable_mfa confirms the code
    await session.flush()
    await session.commit()

    return MFASetupData(qr_uri=qr_uri, backup_codes=backup_codes_plain)


async def enable_mfa(
    session: AsyncSession,
    user_id: uuid.UUID,
    totp_code: str,
) -> None:
    """
    Confirm TOTP code and set mfa_enabled = True.
    Called after the user scans the QR code and submits the first code.
    """
    user = await repo.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="MFA setup not initiated")

    secret = _decrypt(user.mfa_secret)
    if not totp_domain.verify_code(secret, totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid TOTP code")

    user.mfa_enabled = True
    await repo.append_auth_log(session, "mfa_setup",
                               user_id=user.id,
                               org_id=user.organization_id)
    await session.commit()


async def use_backup_code(
    session: AsyncSession,
    user_id: uuid.UUID,
    code: str,
    ip: str | None = None,
    ua: str | None = None,
) -> TokenPair:
    """Use one backup code for MFA bypass. Marks it as consumed."""
    user = await repo.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    backup_codes: list[dict] = list(user.mfa_backup_codes or [])
    matched_idx: int | None = None

    for idx, entry in enumerate(backup_codes):
        if entry.get("used_at") is None and totp_domain.verify_backup_code(
            code, entry["hash"]
        ):
            matched_idx = idx
            break

    if matched_idx is None:
        await repo.append_auth_log(session, "mfa_failed",
                                   user_id=user.id,
                                   org_id=user.organization_id,
                                   ip=ip, ua=ua,
                                   metadata={"method": "backup_code"})
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or already-used backup code")

    backup_codes[matched_idx]["used_at"] = datetime.now(UTC).isoformat()
    user.mfa_backup_codes = backup_codes

    pair = await _issue_token_pair(session, user.id, user.organization_id,
                                   user.email, user.display_name,
                                   user.global_role, ip, ua)
    await repo.append_auth_log(session, "mfa_backup_used",
                               user_id=user.id,
                               org_id=user.organization_id,
                               ip=ip, ua=ua)
    await session.commit()
    return pair
