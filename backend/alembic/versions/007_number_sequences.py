"""007 case_number_sequences

Revision ID: 007
Revises: 006
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_number_sequences",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("counter", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("organization_id", "year"),
    )

    # RLS: each org manages its own sequences
    op.execute("ALTER TABLE case_number_sequences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_number_sequences FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY sequences_org_isolation ON case_number_sequences
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS sequences_org_isolation ON case_number_sequences")
    op.drop_table("case_number_sequences")
