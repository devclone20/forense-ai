"""003 cases

Revision ID: 003
Revises: 002
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE forensic_domain AS ENUM ('digital', 'medico_legal', 'financeiro')")
    op.execute("CREATE TYPE case_status AS ENUM ('aberto', 'em_investigacao', 'em_revisao', 'fechado', 'arquivado')")
    op.execute("CREATE TYPE confidentiality_level AS ENUM ('normal', 'reservado', 'confidencial', 'secreto')")

    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("case_number", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("forensic_domain", sa.Enum("digital", "medico_legal", "financeiro", name="forensic_domain"), nullable=False),
        sa.Column("status", sa.Enum("aberto", "em_investigacao", "em_revisao", "fechado", "arquivado", name="case_status"), nullable=False, server_default="aberto"),
        sa.Column("confidentiality", sa.Enum("normal", "reservado", "confidencial", "secreto", name="confidentiality_level"), nullable=False, server_default="normal"),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.Text()), nullable=False, server_default="'{}'"),
        sa.Column("domain_metadata", JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("search_vector", TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "case_number", name="uq_cases_org_number"),
    )

    op.execute("ALTER TABLE cases ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cases FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY cases_org_isolation ON cases
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS cases_org_isolation ON cases")
    op.drop_table("cases")
    op.execute("DROP TYPE IF EXISTS confidentiality_level")
    op.execute("DROP TYPE IF EXISTS case_status")
    op.execute("DROP TYPE IF EXISTS forensic_domain")
