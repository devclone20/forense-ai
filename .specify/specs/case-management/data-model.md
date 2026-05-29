# Data Model: Case Management

> Gerado por SPEC-DRIVEN em 2026-05-29
> Base de Dados: PostgreSQL
> Multi-tenancy: Row Level Security (RLS)

---

## Diagrama de Entidades

```
organizations
     │
     ├──< users (via org_members)
     │
     ├──< cases
     │         │
     │         ├──< case_members (users com papel no caso)
     │         ├──< case_state_transitions
     │         └──< audit_log (append-only)
     │
     └──< case_number_sequences
```

---

## Tabelas

### `organizations`

```sql
CREATE TABLE organizations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                  TEXT NOT NULL,
  slug                  TEXT NOT NULL UNIQUE,             -- URL-safe identifier
  number_format         TEXT NOT NULL DEFAULT 'FOR-{YYYY}-{NNNNN}',
  number_prefix         TEXT,                             -- prefixo opcional (ex: "LISBOA")
  number_counter        BIGINT NOT NULL DEFAULT 0,        -- contador atómico
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active             BOOLEAN NOT NULL DEFAULT true
);
```

**Notas:**
- `number_format` define o template de numeração. Tokens suportados: `{YYYY}`, `{MM}`, `{NNNNN}`, `{PREFIX}`.
- `number_counter` é incrementado atomicamente via `SELECT ... FOR UPDATE`.
- Não tem RLS — apenas Admins globais acedem directamente.

---

### `users`

```sql
CREATE TABLE users (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL REFERENCES organizations(id),
  email                 TEXT NOT NULL,
  display_name          TEXT NOT NULL,
  global_role           TEXT NOT NULL CHECK (global_role IN (
                          'admin', 'perito', 'investigador', 'supervisor', 'advogado'
                        )),
  is_active             BOOLEAN NOT NULL DEFAULT true,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(organization_id, email)
);

-- RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_org_isolation ON users
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

**Notas:**
- `global_role` é o papel na plataforma. O papel num caso específico é definido em `case_members`.
- Email é único por organização, não globalmente — diferentes organizações podem ter o mesmo email (emails corporativos repetidos).

---

### `cases`

```sql
CREATE TYPE forensic_domain AS ENUM ('digital', 'medico_legal', 'financeiro');
CREATE TYPE case_status AS ENUM (
  'aberto', 'em_investigacao', 'em_revisao', 'fechado', 'arquivado'
);
CREATE TYPE confidentiality_level AS ENUM (
  'normal', 'reservado', 'confidencial', 'secreto'
);

CREATE TABLE cases (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL REFERENCES organizations(id),
  case_number           TEXT NOT NULL,                    -- "FOR-2026-00001"
  title                 TEXT NOT NULL CHECK (length(trim(title)) > 0),
  description           TEXT,
  forensic_domain       forensic_domain NOT NULL,
  status                case_status NOT NULL DEFAULT 'aberto',
  confidentiality       confidentiality_level NOT NULL DEFAULT 'normal',
  owner_id              UUID NOT NULL REFERENCES users(id),
  tags                  TEXT[] NOT NULL DEFAULT '{}',
  domain_metadata       JSONB NOT NULL DEFAULT '{}',      -- campos por domínio
  search_vector         TSVECTOR,                         -- full-text search
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at             TIMESTAMPTZ,
  archived_at           TIMESTAMPTZ,
  UNIQUE(organization_id, case_number)                    -- número único por org
);

-- Índices
CREATE INDEX idx_cases_org_status    ON cases(organization_id, status);
CREATE INDEX idx_cases_org_domain    ON cases(organization_id, forensic_domain);
CREATE INDEX idx_cases_owner         ON cases(owner_id);
CREATE INDEX idx_cases_created_at    ON cases(created_at DESC);
CREATE INDEX idx_cases_search        ON cases USING GIN(search_vector);
CREATE INDEX idx_cases_tags          ON cases USING GIN(tags);

