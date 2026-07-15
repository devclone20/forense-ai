"""010 invitations — org member invite system

Revision ID: 010
Revises: 009
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE invitations (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            email           TEXT NOT NULL,
            role            global_role NOT NULL,
            token_hash      TEXT NOT NULL UNIQUE,
            invited_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            expires_at      TIMESTAMPTZ NOT NULL,
            accepted_at     TIMESTAMPTZ,
            revoked_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # RLS: only members of the same org may see invitations
    op.execute("ALTER TABLE invitations ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY invitations_org_isolation ON invitations
            USING (organization_id = current_setting('app.current_org_id', true)::uuid)
    """)

    op.execute("CREATE INDEX ix_invitations_org ON invitations (organization_id)")
    op.execute("CREATE INDEX ix_invitations_token_hash ON invitations (token_hash)")
    op.execute("CREATE INDEX ix_invitations_email ON invitations (email)")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS invitations_org_isolation ON invitations")
    op.execute("DROP TABLE IF EXISTS invitations")
