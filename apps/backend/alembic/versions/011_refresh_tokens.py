"""011 refresh_tokens — opaque refresh token store with family tracking

Revision ID: 011
Revises: 010
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE refresh_tokens (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL,
            token_hash      TEXT NOT NULL UNIQUE,
            family_id       UUID NOT NULL,
            expires_at      TIMESTAMPTZ NOT NULL,
            revoked_at      TIMESTAMPTZ,
            replaced_by     UUID REFERENCES refresh_tokens(id),
            ip_address      INET,
            user_agent      TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
    op.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")
    op.execute("CREATE INDEX ix_refresh_tokens_family_id ON refresh_tokens (family_id)")
    op.execute("CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
