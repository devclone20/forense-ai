# Tasks: Platform Foundation

> Gerado por SPEC-DRIVEN em 2026-06-02
> Baseia-se em: plan.md aprovado
> Gate: DESBLOQUEADO ✓ — spec + plan + data-model aprovados

---

## Legenda

- `[P]` — paralelizável com outras tasks marcadas `[P]` na mesma fase
- `[S1]`…`[S9]` — User Story da spec que esta task serve
- `(Xh)` — estimativa de tempo

---

## Fase 0 — Domínio Puro + Migrações ⚠️ BLOQUEANTE

> Nada nas fases seguintes começa sem esta fase completa.

| ID | Task | Stories | Est. | Deps |
|---|---|---|---|---|
| T001 | `[P]` `domain/password.py` — Argon2id hash + verify + unit tests | S4 | 1h | — |
| T002 | `[P]` `domain/totp.py` — TOTP secret gen, QR URI, verify, 8 backup codes hash/verify + unit tests | S5 | 2h | — |
| T003 | `[P]` `domain/tokens.py` — JWT issue (access 15min + mfa_pending 5min) + refresh UUID gen + unit tests | S4, S6 | 2h | — |
| T004 | Migração 009 — estender `users` com campos auth + expand `global_role` enum | S4, S5 | 1h | — |
| T005 | `[P]` Migração 010 — tabela `invitations` + RLS | S2, S3 | 1h | T004 |
| T006 | `[P]` Migração 011 — tabela `refresh_tokens` com `family_id` | S6 | 1h | T004 |
| T007 | `[P]` Migração 012 — tabela `auth_log` imutável (REVOKE UPDATE/DELETE) | S4-S8 | 1h | T004 |
| T008 | Migração 013 — `invite_expiry_days` em `organizations` | S2 | 30m | T004 |

**Fase 0 completa quando:** T001–T008 ✓ + `pytest tests/domain/` passa a 100%

---

## Fase 1 — Backend Auth Core `[P com Fase 2]`

| ID | Task | Stories | Est. | Deps |
|---|---|---|---|---|
| T009 | `repositories/auth_repository.py` — invite CRUD, refresh token CRUD, auth_log append | S2–S6 | 2h | F0 |
| T010 | `services/auth_service.py` — login() + MFA flow completo (provisório → verify → definitivo) | S4, S5 | 3h | T009 |
| T011 | `[P]` `services/invite_service.py` — create, accept, revoke | S2, S3 | 2h | T009 |
| T012 | `[P]` `services/recovery_service.py` — request + confirm (token 1h, resposta neutra) | S9 | 1.5h | T009 |
| T013 | `middleware/rate_limit.py` — 5 req/min em auth endpoints, in-memory (Redis-ready) | S4 | 1h | F0 |
| T014 | `api/v1/auth.py` — POST /auth/login, /refresh, /logout, /mfa/setup, /mfa/verify | S4, S5, S6 | 2h | T010 |
| T015 | `[P]` `api/v1/invites.py` — POST /invites, DELETE /invites/:id, POST /invites/:token/accept | S2, S3 | 1.5h | T011 |
| T016 | `[P]` `api/v1/account.py` — GET/PATCH /account/me, POST /account/password, MFA setup/enable/backup-regen | S5, S7 | 2h | T010 |
| T017 | `[P]` `api/v1/admin_users.py` — GET /admin/users, PATCH role, POST suspend (revoga tokens) | S1, S8 | 2h | T010 |
| T018 | `[P]` `api/v1/recovery.py` — POST /auth/recovery/request, POST /auth/recovery/confirm | S9 | 1h | T012 |
| T019 | Testes de integração auth: login flow, MFA flow, token rotation, roubo de token detectado | S4–S6 | 2h | T014 |

---

## Fase 2 — Frontend Auth Base `[P com Fase 1]`

| ID | Task | Stories | Est. | Deps |
|---|---|---|---|---|
| T020 | Layout `app/(auth)/` — páginas de auth separadas do dashboard, sem sidebar | S3, S4 | 1h | F0 |
| T021 | `[P]` `components/auth/LoginForm.tsx` — email + password, validação inline, dark-first | S4 | 1.5h | T020 |
| T022 | `[P]` `components/auth/MFAForm.tsx` — input 6 dígitos auto-focus + opção "usar backup code" | S5 | 1h | T020 |
| T023 | `app/(auth)/login/page.tsx` — orquestra LoginForm → redirect para /mfa se admin | S4 | 1h | T021 |
| T024 | `app/(auth)/login/mfa/page.tsx` — MFAForm + feedback de erro/sucesso | S5 | 1h | T022 |
| T025 | `app/(auth)/invite/[token]/page.tsx` — validar token, form de nome + password | S3 | 1.5h | T020 |
| T026 | `lib/auth.ts` — token storage (httpOnly cookie), auto-refresh em background, logout | S4, S6 | 2h | T020 |

---

## Fase 3 — Account + Admin UI

| ID | Task | Stories | Est. | Deps |
|---|---|---|---|---|
| T027 | `components/auth/MFASetup.tsx` — QR code display + backup codes list (copiar/descarregar) | S5 | 2h | F1, F2 |
| T028 | `app/(dashboard)/account/page.tsx` — perfil: nome, password, estado MFA, regenerar backup codes | S5, S7 | 2h | T027 |
| T029 | `[P]` `components/admin/UserTable.tsx` — tabela com papel (badge), estado, acções (alterar papel, suspender) | S8 | 2h | F1, F2 |
| T030 | `[P]` `components/admin/InviteModal.tsx` — modal: email + papel + prazo, botão "Enviar Convite" | S2 | 1.5h | F1, F2 |
| T031 | `app/(dashboard)/admin/users/page.tsx` — UserTable + InviteModal + convites pendentes | S1, S2, S8 | 1.5h | T029, T030 |

---

## Fase 4 — Recovery + Polish

| ID | Task | Stories | Est. | Deps |
|---|---|---|---|---|
| T032 | `app/(auth)/recovery/page.tsx` — form email, resposta neutra, dark-first | S9 | 1h | F1 |
| T033 | `app/(auth)/recovery/[token]/page.tsx` — nova password + confirmação + redirect login | S9 | 1h | F1 |
| T034 | Testes E2E: login → MFA → dashboard → logout → token expirado → refresh automático | S4–S6 | 2h | F3 |
| T035 | Push + commit final: `feat(auth): Platform Foundation complete` | — | 30m | F4 |

---

## Sumário de Estimativas

| Fase | Tasks | Estimativa |
|---|---|---|
| Fase 0 — Domínio + Migrações | T001–T008 | ~9.5h |
| Fase 1 — Backend Auth Core | T009–T019 | ~19h |
| Fase 2 — Frontend Auth Base `[P com F1]` | T020–T026 | ~9h |
| Fase 3 — Account + Admin UI | T027–T031 | ~9h |
| Fase 4 — Recovery + Polish | T032–T035 | ~4.5h |
| **Total sequencial** | | **~51h** |
| **Com paralelização F1+F2** | | **~35h efectivas** |

---

## Implement Gate — Checklist

- [x] `constitution.md` — 9 artigos definidos
- [x] `spec.md` — APROVADA 2026-06-02
- [x] `plan.md` — aprovado 2026-06-02
- [x] `data-model.md` — migrações 009-013 definidas
- [x] `tasks.md` — este ficheiro
- [x] Decisões técnicas aprovadas — Argon2 + token rotation + TOTP

**GATE: DESBLOQUEADO ✓** — Rider pode começar a implementar.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-06-02*
