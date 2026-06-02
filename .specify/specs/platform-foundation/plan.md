# Plan: Platform Foundation

> Gerado por SPEC-DRIVEN em 2026-06-01
> Baseia-se em: `.specify/specs/platform-foundation/spec.md`
> Integra com: Case Management (RLS middleware + `deps.py` já escritos)
> Decisões técnicas aprovadas pelo fundador em 2026-06-01

---

## Contexto de Integração

O Case Management já tem o `deps.py` e `middleware/tenant.py` escritos à espera do JWT correcto:

```python
# deps.py — já existe, espera JWT com:
claims["sub"]          # → user_id (UUID)
claims["org_id"]       # → organization_id (UUID)  ← alimenta RLS
claims["email"]
claims["display_name"]
claims["role"]         # → global_role
```

O Platform Foundation é a peça que **emite** este JWT. Quando esta feature estiver pronta, o Case Management funciona end-to-end sem tocar em mais nada.

O modelo `User` já existe com `password_hash`. Faltam os campos: `mfa_secret`, `mfa_enabled`, `mfa_backup_codes`, `failed_login_attempts`, `locked_until`, `last_login_at`, `updated_at`.

---

## Stack Decision

Tudo dentro do stack já aprovado — sem novas dependências de runtime, apenas bibliotecas de segurança:

| Biblioteca | Para quê | Alternativa considerada |
|---|---|---|
| **Argon2** (`argon2-cffi`) | Hashing de passwords | bcrypt — Argon2 é o vencedor do Password Hashing Competition 2015, superior em resistência a GPU attacks |
| **python-jose** | JWT encode/decode | já em uso no deps.py |
| **pyotp** | TOTP (Google Authenticator) | passlib TOTP — pyotp é mais focado e mantido |
| **qrcode** | Gerar QR code para TOTP setup | — |
| **itsdangerous** | Tokens assinados para convites + recovery | JWT para estes casos seria over-engineering |

Frontend: nenhuma nova biblioteca. shadcn/ui já tem os primitivos necessários (Dialog, Form, Input, Label).

---

## Arquitectura

```
                       Frontend (Next.js)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         /auth/*         /account/*      /admin/users/*
    (login, register,   (perfil, MFA)   (convites, gestão)
     refresh, recovery)
              │
┌─────────────▼──────────────────────────────────────────┐
│                  FastAPI Backend                         │
│                                                          │
│  AuthService          InviteService     AdminService     │
│  ├ login()            ├ create()        ├ list_users()   │
│  ├ refresh()          ├ accept()        ├ change_role()  │
│  ├ logout()           └ revoke()        └ suspend()      │
│  ├ setup_mfa()                                           │
│  ├ verify_mfa()        TokenService                      │
│  └ recover_password()  ├ issue_access()                  │
│                        ├ issue_refresh()                 │
│                        └ revoke_all_for_user()           │
│                                                          │
│  ──────────── já existente (não tocar) ────────────────  │
│  RLS Middleware  │  deps.py  │  Case Management API      │
└──────────────────────────────────────────────────────────┘
              │
┌─────────────▼──────────────────────────────────────────┐
│                    PostgreSQL                             │
│  users (extend)  invitations  refresh_tokens  auth_log  │
└──────────────────────────────────────────────────────────┘
```

---

## Decisões Técnicas

### 1. Argon2 para passwords, nunca bcrypt

Argon2id é o standard actual. Parâmetros: `time_cost=2`, `memory_cost=65536` (64MB), `parallelism=1`. Resistente a ataques de GPU e ASIC — crítico em dados forenses.

### 2. JWT access token curto (15 min) + Refresh token longo com rotation

- **Access token:** 15 minutos. Assinado com `HS256` usando `SECRET_KEY`. Contém `sub`, `org_id`, `email`, `display_name`, `role`, `exp`.
- **Refresh token:** UUID opaco, guardado na BD com hash. Validade: 30 dias. **Rotation:** cada uso emite novo refresh token e invalida o anterior. Se um refresh token revogado for usado → revogação imediata de toda a família de tokens desse utilizador (detecção de roubo de token).
- **MFA token provisório:** após login com password, antes do TOTP — válido 5 minutos, scope `mfa_pending`. Não dá acesso a nenhum endpoint que não seja `/auth/mfa/verify`.

### 3. Convites com `itsdangerous.URLSafeTimedSerializer`

