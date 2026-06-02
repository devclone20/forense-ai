"""evidences table

Revision ID: 015
Revises: 014
Create Date: 2026-06-02
"""

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TYPE evidence_type AS ENUM (
            'ficheiro_sistema',
            'imagem_disco',
            'dump_memoria',
            'log_sistema',
            'capture_rede',
            'artefacto_browser',
            'registo_so',
            'email_mensagem',
            'relatorio_medico',
            'fotografia_forense',
            'resultado_laboratorial',
            'registo_hospitalar',
            'laudo_pericial',
            'extrato_bancario',
            'fatura_recibo',
            'contrato',
            'registo_transacao',
            'comunicacao_financeira',
            'relatorio_contabilistico',
            'outro'
        );

        CREATE TABLE evidences (
            id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id   UUID         NOT NULL REFERENCES organizations(id),
            case_id           UUID         NOT NULL REFERENCES cases(id),
            evidence_number   TEXT         NOT NULL,
            title             TEXT         NOT NULL CHECK (length(trim(title)) > 0),
            description       TEXT,
            evidence_type     evidence_type NOT NULL,
            storage_ref       TEXT         NOT NULL,
            original_filename TEXT         NOT NULL,
            size_bytes        BIGINT       NOT NULL CHECK (size_bytes > 0),
            mime_type         TEXT         NOT NULL,
            sha256_hash       CHAR(64)     NOT NULL,
            source_origin     TEXT,
            collected_at      TIMESTAMPTZ,
            ingested_by       UUID         NOT NULL REFERENCES users(id),
            ingested_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
            tags              TEXT[]       NOT NULL DEFAULT '{}',
            domain_metadata   JSONB        NOT NULL DEFAULT '{}',
            search_vector     TSVECTOR,
            UNIQUE (case_id, evidence_number)
        );

        ALTER TABLE evidences ENABLE ROW LEVEL SECURITY;

        CREATE POLICY evidences_org ON evidences
            USING (
                organization_id = current_setting('app.current_org_id')::uuid
            );

        -- Performance indexes
        CREATE INDEX idx_evidences_case_id        ON evidences (case_id);
        CREATE INDEX idx_evidences_sha256          ON evidences (sha256_hash);
        CREATE INDEX idx_evidences_type            ON evidences (evidence_type);
        CREATE INDEX idx_evidences_search          ON evidences USING GIN (search_vector);
        CREATE INDEX idx_evidences_tags            ON evidences USING GIN (tags);
        CREATE INDEX idx_evidences_ingested_at     ON evidences (ingested_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS evidences_org ON evidences;
        DROP TABLE IF EXISTS evidences;
        DROP TYPE IF EXISTS evidence_type;
    """)