-- Full-text search trigger
CREATE FUNCTION update_case_search_vector() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('portuguese', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('portuguese', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('simple', NEW.case_number), 'A') ||
    setweight(to_tsvector('simple', array_to_string(NEW.tags, ' ')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cases_search
  BEFORE INSERT OR UPDATE OF title, description, case_number, tags ON cases
  FOR EACH ROW EXECUTE FUNCTION update_case_search_vector();

-- RLS
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

CREATE POLICY cases_org_isolation ON cases
  USING (organization_id = current_setting('app.current_org_id')::uuid);

-- Política adicional: utilizadores só veem casos onde são membros OU são owner
CREATE POLICY cases_member_access ON cases
  USING (
    owner_id = current_setting('app.current_user_id')::uuid
    OR EXISTS (
      SELECT 1 FROM case_members cm
      WHERE cm.case_id = cases.id
        AND cm.user_id = current_setting('app.current_user_id')::uuid
        AND cm.removed_at IS NULL
    )
  );
```

**Notas:**
- `domain_metadata` em JSONB permite campos específicos por domínio sem migrações (ex: `{"processo_tribunal": "123/2026"}` para médico-legal).
- `search_vector` é mantido por trigger — a search é sempre actualizada automaticamente.
- Full-text search em Português (`'portuguese'`) para stemming correcto.
- Dois níveis de RLS: isolamento por organização + visibilidade por membro.

---

### `case_members`

```sql
CREATE TYPE case_role AS ENUM (
  'responsavel', 'investigador', 'supervisor', 'consultor'
);

CREATE TABLE case_members (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id               UUID NOT NULL REFERENCES cases(id),
  user_id               UUID NOT NULL REFERENCES users(id),
  role                  case_role NOT NULL,
  assigned_by           UUID NOT NULL REFERENCES users(id),
  assigned_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  removed_at            TIMESTAMPTZ,                      -- NULL = membro activo
  removed_by            UUID REFERENCES users(id),
  UNIQUE(case_id, user_id, removed_at)                    -- um utilizador activo por caso
);

CREATE INDEX idx_case_members_case     ON case_members(case_id) WHERE removed_at IS NULL;
CREATE INDEX idx_case_members_user     ON case_members(user_id) WHERE removed_at IS NULL;

-- RLS (herdado do contexto de org via JOIN com cases)
ALTER TABLE case_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY case_members_org_isolation ON case_members
  USING (
    EXISTS (
      SELECT 1 FROM cases c
      WHERE c.id = case_members.case_id
        AND c.organization_id = current_setting('app.current_org_id')::uuid
    )
  );
```

**Notas:**
- Remoção é soft-delete (`removed_at`) — histórico de participação preservado (requisito da spec).
- `UNIQUE(case_id, user_id, removed_at)` com `removed_at IS NULL` garante que um utilizador só tem um papel activo por caso.

---

### `case_state_transitions`

```sql
CREATE TABLE case_state_transitions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id               UUID NOT NULL REFERENCES cases(id),
  from_status           case_status NOT NULL,
  to_status             case_status NOT NULL,
  transitioned_by       UUID NOT NULL REFERENCES users(id),
  justification         TEXT,                             -- obrigatório em backward transitions
  transitioned_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_transitions_case ON case_state_transitions(case_id, transitioned_at DESC);
```

**Notas:**
- Esta tabela é o histórico completo de estados — não apenas o estado actual (que está em `cases.status`).
- `justification` é obrigatório no código de aplicação para backward transitions. A validação não está na BD para manter o schema simples, mas está no `CaseService`.

---

### `audit_log`

```sql
CREATE TYPE audit_action AS ENUM (
  'case_created',
  'case_updated',
  'case_status_changed',
  'member_added',
  'member_removed',
  'evidence_added',          -- escrito por evidence-ingestion module
  'analysis_started',        -- escrito por ai-analysis module
  'report_generated'         -- escrito por report-generator module
);

CREATE TABLE audit_log (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL,                    -- sem FK para não bloquear deleção de orgs
  case_id               UUID NOT NULL,
  action                audit_action NOT NULL,
  actor_id              UUID NOT NULL,
  actor_display_name    TEXT NOT NULL,                    -- snapshot — não muda se user mudar nome
  metadata              JSONB NOT NULL DEFAULT '{}',      -- dados específicos da acção
  occurred_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address            INET                              -- para auditoria de segurança
);

-- Sem UPDATE nem DELETE — garantido por permissões
-- O app user não tem GRANT UPDATE, DELETE ON audit_log
REVOKE UPDATE, DELETE ON audit_log FROM forense_app_user;

CREATE INDEX idx_audit_case        ON audit_log(case_id, occurred_at DESC);
CREATE INDEX idx_audit_org         ON audit_log(organization_id, occurred_at DESC);
CREATE INDEX idx_audit_actor       ON audit_log(actor_id);

-- Trigger: auto-log em alterações de cases
CREATE FUNCTION log_case_change() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log(organization_id, case_id, action, actor_id, actor_display_name, metadata)
    VALUES (
      NEW.organization_id,
      NEW.id,
      'case_created',
      current_setting('app.current_user_id')::uuid,
      current_setting('app.current_user_name'),
      jsonb_build_object('case_number', NEW.case_number, 'title', NEW.title, 'domain', NEW.forensic_domain)
    );
  ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
    INSERT INTO audit_log(organization_id, case_id, action, actor_id, actor_display_name, metadata)
    VALUES (
      NEW.organization_id,
      NEW.id,
      'case_status_changed',
      current_setting('app.current_user_id')::uuid,
      current_setting('app.current_user_name'),
      jsonb_build_object('from', OLD.status, 'to', NEW.status)
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_cases
  AFTER INSERT OR UPDATE ON cases
  FOR EACH ROW EXECUTE FUNCTION log_case_change();
```

**Notas:**
- `actor_display_name` é um snapshot no momento da acção — o log mantém o nome correcto mesmo se o utilizador o mudar depois.
- `REVOKE UPDATE, DELETE` garante imutabilidade ao nível do motor de BD, não apenas por convenção de código.
- A tabela aceita acções de outros módulos futuros (`evidence_added`, `analysis_started`, `report_generated`) — é o log central da plataforma.

---

### `case_number_sequences`

```sql
CREATE TABLE case_number_sequences (
  organization_id       UUID NOT NULL REFERENCES organizations(id),
  year                  INTEGER NOT NULL,
  counter               BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (organization_id, year)
);
```

**Lógica de geração de número:**

```sql
-- Atómico: incrementa e retorna o novo valor em uma operação
INSERT INTO case_number_sequences(organization_id, year, counter)
VALUES (:org_id, :year, 1)
ON CONFLICT (organization_id, year)
DO UPDATE SET counter = case_number_sequences.counter + 1
RETURNING counter;
```

**Notas:**
- Sequência separada por organização + ano — o counter reinicia a cada ano (2026-00001, 2027-00001).
- `ON CONFLICT ... DO UPDATE` é atómico — sem race conditions em criações simultâneas.

---

## Transições de Estado Permitidas

```
                    ┌─────────────────────────────┐
                    ↓                             │ (justificação obrigatória)
Aberto → Em Investigação → Em Revisão → Fechado → Em Investigação
                                           │
                                           ↓
                                       Arquivado

Backward transitions permitidas (com justificação):
  Em Investigação → Aberto
  Em Revisão → Em Investigação
  Fechado → Em Investigação
  Arquivado → Fechado (apenas Administrador)
```

---

## Papéis e Permissões por Acção

| Acção | Admin | Perito (owner) | Investigador | Supervisor | Consultor |
|---|---|---|---|---|---|
| Criar caso | ✓ | ✓ | — | — | — |
| Ver caso | ✓ | ✓ | ✓ | ✓ | ✓ |
| Editar título/descrição | ✓ | ✓ | — | — | — |
| Transição de estado | ✓ | ✓ | — | — | — |
| Atribuir membros | ✓ | ✓ | — | — | — |
| Remover membros | ✓ | ✓ | — | — | — |
| Ver log de actividade | ✓ | ✓ | ✓ | ✓ | ✓ |
| Exportar log | ✓ | ✓ | — | ✓ | — |
| Desarquivar caso | ✓ | — | — | — | — |

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-05-29*
