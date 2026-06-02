"""
Password recovery service.

All responses that could reveal whether an email exists in the system
return 200 OK regardless — this is by design (enumeration protection).
"""
import logging
import uuid

from fastapi import HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain import password as pwd_domain
from app.repositories import auth_repository as repo

logger = logging.getLogger(__name__)

_SALT = "forense-ai-password-recovery"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.recovery_secret_key, salt=_SALT)


async def request_recovery(session: AsyncSession, email: str) -> None:
    """
    Initiate password recovery.

    Always returns without error, even if the email is unknown (enumeration protection).
    If the email exists, generate a signed token and stub the email delivery.
    """
    user = await repo.get_user_by_email(session, email)
    if user is None:
        # Intentional no-op — do not leak whether the email exists
        logger.info("recovery_requested: email not found (suppressed)")
        return

    token = _serializer().dumps({"user_id": str(user.id)})

    # TODO: send email via transactional provider (Resend / SendGrid)
    # For now, log the token for development purposes only.
    if settings.debug:
        logger.debug("recovery_token (dev only — never log in prod): %s", token)

    await repo.append_auth_log(
        session,
        "recovery_requested",
        user_id=user.id,
        org_id=user.organization_id,
    )
    await session.commit()


async def confirm_recovery(
    session: AsyncSession,
    token: str,
    new_password: str,
) -> None:
    """
    Validate the recovery token, set the new password, and revoke all sessions.
    """
    try:
        data = _serializer().loads(
            token, max_age=settings.recovery_token_expire_seconds
        )
    except SignatureExpired as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Recovery link has expired") from exc
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recovery token") from exc

    user_id = uuid.UUID(data["user_id"])
    user = await repo.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid recovery token")

    user.password_hash = pwd_domain.hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    await repo.revoke_all_user_tokens(session, user_id)
    await repo.append_auth_log(
        session,
        "password_changed",
        user_id=user.id,
        org_id=user.organization_id,
    )
    await repo.append_auth_log(
        session,
        "recovery_completed",
        user_id=user.id,
        org_id=user.organization_id,
    )
    await session.commit()
