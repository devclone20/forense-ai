"""012 auth_log — immutable authentication event log

Revision ID: 012
Revises: 011
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE auth_event AS ENUM (
            'login_success',
            'login_failed',
            'login_locked',
            'logout',
            'mfa_setup',
            'mfa_success',
            'mfa_failed',
            'mfa_backup_used',
            'mfa_backup_regenerated',
            'token_refreshed',
            'token_revoked_all',
            'invite_created',
            'invite_accepted',
            'invite_revoked',
            'password_changed',
            'recovery_requested',
            'recovery_completed',
            'user_suspended',
            'role_changed'
        )
    """)

    op.execute("""
        CREATE TABLE auth_log (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID REFERENCES users(id),
            organization_id UUID,
            event_type      auth_event NOT NULL,
            ip_address      INET,
            user_agent      TEXT,
            metadata        JSONB NOT NULL DEFAULT '{}',
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # Immutability: revoke UPDATE and DELETE from the application role
    op.execute("REVOKE UPDATE, DELETE ON auth_log FROM forense_app_user")

    # Immutability: trigger-level guard (belt + suspenders alongside REVOKE)
    op.execute("""
        CREATE OR REPLACE FUNCTION auth_log_immutable()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'auth_log is immutable — updates and deletes are forbidden';
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER auth_log_prevent_mutate
        BEFORE UPDATE OR DELETE ON auth_log
        FOR EACH ROW EXECUTE FUNCTION auth_log_immutable();
    """)

    op.execute("CREATE INDEX ix_auth_log_user_id ON auth_log (user_id)")
    op.execute("CREATE INDEX ix_auth_log_org_id ON auth_log (organization_id)")
    op.execute("CREATE INDEX ix_auth_log_event_type ON auth_log (event_type)")
    op.execute("CREATE INDEX ix_auth_log_occurred_at ON auth_log (occurred_at DESC)")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS auth_log_prevent_mutate ON auth_log")
    op.execute("DROP FUNCTION IF EXISTS auth_log_immutable()")
    op.execute("DROP TABLE IF EXISTS auth_log")
    op.execute("DROP TYPE IF EXISTS auth_event")
