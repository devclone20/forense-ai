# Data Model: Evidence Ingestion

> Gerado por SPEC-DRIVEN em 2026-06-02
> Migrações: 014 → 018 (a seguir às 013 do Platform Foundation)

---

## Resumo das Novas Tabelas

```
organizations (existente)
     │
     └──< storage_configs (1:1 — cada org tem um backend configurado)
     │
cases (existente)
     │
     ├──< evidences
     │         │
     │         └──< evidence_events (append-only — cada acesso registado)
     │
     └──< evidence_number_sequences (contador por caso)
```

---

## Migração 014 — `storage_configs`

```sql
CREATE TABLE storage_configs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL UNIQUE REFERENCES organizations(id),
  backend               TEXT NOT NULL
                          CHECK (backend IN ('local','s3','minio','r2','wasabi','replicated')),
  credentials_encrypted JSONB NOT NULL DEFAULT '{}',
  -- Fernet-encrypted. Conteúdo desencriptado varia por backend:
  -- local: {"base_path": "/data/evidences"}
  -- s3/r2/wasabi: {"bucket": "...", "region": "...", "access_key": "...", "secret_key": "..."}
  -- minio: {"endpoint_url": "...", "bucket": "...", "access_key": "...", "secret_key": "..."}
  -- replicated: {"primary": {...local...}, "replica": {...s3...}}
  max_file_bytes        BIGINT,          -- NULL = sem limite por ficheiro
  quota_bytes           BIGINT,          -- NULL = sem limite total
  used_bytes            BIGINT NOT NULL DEFAULT 0,
  quota_alert_sent_at   TIMESTAMPTZ,     -- NULL = alerta ainda não enviado
  configured_by         UUID NOT NULL REFERENCES users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Apenas admins da organização acedem à config de storage
ALTER TABLE storage_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY storage_configs_org ON storage_configs
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

---

## Migração 015 — `evidences`

```sql
CREATE TYPE evidence_type AS ENUM (
  -- Domínio Digital
  'ficheiro_sistema', 'imagem_disco', 'dump_memoria', 'log_sistema',
  'capture_rede', 'artefacto_browser', 'registo_so', 'email_mensagem',
  -- Domínio Médico-Legal
  'relatorio_medico', 'fotografia_forense', 'resultado_laboratorial',
  'registo_hospitalar', 'laudo_pericial',
  -- Domínio Financeiro
  'extrato_bancario', 'fatura_recibo', 'contrato',
  'registo_transacao', 'comunicacao_financeira', 'relatorio_contabilistico',
  -- Genérico (qualquer domínio)
  'outro'
);

CREATE TABLE evidences (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   UUID NOT NULL REFERENCES organizations(id),
  case_id           UUID NOT NULL REFERENCES cases(id),
  evidence_number   TEXT NOT NULL,           -- "EV-001", único por caso
  title             TEXT NOT NULL CHECK (length(trim(title)) > 0),
  description       TEXT,
  evidence_type     evidence_type NOT NULL,
  storage_ref       TEXT NOT NULL,           -- referência opaca → StorageProvider interpreta
  original_filename TEXT NOT NULL,
  size_bytes        BIGINT NOT NULL CHECK (size_bytes > 0),
  mime_type         TEXT NOT NULL,           -- detectado por python-magic, não pelo cliente
  sha256_hash       CHAR(64) NOT NULL,       -- hex lowercase, calculado no servidor
  source_origin     TEXT,
  collected_at      TIMESTAMPTZ,
  ingested_by       UUID NOT NULL REFERENCES users(id),
  ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  tags              TEXT[] NOT NULL DEFAULT '{}',
  domain_metadata   JSONB NOT NULL DEFAULT '{}',
  search_vector     TSVECTOR,
  UNIQUE(case_id, evidence_number)
);

-- RLS dupla: org isolation + acesso por membros do caso
ALTER TABLE evidences ENABLE ROW LEVEL SECURITY;

