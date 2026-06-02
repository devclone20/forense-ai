"""evidence_events table (append-only chain of custody)

Revision ID: 016
Revises: 015
Create Date: 2026-06-02
"""

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TYPE evidence_event_type AS ENUM (
            'ingested',
            'viewed',
            'downloaded',
            'integrity_verified',
            'integrity_alert',
            'chain_exported'
        );

        CREATE TABLE evidence_events (
            id              UUID                 PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID                 NOT NULL,
            evidence_id     UUID                 NOT NULL REFERENCES evidences(id),
            event_type      evidence_event_type  NOT NULL,
            actor_id        UUID                 REFERENCES users(id),
            actor_name      TEXT                 NOT NULL,
            ip_address      INET,
            metadata        JSONB                NOT NULL DEFAULT '{}',
            occurred_at     TIMESTAMPTZ          NOT NULL DEFAULT now()
        );

        -- Append-only enforcement at the DB level
        REVOKE UPDATE, DELETE ON evidence_events FROM forense_app_user;

        CREATE INDEX idx_ev_events_evidence_id  ON evidence_events (evidence_id);
        CREATE INDEX idx_ev_events_occurred_at  ON evidence_events (occurred_at DESC);
        CREATE INDEX idx_ev_events_event_type   ON evidence_events (event_type);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS evidence_events;
        DROP TYPE IF EXISTS evidence_event_type;
    """)
