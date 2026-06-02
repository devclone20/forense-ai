"""evidence_number_sequences table

Revision ID: 017
Revises: 016
Create Date: 2026-06-02
"""

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TABLE evidence_number_sequences (
            case_id  UUID   NOT NULL REFERENCES cases(id) PRIMARY KEY,
            counter  BIGINT NOT NULL DEFAULT 0
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS evidence_number_sequences;")
