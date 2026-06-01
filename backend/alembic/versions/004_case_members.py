"""004 case_members

Revision ID: 004
Revises: 003
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE case_role AS ENUM ('responsavel', 'investigador', 'supervisor', 'consultor')")

    op.create_table(
        "case_members",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("responsavel", "investigador", "supervisor", "consultor", name="case_role"), nullable=False),
        sa.Column("assigned_by", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("removed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("removed_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_case_members_case_id", "case_members", ["case_id"])
    op.create_index("ix_case_members_user_id", "case_members", ["user_id"])
    # Partial unique: one active membership per user per case
    op.execute("""
        CREATE UNIQUE INDEX uq_case_members_active
        ON case_members (case_id, user_id)
        WHERE removed_at IS NULL
    """)

    op.execute("ALTER TABLE case_members ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_members FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY case_members_org_isolation ON case_members
        USING (
            case_id IN (
                SELECT id FROM cases
                WHERE organization_id = current_setting('app.current_org_id', true)::uuid
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS case_members_org_isolation ON case_members")
    op.drop_index("uq_case_members_active", table_name="case_members")
    op.drop_index("ix_case_members_user_id", table_name="case_members")
    op.drop_index("ix_case_members_case_id", table_name="case_members")
    op.drop_table("case_members")
    op.execute("DROP TYPE IF EXISTS case_role")
