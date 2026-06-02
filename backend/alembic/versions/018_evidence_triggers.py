"""Evidence triggers: search_vector + storage quota

Revision ID: 018
Revises: 017
Create Date: 2026-06-02
"""

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
        -- ── Extend audit_action enum ──────────────────────────────────────────
        ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'evidence_added';

        -- ── Search vector trigger ──────────────────────────────────────────────
        CREATE OR REPLACE FUNCTION update_evidence_search_vector()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('portuguese', coalesce(NEW.title, '')),           'A') ||
                setweight(to_tsvector('portuguese', coalesce(NEW.description, '')),     'B') ||
                setweight(to_tsvector('simple',     NEW.evidence_number),               'A') ||
                setweight(to_tsvector('simple',     NEW.original_filename),             'B') ||
                setweight(to_tsvector('simple',     array_to_string(NEW.tags, ' ')),    'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_evidence_search
            BEFORE INSERT OR UPDATE OF
                title, description, evidence_number, original_filename, tags
            ON evidences
            FOR EACH ROW
            EXECUTE FUNCTION update_evidence_search_vector();

        -- ── Storage quota trigger ──────────────────────────────────────────────
        CREATE OR REPLACE FUNCTION update_storage_quota()
        RETURNS trigger AS $$
        BEGIN
            UPDATE storage_configs
            SET
                used_bytes = used_bytes + NEW.size_bytes,
                updated_at = now()
            WHERE organization_id = NEW.organization_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_storage_quota
            AFTER INSERT ON evidences
            FOR EACH ROW
            EXECUTE FUNCTION update_storage_quota();
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS trg_storage_quota     ON evidences;
        DROP TRIGGER IF EXISTS trg_evidence_search   ON evidences;
        DROP FUNCTION IF EXISTS update_storage_quota();
        DROP FUNCTION IF EXISTS update_evidence_search_vector();
    """)
