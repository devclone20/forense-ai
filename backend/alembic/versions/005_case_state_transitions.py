"""005 case_state_transitions

Revision ID: 005
Revises: 004
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_state_transitions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.Enum("aberto", "em_investigacao", "em_revisao", "fechado", "arquivado", name="case_status"), nullable=False),
        sa.Column("to_status", sa.Enum("aberto", "em_investigacao", "em_revisao", "fechado", "arquivado", name="case_status"), nullable=False),
        sa.Column("transitioned_by", sa.UUID(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("transitioned_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transitioned_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_case_state_transitions_case_id", "case_state_transitions", ["case_id"])

    op.execute("ALTER TABLE case_state_transitions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_state_transitions FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY state_transitions_org_isolation ON case_state_transitions
        USING (
            case_id IN (
                SELECT id FROM cases
                WHERE organization_id = current_setting('app.current_org_id', true)::uuid
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS state_transitions_org_isolation ON case_state_transitions")
    op.drop_index("ix_case_state_transitions_case_id", table_name="case_state_transitions")
    op.drop_table("case_state_transitions")