CREATE POLICY evidences_org_isolation ON evidences
  USING (organization_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY evidences_case_member ON evidences
  USING (
    EXISTS (
      SELECT 1 FROM cases c
      WHERE c.id = evidences.case_id
        AND (
          c.owner_id = current_setting('app.current_user_id')::uuid
          OR EXISTS (
            SELECT 1 FROM case_members cm
            WHERE cm.case_id = c.id
              AND cm.user_id = current_setting('app.current_user_id')::uuid
              AND cm.removed_at IS NULL
          )
        )
    )
  );

CREATE INDEX idx_evidences_case       ON evidences(case_id, ingested_at DESC);
CREATE INDEX idx_evidences_hash       ON evidences(sha256_hash);
CREATE INDEX idx_evidences_type       ON evidences(case_id, evidence_type);
CREATE INDEX idx_evidences_ingested   ON evidences(ingested_by);
CREATE INDEX idx_evidences_search     ON evidences USING GIN(search_vector);
CREATE INDEX idx_evidences_tags       ON evidences USING GIN(tags);
```

---

## Migração 016 — `evidence_events` (append-only)

```sql
CREATE TYPE evidence_event_type AS ENUM (
  'ingested',
  'viewed',
  'downloaded',
  'integrity_verified',
  'integrity_alert',      -- hash divergiu → adulteração detectada
  'chain_exported'
);

CREATE TABLE evidence_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,
  evidence_id     UUID NOT NULL REFERENCES evidences(id),
  event_type      evidence_event_type NOT NULL,
  actor_id        UUID REFERENCES users(id),     -- NULL para eventos de sistema
  actor_name      TEXT NOT NULL,                 -- snapshot no momento do evento
  ip_address      INET,
  metadata        JSONB NOT NULL DEFAULT '{}',
  -- Para integrity_verified: {"hash_stored": "...", "hash_computed": "...", "match": true/false}
  -- Para downloaded: {"download_filename": "EV-001_original.pdf"}
  -- Para chain_exported: {"format": "csv", "hmac": "..."}
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Fisicamente imutável
REVOKE UPDATE, DELETE ON evidence_events FROM forense_app_user;

CREATE INDEX idx_ev_events_evidence ON evidence_events(evidence_id, occurred_at DESC);
CREATE INDEX idx_ev_events_case     ON evidence_events(organization_id, occurred_at DESC);
CREATE INDEX idx_ev_events_actor    ON evidence_events(actor_id);
CREATE INDEX idx_ev_events_type     ON evidence_events(event_type, occurred_at DESC);
```

---

## Migração 017 — `evidence_number_sequences`

```sql
CREATE TABLE evidence_number_sequences (
  case_id   UUID NOT NULL REFERENCES cases(id) ON DELETE RESTRICT,
  counter   BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (case_id)
);

-- Incremento atómico (mesma técnica do case_number_sequences)
-- INSERT INTO evidence_number_sequences(case_id, counter)
-- VALUES (:case_id, 1)
-- ON CONFLICT (case_id)
-- DO UPDATE SET counter = evidence_number_sequences.counter + 1
-- RETURNING counter;
```

---

## Migração 018 — `evidence_search` (índices + trigger)

```sql
-- Trigger: manter search_vector actualizado automaticamente
CREATE FUNCTION update_evidence_search_vector() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('portuguese', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('portuguese', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('simple', NEW.evidence_number), 'A') ||
    setweight(to_tsvector('simple', NEW.original_filename), 'B') ||
    setweight(to_tsvector('simple', array_to_string(NEW.tags, ' ')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evidence_search
  BEFORE INSERT OR UPDATE OF title, description, evidence_number, original_filename, tags
  ON evidences
  FOR EACH ROW EXECUTE FUNCTION update_evidence_search_vector();

-- Trigger: actualizar used_bytes na storage_config quando evidência é ingerida
CREATE FUNCTION update_storage_quota() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE storage_configs
    SET used_bytes = used_bytes + NEW.size_bytes,
        updated_at = now()
    WHERE organization_id = NEW.organization_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_storage_quota
  AFTER INSERT ON evidences
  FOR EACH ROW EXECUTE FUNCTION update_storage_quota();
```

---

## Metadata de Domínio — Estrutura JSONB por Tipo

### Digital
```json
{
  "device_id": "string",
  "acquisition_tool": "FTK Imager 4.7",
  "acquisition_hash": "sha256:...",
  "filesystem": "NTFS",
  "os_detected": "Windows 11"
}
```

### Médico-Legal
```json
{
  "patient_id_anonymized": "PT-001",
  "medical_institution": "Hospital X",
  "exam_type": "Autópsia",
  "physician": "Dr. Silva",
  "case_reference_external": "123/2026"
}
```

### Financeiro
```json
{
  "institution": "Banco Y",
  "account_reference_anonymized": "ACC-001",
  "period_start": "2026-01-01",
  "period_end": "2026-03-31",
  "currency": "EUR",
  "transaction_count": 847
}
```

---

## StorageRef — Formato por Backend

| Backend | Formato da `storage_ref` |
|---|---|
| `local` | `local://org-uuid/case-uuid/ev-uuid/original_filename.ext` |
| `s3` / `r2` / `wasabi` | `s3://bucket-name/org-uuid/case-uuid/ev-uuid` |
| `minio` | `minio://bucket-name/org-uuid/case-uuid/ev-uuid` |
| `replicated` | `replicated://local:...|s3:...` |

A `storage_ref` é guardada na BD mas **nunca exposta** ao frontend ou ao utilizador.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-06-02*
