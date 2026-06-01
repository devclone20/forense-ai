"""006 audit_log

Revision ID: 006
Revises: 005
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE audit_action AS ENUM (
            'case_created',
            'case_updated',
            'case_status_changed',
            'member_added',
            'member_removed'
        )
    """)

    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.Enum(
            "case_created", "case_updated", "case_status_changed",
            "member_added", "member_removed",
            name="audit_action"
        ), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("actor_display_name", sa.String(length=255), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("hmac_signature", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        # case_id is nullable: org-level events have no case
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_audit_log_organization_id", "audit_log", ["organization_id"])
    op.create_index("ix_audit_log_case_id", "audit_log", ["case_id"])
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])

    # RLS: each org sees only its own audit log
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_log FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY audit_log_org_isolation ON audit_log
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
    """)

    # CRITICAL: audit log is append-only — revoke destructive permissions from app_user
    op.execute("REVOKE UPDATE, DELETE ON audit_log FROM app_user")


def downgrade() -> None:
    op.execute("GRANT UPDATE, DELETE ON audit_log TO app_user")
    op.execute("DROP POLICY IF EXISTS audit_log_org_isolation ON audit_log")
    op.drop_index("ix_audit_log_occurred_at", table_name="audit_log")
    op.drop_index("ix_audit_log_case_id", table_name="audit_log")
    op.drop_index("ix_audit_log_organization_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.execute("DROP TYPE IF EXISTS audit_action")
