"""storage_configs table

Revision ID: 014
Revises: 013
Create Date: 2026-06-02
"""

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TABLE storage_configs (
            id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id      UUID         NOT NULL UNIQUE REFERENCES organizations(id),
            backend              TEXT         NOT NULL
                                             CHECK (backend IN (
                                                 'local','s3','minio','r2','wasabi','replicated'
                                             )),
            credentials_encrypted JSONB       NOT NULL DEFAULT '{}',
            max_file_bytes       BIGINT,
            quota_bytes          BIGINT,
            used_bytes           BIGINT       NOT NULL DEFAULT 0,
            quota_alert_sent_at  TIMESTAMPTZ,
            configured_by        UUID         NOT NULL REFERENCES users(id),
            created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
        );

        ALTER TABLE storage_configs ENABLE ROW LEVEL SECURITY;

        CREATE POLICY storage_configs_org ON storage_configs
            USING (
                organization_id = current_setting('app.current_org_id')::uuid
            );
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS storage_configs_org ON storage_configs;
        DROP TABLE IF EXISTS storage_configs;
    """)
