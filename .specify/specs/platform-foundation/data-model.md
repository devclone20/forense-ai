# Data Model: Platform Foundation

> Gerado por SPEC-DRIVEN em 2026-06-01
> Estende o data model de Case Management — não substitui.

---

## Extensão da Tabela `users` (Migração 009)

```sql
-- Adicionar campos de autenticação ao modelo User existente
ALTER TABLE users
  ADD COLUMN password_hash       TEXT,                        -- Argon2id hash
  ADD COLUMN mfa_secret          TEXT,                        -- Fernet-encrypted TOTP secret
  ADD COLUMN mfa_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN mfa_backup_codes    JSONB NOT NULL DEFAULT '[]', -- [{hash, used_at|null}]
  ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN locked_until        TIMESTAMPTZ,                 -- NULL = não bloqueada
  ADD COLUMN last_login_at       TIMESTAMPTZ,
  ADD COLUMN updated_at          TIMESTAMPTZ NOT NULL DEFAULT now();

-- Corrigir o enum global_role para incluir todos os papéis definidos na spec
-- (o modelo existente tem apenas admin/perito/viewer — expandir)
ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'investigador';
ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'supervisor';
ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'advogado';
ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'consultor';
-- 'viewer' é substituído por 'consultor' semanticamente; manter para retrocompatibilidade

CREATE INDEX idx_users_email_org ON users(organization_id, lower(email));
CREATE INDEX idx_users_locked    ON users(locked_until) WHERE locked_until IS NOT NULL;
```

---

## Extensão da Tabela `organizations` (Migração 013)

```sql
ALTER TABLE organizations
  ADD COLUMN invite_expiry_days  INTEGER NOT NULL DEFAULT 7
    CHECK (invite_expiry_days BETWEEN 1 AND 90);
```

---

## Nova Tabela: `invitations` (Migração 010)

