"""
Pure domain — password hashing and verification.
Zero I/O. Testable without a database.

Algorithm: Argon2id (winner of Password Hashing Competition 2015).
Parameters follow OWASP recommended minimums for 2024+.
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password with Argon2id.

    Returns an encoded string that includes the salt and parameters —
    safe to store directly in the database.

    Never logs or re-raises with the plaintext value.
    """
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns True if the password matches, False otherwise.
    Does NOT raise — exceptions are swallowed and mapped to False
    to prevent timing oracle attacks.
    """
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """
    Return True if the stored hash was produced with outdated parameters
    and should be re-hashed after a successful login.
    """
    return _hasher.check_needs_rehash(hashed)