Token HMAC assinado contendo `{email, org_id, role, invite_id}`. Não precisa de lookup na BD para validar — a assinatura garante integridade. Mas o `invite_id` é verificado na BD para suportar revogação explícita.

### 4. Rate limiting em endpoints de autenticação

5 tentativas por IP por minuto em `/auth/login` e `/auth/recovery`. Implementado via middleware simples em memória (ou Redis se disponível). Bloqueio de conta ao 5.º falhanço consecutivo (independente de IP).

### 5. MFA TOTP + 8 backup codes

- TOTP standard RFC 6238 (30 segundos, 6 dígitos, SHA-1 — compatível com todos os autenticadores)
- Backup codes: 8 strings de 10 caracteres alfanuméricos, guardadas com Argon2 (não em texto claro). Uso de um código: marca como `used_at`, nunca reutilizável.
- Regeneração de backup codes: invalida todos os anteriores, emite 8 novos — registado em `auth_log`.

---

## Componentes a Criar

### Backend — Novas Migrações

| Migração | O que faz |
|---|---|
| `009_extend_users_auth.py` | Adiciona `mfa_secret` (encriptado), `mfa_enabled`, `mfa_backup_codes` (JSONB), `failed_login_attempts`, `locked_until`, `last_login_at`, `updated_at` |
| `010_invitations.py` | Tabela `invitations`: id, org_id, email, role, token_hash, invited_by, expires_at, accepted_at, revoked_at |
| `011_refresh_tokens.py` | Tabela `refresh_tokens`: id, user_id, token_hash, family_id, expires_at, revoked_at, replaced_by |
| `012_auth_log.py` | Tabela `auth_log`: id, user_id (nullable), org_id (nullable), event_type, ip, user_agent, metadata JSONB, occurred_at |
| `013_extend_organizations_invite.py` | Adiciona `invite_expiry_days` (default 7) à tabela `organizations` |

### Backend — Novos Ficheiros

| Ficheiro | Responsabilidade |
|---|---|
| `app/domain/password.py` | Argon2 hash + verify (zero I/O) |
| `app/domain/totp.py` | TOTP secret generation, QR URI, verify code, backup codes (zero I/O) |
| `app/domain/tokens.py` | JWT issue/decode, refresh token generation (zero I/O) |
| `app/repositories/auth_repository.py` | invite CRUD, refresh token CRUD, auth_log append |
| `app/services/auth_service.py` | login, refresh, logout, setup_mfa, verify_mfa, use_backup_code |
| `app/services/invite_service.py` | create_invite, accept_invite, revoke_invite |
| `app/services/admin_service.py` | list_users, change_role, suspend_user (+ revoke tokens) |
| `app/services/recovery_service.py` | request_recovery, confirm_recovery |
| `app/api/v1/auth.py` | POST /auth/login, POST /auth/refresh, POST /auth/logout, POST /auth/mfa/setup, POST /auth/mfa/verify, POST /auth/recovery/request, POST /auth/recovery/confirm |
| `app/api/v1/invites.py` | POST /invites, DELETE /invites/:id, POST /invites/:token/accept |
| `app/api/v1/account.py` | GET/PATCH /account/me, POST /account/password, GET /account/mfa/setup, POST /account/mfa/enable, POST /account/mfa/backup-codes/regenerate |
| `app/api/v1/admin_users.py` | GET /admin/users, PATCH /admin/users/:id/role, POST /admin/users/:id/suspend |
| `app/schemas/auth.py` | LoginRequest, TokenResponse, MFASetupResponse, RefreshRequest, etc. |
| `app/middleware/rate_limit.py` | Middleware de rate limiting para endpoints de auth |

### Frontend — Novas Páginas e Componentes

| Ficheiro | Responsabilidade |
|---|---|
| `app/(auth)/login/page.tsx` | Login form — email + password, depois MFA se admin |
| `app/(auth)/login/mfa/page.tsx` | Segundo passo: TOTP code ou backup code |
| `app/(auth)/invite/[token]/page.tsx` | Aceitação de convite + definição de password |
| `app/(auth)/recovery/page.tsx` | Pedido de recuperação de password |
| `app/(auth)/recovery/[token]/page.tsx` | Definição de nova password |
| `app/(dashboard)/account/page.tsx` | Perfil: nome, password, MFA setup/estado |
| `app/(dashboard)/admin/users/page.tsx` | Gestão de utilizadores + convites pendentes |
| `components/auth/LoginForm.tsx` | Form de login com validação |
| `components/auth/MFAForm.tsx` | Input de 6 dígitos com auto-focus |
| `components/auth/MFASetup.tsx` | QR code + backup codes display |
| `components/admin/InviteModal.tsx` | Modal de convite: email + papel |
| `components/admin/UserTable.tsx` | Tabela de utilizadores com acções |
| `lib/auth.ts` | Token storage (httpOnly cookie strategy), refresh logic |

