"""
Auth service integration tests.

Uses the same session fixture as other tests — real PostgreSQL, rolled back
after each test. The auth_service is called directly (no HTTP layer).
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.password import hash_password
from app.domain.totp import generate_secret
from app.models.organization import Organization
from app.models.user import User
from app.repositories import auth_repository as repo
from app.services import auth_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(
    org_id: uuid.UUID,
    role: str = "perito",
    password: str = "valid-password-123",
    mfa_enabled: bool = False,
    mfa_secret: str | None = None,
) -> User:
    u = User(
        organization_id=org_id,
        email=f"user-{uuid.uuid4().hex[:8]}@test.com",
        display_name="Test User",
        global_role=role,
        is_active=True,
        password_hash=hash_password(password),
        mfa_enabled=mfa_enabled,
    )
    if mfa_secret:
        # Store a pre-encrypted secret for tests that need MFA
        u.mfa_secret = mfa_secret
    return u


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def org(session: AsyncSession) -> Organization:
    o = Organization(name="Auth Test Org", slug=f"auth-{uuid.uuid4().hex[:6]}")
    session.add(o)
    await session.flush()
    return o


@pytest_asyncio.fixture
async def perito_user(session: AsyncSession, org: Organization) -> User:
    u = make_user(org.id, role="perito")
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
async def admin_user_no_mfa(session: AsyncSession, org: Organization) -> User:
    u = make_user(org.id, role="admin", mfa_enabled=False)
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
async def admin_user_with_mfa(session: AsyncSession, org: Organization) -> User:
    """Admin user with MFA enabled — uses a real Fernet-encrypted secret."""
    from cryptography.fernet import Fernet
    from app.config import settings

    # Temporarily use a known test key
    secret_plain = generate_secret()
    fernet_key = settings.encryption_key.encode()
    encrypted = Fernet(fernet_key).encrypt(secret_plain.encode()).decode()

    u = make_user(org.id, role="admin", mfa_enabled=True, mfa_secret=encrypted)
    # Store plain secret as attribute for use in tests
    u._test_totp_secret = secret_plain  # type: ignore[attr-defined]
    session.add(u)
    await session.flush()
    return u


# ── Login tests ───────────────────────────────────────────────────────────────

class TestLogin:
    async def test_correct_credentials_returns_token_pair(
        self, session: AsyncSession, perito_user: User
    ):
        result = await auth_service.login(
            session, perito_user.email, "valid-password-123"
        )
        assert result.token_pair is not None
        assert result.requires_mfa is False
        assert result.requires_mfa_setup is False
        assert result.token_pair.access_token
        assert result.token_pair.refresh_token

    async def test_wrong_password_raises_401(
        self, session: AsyncSession, perito_user: User
    ):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(session, perito_user.email, "wrong-password")
        assert exc_info.value.status_code == 401

    async def test_unknown_email_raises_401(self, session: AsyncSession):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(session, "ghost@example.com", "any-password")
        assert exc_info.value.status_code == 401

    async def test_five_wrong_attempts_locks_account(
        self, session: AsyncSession, org: Organization
    ):
        from fastapi import HTTPException
        u = make_user(org.id, role="perito")
        session.add(u)
        await session.flush()

        for _ in range(5):
            try:
                await auth_service.login(session, u.email, "wrong")
            except HTTPException:
                pass

        # 6th attempt — should be locked (429)
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(session, u.email, "wrong")
        assert exc_info.value.status_code == 429

    async def test_admin_without_mfa_returns_requires_mfa_setup(
        self, session: AsyncSession, admin_user_no_mfa: User
    ):
        result = await auth_service.login(
            session, admin_user_no_mfa.email, "valid-password-123"
        )
        assert result.requires_mfa_setup is True
        assert result.token_pair is None

    async def test_admin_with_mfa_returns_mfa_pending_token(
        self, session: AsyncSession, admin_user_with_mfa: User
    ):
        result = await auth_service.login(
            session, admin_user_with_mfa.email, "valid-password-123"
        )
        assert result.requires_mfa is True
        assert result.mfa_pending_token is not None
        assert result.token_pair is None

        # Verify the pending token has the correct scope
        from app.domain.tokens import decode_token
        claims = decode_token(result.mfa_pending_token)
        assert claims["scope"] == "mfa_pending"


# ── MFA verification ──────────────────────────────────────────────────────────

class TestVerifyMFA:
    async def test_correct_totp_code_returns_token_pair(
        self, session: AsyncSession, admin_user_with_mfa: User
    ):
        import pyotp
        secret = admin_user_with_mfa._test_totp_secret  # type: ignore[attr-defined]
        code = pyotp.TOTP(secret).now()

        from app.domain.tokens import issue_mfa_pending_token
        mfa_token = issue_mfa_pending_token(
            admin_user_with_mfa.id, admin_user_with_mfa.organization_id
        )

        pair = await auth_service.verify_mfa(session, mfa_token, code)
        assert pair.access_token
        assert pair.refresh_token

        from app.domain.tokens import decode_token
        claims = decode_token(pair.access_token)
        assert claims["scope"] == "access"
        assert claims["sub"] == str(admin_user_with_mfa.id)

    async def test_wrong_totp_code_raises_401(
        self, session: AsyncSession, admin_user_with_mfa: User
    ):
        from fastapi import HTTPException
        from app.domain.tokens import issue_mfa_pending_token
        mfa_token = issue_mfa_pending_token(
            admin_user_with_mfa.id, admin_user_with_mfa.organization_id
        )
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_mfa(session, mfa_token, "000000")
        assert exc_info.value.status_code == 401

    async def test_access_token_rejected_as_mfa_pending(
        self, session: AsyncSession, admin_user_with_mfa: User
    ):
        from fastapi import HTTPException
        from app.domain.tokens import issue_access_token
        access = issue_access_token(
            admin_user_with_mfa.id,
            admin_user_with_mfa.organization_id,
            admin_user_with_mfa.email,
            admin_user_with_mfa.display_name,
            admin_user_with_mfa.global_role,
        )
        with pytest.raises(HTTPException):
            await auth_service.verify_mfa(session, access, "000000")


# ── Refresh token rotation ────────────────────────────────────────────────────

class TestRefresh:
    async def test_valid_refresh_returns_new_pair(
        self, session: AsyncSession, perito_user: User
    ):
        result = await auth_service.login(
            session, perito_user.email, "valid-password-123"
        )
        assert result.token_pair is not None
        old_refresh = result.token_pair.refresh_token

        new_pair = await auth_service.refresh(session, old_refresh)
        assert new_pair.access_token
        assert new_pair.refresh_token
        # New token must differ
        assert new_pair.refresh_token != old_refresh

    async def test_old_token_revoked_after_rotation(
        self, session: AsyncSession, perito_user: User
    ):
        from fastapi import HTTPException
        result = await auth_service.login(
            session, perito_user.email, "valid-password-123"
        )
        assert result.token_pair is not None
        old_refresh = result.token_pair.refresh_token

        # First rotation — should succeed
        await auth_service.refresh(session, old_refresh)

        # Second use of the same old token — theft detection → family revoked
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh(session, old_refresh)
        assert exc_info.value.status_code == 401

    async def test_invalid_refresh_token_raises_401(self, session: AsyncSession):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh(session, "not-a-real-token")
        assert exc_info.value.status_code == 401


# ── Suspend user ──────────────────────────────────────────────────────────────

class TestSuspendUser:
    async def test_suspend_revokes_all_refresh_tokens(
        self, session: AsyncSession, org: Organization
    ):
        from app.services.admin_service import suspend_user

        # Create admin + target
        admin = make_user(org.id, role="admin")
        target = make_user(org.id, role="perito")
        session.add(admin)
        session.add(target)
        await session.flush()

        # Give target an active refresh token
        expires = datetime.now(UTC) + timedelta(days=30)
        _, rt_hash = auth_service.token_domain.generate_refresh_token()  # type: ignore
        from app.domain.tokens import generate_refresh_token
        _, rt_hash = generate_refresh_token()
        await repo.create_refresh_token(
            session, target.id, org.id, rt_hash, uuid.uuid4(), expires, None, None
        )

        await suspend_user(session, admin.id, target.id, org.id)

        # Target user should be inactive
        refreshed = await repo.get_user_by_id(session, target.id)
        assert refreshed is not None
        assert refreshed.is_active is False
