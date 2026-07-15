"""008 indexes triggers

Revision ID: 008
Revises: 007
Create Date: 2026-06-01
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GIN index for full-text search on cases
    op.execute("CREATE INDEX ix_cases_search_vector ON cases USING GIN (search_vector)")

    # GIN index for JSONB domain_metadata queries
    op.execute("CREATE INDEX ix_cases_domain_metadata ON cases USING GIN (domain_metadata)")

    # GIN index for tags array
    op.execute("CREATE INDEX ix_cases_tags ON cases USING GIN (tags)")

    # B-tree indexes for common filters
    op.execute("CREATE INDEX ix_cases_org_status ON cases (organization_id, status)")
    op.execute("CREATE INDEX ix_cases_org_domain ON cases (organization_id, forensic_domain)")
    op.execute("CREATE INDEX ix_cases_owner_id ON cases (owner_id)")
    op.execute("CREATE INDEX ix_cases_created_at ON cases (created_at DESC)")

    # Trigger: auto-update search_vector on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION cases_search_vector_trigger()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('portuguese', coalesce(NEW.case_number, '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER cases_search_vector_update
        BEFORE INSERT OR UPDATE OF title, description, case_number
        ON cases
        FOR EACH ROW EXECUTE FUNCTION cases_search_vector_trigger();
    """)

    # Trigger: auto-set updated_at on cases update
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
            NEW.updated_at := now();
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER cases_set_updated_at
        BEFORE UPDATE ON cases
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # Trigger: prevent UPDATE/DELETE on audit_log at DB level (belt+suspenders)
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_log_immutable()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is immutable — updates and deletes are forbidden';
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER audit_log_prevent_mutate
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_prevent_mutate ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_immutable()")
    op.execute("DROP TRIGGER IF EXISTS cases_set_updated_at ON cases")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
    op.execute("DROP TRIGGER IF EXISTS cases_search_vector_update ON cases")
    op.execute("DROP FUNCTION IF EXISTS cases_search_vector_trigger()")
    op.execute("DROP INDEX IF EXISTS ix_cases_created_at")
    op.execute("DROP INDEX IF EXISTS ix_cases_owner_id")
    op.execute("DROP INDEX IF EXISTS ix_cases_org_domain")
    op.execute("DROP INDEX IF EXISTS ix_cases_org_status")
    op.execute("DROP INDEX IF EXISTS ix_cases_tags")
    op.execute("DROP INDEX IF EXISTS ix_cases_domain_metadata")
    op.execute("DROP INDEX IF EXISTS ix_cases_search_vector")