---

## Sequência de Implementação

### Fase 0 — Migrações + Domínio (bloqueante)
1. Migrações 009-013
2. `domain/password.py` — Argon2 (com testes unitários)
3. `domain/totp.py` — TOTP + backup codes (com testes unitários)
4. `domain/tokens.py` — JWT + refresh token (com testes unitários)

### Fase 1 — Auth Core [P com Fase 2]
5. `repositories/auth_repository.py`
6. `services/auth_service.py` — login + MFA flow completo
7. `services/invite_service.py`
8. `api/v1/auth.py` + `api/v1/invites.py`

### Fase 2 — Frontend Auth [P com Fase 1]
9. Layout `(auth)` — páginas de autenticação separadas do dashboard
10. `LoginForm.tsx` + `MFAForm.tsx`
11. `app/(auth)/login/page.tsx` + `/mfa/page.tsx`
12. `lib/auth.ts` — token storage + auto-refresh

### Fase 3 — Account + Admin
13. `services/admin_service.py` + `api/v1/admin_users.py`
14. `api/v1/account.py` + MFA setup flow
15. `components/auth/MFASetup.tsx` — QR code + backup codes UI
16. `app/(dashboard)/account/page.tsx`
17. `app/(dashboard)/admin/users/page.tsx` + `UserTable.tsx` + `InviteModal.tsx`

### Fase 4 — Recovery + Rate Limiting
18. `services/recovery_service.py` + recovery endpoints
19. `middleware/rate_limit.py`
20. Recovery pages frontend

---

## Markers de Paralelização

- **[P]** Fase 1 (backend auth) e Fase 2 (frontend auth) após Fase 0
- **[P]** `domain/password.py`, `domain/totp.py`, `domain/tokens.py` — completamente independentes entre si
- **[P]** `admin_users.py` e `account.py` após Fase 1

---

## Riscos Técnicos

| Risco | Prob | Impacto | Mitigação |
|---|---|---|---|
| Token rotation race condition (dois refreshes simultâneos) | Média | Alto | `SELECT ... FOR UPDATE` no refresh token antes de rotation |
| MFA secret exposto em logs | Baixa | Crítico | `mfa_secret` encriptado com `Fernet(SECRET_KEY)` antes de guardar na BD; nunca em logs |
| Backup codes em texto claro na BD | Baixa | Alto | Argon2 hash de cada código individualmente |
| Rate limiting insuficiente em produção (memória local não escala) | Média | Médio | Middleware aceita Redis como backend; em dev usa dict em memória |
| Convite interceptado em trânsito | Baixa | Alto | HTTPS obrigatório; token tem validade e é one-time; mesmo interceptado expira |

---

## Impacto no Case Management Existente

**Zero alterações necessárias.** O `deps.py` já está escrito à espera deste JWT. Quando Platform Foundation emitir tokens com `sub`, `org_id`, `email`, `display_name`, `role` — o Case Management funciona imediatamente.

Único ajuste: o `GlobalRoleEnum` no modelo `User` tem `"viewer"` mas a spec define `"consultor"`. Corrigir na migração 009 sem quebrar dados existentes.

---

## Validação de Constituição

- **Art. 1 (World-Class):** ✓ Argon2 > bcrypt. Token rotation. Rate limiting. Backup codes com hash.
- **Art. 2 (Segurança):** ✓ MFA obrigatório para admins. Revogação imediata. Sem revelação de existência de email. TOTP não SMS.
- **Art. 5 (Design Editorial):** ✓ Login page dark-first, sem campos desnecessários, tipografia limpa.
- **Art. 6 (Integridade):** ✓ Todos os eventos de auth no `auth_log`. Imutável.
- **Art. 8 (Multi-Domínio):** ✓ Auth é agnóstica ao domínio forense — serve Digital, Médico-Legal, Financeiro sem distinção.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-06-01*
