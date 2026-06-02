"""013 org invite expiry — per-org configurable invitation TTL

Revision ID: 013
Revises: 012
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE organizations
            ADD COLUMN invite_expiry_days INTEGER NOT NULL DEFAULT 7
            CHECK (invite_expiry_days BETWEEN 1 AND 90)
    """)


def downgrade() -> None:
    op.drop_column("organizations", "invite_expiry_days")
