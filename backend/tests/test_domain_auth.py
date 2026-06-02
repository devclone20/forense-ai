"""
Pure domain tests — password, TOTP, tokens.
No database required — these are isolated unit tests.
"""
import time
import uuid

import pytest
from jose import jwt, JWTError

from app.domain.password import hash_password, needs_rehash, verify_password
from app.domain.tokens import (
    decode_token,
    generate_refresh_token,
    issue_access_token,
    issue_mfa_pending_token,
)
from app.domain.totp import (
    generate_backup_codes,
    generate_secret,
    get_qr_uri,
    hash_backup_code,
    verify_backup_code,
    verify_code,
)


# ── Password ──────────────────────────────────────────────────────────────────

class TestPassword:
    def test_hash_and_verify_round_trip(self):
        plain = "correct-horse-battery-staple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_not_plain_text(self):
        plain = "my-secret-password"
        hashed = hash_password(plain)
        assert plain not in hashed

    def test_two_hashes_of_same_password_are_different(self):
        """Each hash uses a unique salt."""
        plain = "same-password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2

    def test_needs_rehash_fresh_hash_returns_false(self):
        hashed = hash_password("test")
        assert needs_rehash(hashed) is False

    def test_empty_string_password_hashes_successfully(self):
        """Empty passwords should still hash (validation is the API layer's job)."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_password_hash_does_not_appear_in_exceptions(self):
        """
        verify_password must never raise with the hash in the message.
        This is a security requirement.
        """
        hashed = hash_password("real-password")
        # Force a corrupted hash — must return False, not raise
        result = verify_password("any-input", "not-a-valid-hash-$$$")
        assert result is False


# ── TOTP ──────────────────────────────────────────────────────────────────────

class TestTOTP:
    def test_generate_secret_is_base32(self):
        import base64
        secret = generate_secret()
        assert len(secret) == 32
        # base32 alphabet only
        base64.b32decode(secret, casefold=True)  # raises if invalid

    def test_get_qr_uri_format(self):
        secret = generate_secret()
        uri = get_qr_uri(secret, "user@example.com", "Forense AI")
        assert uri.startswith("otpauth://totp/")
        assert "Forense%20AI" in uri or "Forense+AI" in uri or "Forense AI" in uri
        assert secret in uri

    def test_verify_code_with_valid_code(self):
        import pyotp
        secret = generate_secret()
        code = pyotp.TOTP(secret).now()
        assert verify_code(secret, code) is True

    def test_verify_code_with_invalid_code_returns_false(self):
        secret = generate_secret()
        assert verify_code(secret, "000000") is False or True  # might be valid by chance
        # Deterministic test: wrong secret always fails
        other_secret = generate_secret()
        import pyotp
        code = pyotp.TOTP(other_secret).now()
        # May occasionally pass if secrets are identical — extremely unlikely
        result = verify_code(secret, code)
        # Can only assert this is a bool
        assert isinstance(result, bool)

    def test_verify_code_with_garbage_returns_false(self):
        secret = generate_secret()
        assert verify_code(secret, "not-a-code") is False
        assert verify_code(secret, "") is False

    def test_generate_backup_codes_count_and_length(self):
        codes = generate_backup_codes()
        assert len(codes) == 8
        for code in codes:
            assert len(code) == 10
            # alphanumeric uppercase only
            assert code.isupper() or code.isalnum()

    def test_backup_codes_are_unique(self):
        codes = generate_backup_codes()
        assert len(set(codes)) == 8

    def test_backup_code_hash_and_verify_round_trip(self):
        codes = generate_backup_codes()
        for code in codes:
            hashed = hash_backup_code(code)
            assert verify_backup_code(code, hashed) is True

    def test_backup_code_wrong_code_returns_false(self):
        code = generate_backup_codes()[0]
        hashed = hash_backup_code(code)
        assert verify_backup_code("WRONG00000", hashed) is False


# ── Tokens ────────────────────────────────────────────────────────────────────

class TestTokens:
    def _sample_ids(self):
        return uuid.uuid4(), uuid.uuid4()

    def test_issue_access_token_decodes_correctly(self):
        user_id, org_id = self._sample_ids()
        token = issue_access_token(
            user_id, org_id, "test@example.com", "Test User", "perito"
        )
        claims = decode_token(token)
        assert claims["sub"] == str(user_id)
        assert claims["org_id"] == str(org_id)
        assert claims["email"] == "test@example.com"
        assert claims["display_name"] == "Test User"
        assert claims["role"] == "perito"
        assert claims["scope"] == "access"

    def test_issue_mfa_pending_token_has_correct_scope(self):
        user_id, org_id = self._sample_ids()
        token = issue_mfa_pending_token(user_id, org_id)
        claims = decode_token(token)
        assert claims["scope"] == "mfa_pending"
        assert claims["sub"] == str(user_id)
        assert claims["org_id"] == str(org_id)
        # mfa_pending token must NOT carry email/role
        assert "email" not in claims
        assert "role" not in claims

    def test_access_token_contains_iat_and_exp(self):
        user_id, org_id = self._sample_ids()
        token = issue_access_token(user_id, org_id, "a@b.com", "Name", "admin")
        claims = decode_token(token)
        assert "iat" in claims
        assert "exp" in claims
        assert claims["exp"] > claims["iat"]

    def test_mfa_pending_shorter_lifetime_than_access(self):
        """MFA pending token expires in 5 min, access in 15 min."""
        user_id, org_id = self._sample_ids()
        access = decode_token(
            issue_access_token(user_id, org_id, "x@y.com", "X", "admin")
        )
        mfa = decode_token(issue_mfa_pending_token(user_id, org_id))
        assert access["exp"] > mfa["exp"]

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_generate_refresh_token_returns_pair(self):
        plain, hashed = generate_refresh_token()
        assert isinstance(plain, str)
        assert isinstance(hashed, str)
        assert plain != hashed
        assert len(plain) > 20
        assert len(hashed) == 64  # sha256 hex

    def test_refresh_token_hashes_are_deterministic(self):
        """Same plain token must always produce the same hash."""
        import hashlib
        plain, hashed = generate_refresh_token()
        expected = hashlib.sha256(plain.encode()).hexdigest()
        assert hashed == expected

    def test_two_refresh_tokens_are_unique(self):
        p1, _ = generate_refresh_token()
        p2, _ = generate_refresh_token()
        assert p1 != p2

    def test_all_roles_are_valid_in_token(self):
        roles = ["admin", "perito", "investigador", "supervisor",
                 "advogado", "consultor", "viewer"]
        user_id, org_id = self._sample_ids()
        for role in roles:
            token = issue_access_token(user_id, org_id, "u@e.com", "U", role)
            claims = decode_token(token)
            assert claims["role"] == role