```sql
CREATE TABLE invitations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  email           TEXT NOT NULL,
  role            global_role NOT NULL,
  token_hash      TEXT NOT NULL UNIQUE,        -- SHA-256 do token enviado por email
  invited_by      UUID NOT NULL REFERENCES users(id),
  expires_at      TIMESTAMPTZ NOT NULL,
  accepted_at     TIMESTAMPTZ,                 -- NULL = ainda não aceite
  revoked_at      TIMESTAMPTZ,                 -- NULL = não revogado
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_invitations_org_email ON invitations(organization_id, lower(email))
  WHERE accepted_at IS NULL AND revoked_at IS NULL;
CREATE INDEX idx_invitations_token     ON invitations(token_hash);

-- RLS: apenas admins da org vêem os convites da sua org
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY invitations_org_isolation ON invitations
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

**Notas:**
- `token_hash` — o token real nunca é guardado; apenas o seu SHA-256. Assim, um leak da BD não compromete convites activos.
- Um utilizador pode ter múltiplos convites pendentes se o Admin reenviar (os anteriores ficam como revogados implicitamente quando o novo é aceite).

---

## Nova Tabela: `refresh_tokens` (Migração 011)

```sql
CREATE TABLE refresh_tokens (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL,               -- desnormalizado para queries rápidas
  token_hash      TEXT NOT NULL UNIQUE,        -- SHA-256 do token opaco
  family_id       UUID NOT NULL,               -- grupo de tokens relacionados por rotation
  expires_at      TIMESTAMPTZ NOT NULL,
  revoked_at      TIMESTAMPTZ,
  replaced_by     UUID REFERENCES refresh_tokens(id),  -- chain de rotation
  ip_address      INET,
  user_agent      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rt_user        ON refresh_tokens(user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_rt_token_hash  ON refresh_tokens(token_hash);
CREATE INDEX idx_rt_family      ON refresh_tokens(family_id);
CREATE INDEX idx_rt_expires     ON refresh_tokens(expires_at) WHERE revoked_at IS NULL;
```

**Lógica de token rotation + detecção de roubo:**
```
1. Cliente apresenta refresh token R1
2. Backend verifica R1 na BD (válido, não revogado, não expirado)
3. Backend cria R2 com mesmo family_id; marca R1.replaced_by = R2.id e R1.revoked_at = now()
4. Backend devolve R2 ao cliente

Se alguém apresentar R1 novamente (já revogado):
  → Sinal de roubo → revogar TODOS os tokens da family_id imediatamente
  → Forçar re-autenticação
```

---

## Nova Tabela: `auth_log` (Migração 012)

```sql
CREATE TYPE auth_event AS ENUM (
  'login_success',
  'login_failed',
  'login_locked',
  'logout',
  'mfa_setup',
  'mfa_success',
  'mfa_failed',
  'mfa_backup_used',
  'mfa_backup_regenerated',
  'token_refreshed',
  'token_revoked_all',
  'invite_created',
  'invite_accepted',
  'invite_revoked',
  'password_changed',
  'recovery_requested',
  'recovery_completed',
  'user_suspended',
  'role_changed'
);

CREATE TABLE auth_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id),    -- nullable: eventos de IP sem user (falhanços)
  organization_id UUID,                         -- nullable: antes de saber a org
  event_type      auth_event NOT NULL,
  ip_address      INET,
  user_agent      TEXT,
  metadata        JSONB NOT NULL DEFAULT '{}',  -- dados específicos do evento
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Imutável: igual ao audit_log do Case Management
REVOKE UPDATE, DELETE ON auth_log FROM forense_app_user;

CREATE INDEX idx_auth_log_user    ON auth_log(user_id, occurred_at DESC);
CREATE INDEX idx_auth_log_org     ON auth_log(organization_id, occurred_at DESC);
CREATE INDEX idx_auth_log_event   ON auth_log(event_type, occurred_at DESC);
CREATE INDEX idx_auth_log_ip      ON auth_log(ip_address, occurred_at DESC);
```

---

## Fluxos de Autenticação

### Login Normal (não-admin ou admin com MFA já configurado)

```
POST /auth/login {email, password}
  → verificar password com Argon2
  → se 5+ falhanços: bloqueio temporário, log login_locked
  → se admin sem MFA: forçar setup (retornar mfa_setup_required: true)
  → se admin com MFA: emitir JWT provisório scope=mfa_pending (5 min)
                      retornar {requires_mfa: true, mfa_token: "..."}
  → se não-admin: emitir access_token + refresh_token → retornar

POST /auth/mfa/verify {mfa_token, totp_code}   (apenas admins)
  → verificar JWT provisório (scope=mfa_pending)
  → verificar TOTP code com pyotp
  → se inválido: log mfa_failed, incrementar contador
  → se válido: emitir access_token + refresh_token definitivos, log mfa_success
```

### Refresh Flow

```
POST /auth/refresh {refresh_token}
  → SELECT ... FOR UPDATE WHERE token_hash = hash(refresh_token) AND revoked_at IS NULL
  → se não existe: 401
  → se expirado: 401, revogar família
  → se já revogado: ROUBO DETECTADO → revogar família inteira → 401
  → criar novo token na mesma família, revogar o anterior
  → retornar novo access_token + novo refresh_token
```

### Convite Flow

```
POST /invites {email, role}                    (Admin)
  → gerar token = secrets.token_urlsafe(32)
  → guardar hash(token) na BD
  → enviar email com link: /invite/{token}
  → retornar convite criado

GET /invites/:token/validate                   (público)
  → verificar assinatura + BD
  → retornar {email, role, organization_name, valid: true/false}

POST /invites/:token/accept {display_name, password}
  → verificar token válido + não expirado + não revogado
  → criar User com Argon2(password)
  → marcar convite accepted_at = now()
  → log invite_accepted
  → retornar redirect para /login
```

---

## Papéis e Permissões — Referência Completa

| Papel | Criar Casos | Ver Casos | Gerir Equipa | Fechar Casos | Admin Org |
|---|---|---|---|---|---|
| `admin` | ✓ | todos | ✓ | ✓ | ✓ |
| `perito` | ✓ (owner) | os seus | ✓ (nos seus) | ✓ (owner) | — |
| `investigador` | — | atribuídos | — | — | — |
| `supervisor` | — | todos | — | — | — |
| `advogado` | — | autorizados | — | — | — |
| `consultor` | — | atribuídos | — | — | — |

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-06-01*
