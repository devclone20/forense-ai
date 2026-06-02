"""
Pure domain — TOTP (RFC 6238) and backup-code operations.
Zero I/O. Testable without a database.

Standard: RFC 6238 — TOTP: Time-Based One-Time Password Algorithm.
Window: ±1 step (30s) to compensate for clock skew between client and server.
"""
import secrets
import string

import pyotp

from app.domain.password import hash_password, verify_password

_BACKUP_CODE_ALPHABET = string.ascii_uppercase + string.digits
_BACKUP_CODE_LENGTH = 10
_BACKUP_CODE_COUNT = 8
_SECRET_LENGTH = 32  # base32 chars → 160 bits of entropy


def generate_secret() -> str:
    """Generate a cryptographically-secure base32 TOTP secret (32 chars)."""
    return pyotp.random_base32(length=_SECRET_LENGTH)


def get_qr_uri(secret: str, email: str, org_name: str) -> str:
    """
    Build the otpauth:// URI for QR code generation.

    The issuer is set to org_name so authenticator apps display a
    meaningful label instead of a bare hostname.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=org_name)


def verify_code(secret: str, code: str) -> bool:
    """
    Verify a 6-digit TOTP code against the secret.

    valid_window=1 allows the previous and next 30-second windows
    to absorb clock skew without significantly weakening security.
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def generate_backup_codes() -> list[str]:
    """
    Generate 8 one-time backup codes (10 alphanumeric chars each).

    These are shown to the user ONCE in plaintext at setup time.
    Only the Argon2id hashes are persisted.
    """
    return [
        "".join(secrets.choice(_BACKUP_CODE_ALPHABET) for _ in range(_BACKUP_CODE_LENGTH))
        for _ in range(_BACKUP_CODE_COUNT)
    ]


def hash_backup_code(code: str) -> str:
    """Hash a backup code with Argon2id for storage."""
    return hash_password(code)


def verify_backup_code(code: str, hashed: str) -> bool:
    """Verify a backup code against its stored Argon2id hash."""
    return verify_password(code, hashed)
