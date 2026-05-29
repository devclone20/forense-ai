# Plan: Case Management

> Gerado por SPEC-DRIVEN em 2026-05-29
> Decisões técnicas aprovadas pelo fundador em 2026-05-29
> Baseia-se em: `.specify/specs/case-management/spec.md`
> Constituição: `.specify/memory/constitution.md`

---

## Stack Decision

Esta é a escolha mais importante do projecto. A stack não é escolhida pelo que é popular — é escolhida pelo que é a melhor ferramenta para este problema específico.

**Requisitos que determinam a stack:**
- Multi-tenancy com isolamento total de dados
- Audit log imutável com integridade verificável
- RBAC por caso (não apenas por utilizador)
- Full-text search <500ms em 10K casos
- Plataforma AI — o backend vai crescer para análise de dados forenses
- Operado por profissionais (não consumer) — performance e segurança > time-to-market

### Backend — Python + FastAPI

| Alternativa | Por que não |
|---|---|
| Node.js/Express | Ecossistema AI/ML inexistente. Processar dados forenses em Python é a norma da indústria. |
| Django | Mais batteries-included mas mais opinionado. FastAPI dá mais controlo para um produto custom. |
| Go | Excelente performance, mas ecossistema AI/ML fraco. O produto vai crescer para ML — não vale a penalização. |

**FastAPI** — async nativo, validação automática via Pydantic, OpenAPI spec gerada automaticamente, excelente para APIs que crescem.

### Base de Dados — PostgreSQL

A única escolha para este problema. Razões:

1. **Row Level Security (RLS)** — isolamento de dados multi-tenant ao nível do motor de base de dados. Uma query que não inclua o `organization_id` certo retorna zero linhas — por policy, não por código de aplicação.
2. **JSONB** — campos personalizáveis por domínio forense sem reescritas de schema.
3. **Full-text search nativo** — `tsvector`/`tsquery` com índices GIN. Zero dependências externas para <500ms em 10K casos.
4. **Sequences atómicas** — resolução do problema de numeração concorrente de casos.
5. **ACID completo** — audit log append-only com garantias transaccionais.

### ORM — SQLAlchemy 2.0 (async) + Alembic

- SQLAlchemy 2.0 com suporte async completo — não bloqueia o event loop do FastAPI
- Alembic para migrações versionadas — cada alteração de schema é rastreável

### Frontend — Next.js 14 + TypeScript + Tailwind CSS

| Alternativa | Por que não |
|---|---|
| React SPA puro | Sem SSR — problemas de SEO e performance inicial em dashboards complexos. Sem file-based routing. |
| Vanilla JS | Inadequado para a complexidade de UI deste produto (dashboards, timelines, filtros, RBAC visual). |
| Vue/Svelte | Menor ecossistema de componentes. A combinação Next.js + shadcn/ui é a referência do sector (Linear, Vercel, Stripe). |

**shadcn/ui** como primitivos de componentes — não é uma biblioteca de componentes com opinião visual; é código que se copia e adapta. O design é nosso, não deles.

### Autenticação — Auth pré-existente (spec `platform-foundation`)

A spec de Case Management pressupõe autenticação funcional. O JWT inclui `organization_id` e `user_id` nos claims — o backend valida e propaga para o contexto de RLS.

---

## Arquitectura da Solução

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  CaseListPage │ CaseDetailPage │ Dashboard │ Modals      │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS / JSON
┌──────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend                        │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  API Layer  │  │ Service Layer│  │  Domain Models │  │
│  │  (routers)  │→ │  (business   │→ │  (Pydantic +   │  │
│  │             │  │   logic)     │  │   SQLAlchemy)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Repository Layer                    │    │
│  │  (abstracção sobre SQLAlchemy — testável)        │    │
│  └──────────────────────┬──────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    PostgreSQL                             │
│                                                          │
│  Row Level Security (RLS) — isolamento por org          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │organizations│ │  cases  │ │case_members│ │audit_log │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────────────────┐ ┌────────────────────────┐    │
│  │ case_state_transitions│ │ case_number_sequences  │    │
│  └──────────────────────┘ └────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Padrões de Design Críticos

### 1. Multi-Tenancy via Row Level Security (RLS)

**O problema:** Numa instância partilhada, uma query errada pode vazar dados entre organizações.

**A solução:** PostgreSQL RLS — policies que filtram automaticamente por `organization_id`. O código de aplicação **não consegue** retornar dados de outra organização, mesmo com um bug.

```sql
-- Exemplo de policy (ver data-model.md para versão completa)
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
CREATE POLICY cases_org_isolation ON cases
  USING (organization_id = current_setting('app.current_org_id')::uuid);
```

O backend propaga o `organization_id` do JWT para o contexto da sessão PostgreSQL antes de qualquer query.

### 2. Audit Log Append-Only

**O problema:** Um log que pode ser modificado não tem valor legal.

**A solução:**
- Tabela `audit_log` sem `UPDATE` nem `DELETE` — permissões a nível de BD
- Trigger PostgreSQL que escreve no audit_log automaticamente para alterações em `cases` e `case_members`
- Exportação com HMAC-SHA256 assinado por chave do servidor — o ficheiro exportado tem uma assinatura verificável

### 3. Motor de Numeração de Casos (Pluggable)

**O problema:** O formato `FOR-YYYY-NNNNN` é o padrão hoje, mas amanhã pode mudar.

**A solução:** Strategy pattern — um `CaseNumberFormatter` abstract com implementações plugáveis. A sequência é atómica (PostgreSQL `SEQUENCE` por organização).

```
CaseNumberFormatter (abstract)
├── DefaultFormatter        → "FOR-2026-00001"
├── OrgPrefixFormatter      → "LISBOA-2026-00001"
└── DomainFormatter         → "DIG-2026-00001" / "MED-2026-00001"
```

Cada organização tem uma configuração que aponta para o formatter e os seus parâmetros.

### 4. State Machine Explícita

Os estados não são strings soltas — são uma máquina de estados com transições permitidas definidas no código:

```
Aberto → Em Investigação → Em Revisão → Fechado → Arquivado
                                              ↑
         (backward transitions com justificação obrigatória)
```

A lógica de transição vive no `CaseService`, não em validações ad-hoc nos routers.

### 5. RBAC por Caso (não global)

Um utilizador tem um papel **global** na plataforma (ex: Perito Forense) e pode ter papéis **diferentes em cada caso** (ex: Investigador no caso A, Supervisor no caso B). O controlo de acesso verifica sempre o papel no caso específico, não apenas o papel global.

---

## Componentes a Criar

### Backend

| Componente | Ficheiro | Responsabilidade |
|---|---|---|
| Case Router | `api/routers/cases.py` | Endpoints CRUD de casos |
| Case Member Router | `api/routers/case_members.py` | Endpoints de atribuição de equipa |
| Activity Router | `api/routers/activity.py` | Endpoints de log e exportação |
| Case Service | `services/case_service.py` | Lógica de negócio: criar, editar, state machine |
| Case Member Service | `services/case_member_service.py` | Lógica de atribuição e remoção |
| Audit Log Service | `services/audit_log_service.py` | Escrita e exportação do log |
| Case Number Service | `services/case_number_service.py` | Motor de numeração plugável |
| Case Repository | `repositories/case_repository.py` | Acesso a dados — cases |
| Case Member Repository | `repositories/case_member_repository.py` | Acesso a dados — membros |
| Audit Log Repository | `repositories/audit_log_repository.py` | Acesso a dados — log (read-only) |
| Case Models | `models/case.py` | SQLAlchemy models |
| Case Schemas | `schemas/case.py` | Pydantic request/response schemas |
| RLS Middleware | `middleware/tenant.py` | Propaga org_id para contexto PostgreSQL |
| State Machine | `domain/case_state_machine.py` | Transições e validações de estado |
| Number Formatters | `domain/number_formatters.py` | Strategy pattern para numeração |

### Frontend

| Componente | Ficheiro | Responsabilidade |
|---|---|---|
| Cases List Page | `app/cases/page.tsx` | Lista de casos com filtros |
| Case Detail Page | `app/cases/[id]/page.tsx` | Detalhe de um caso |
| Dashboard Page | `app/dashboard/page.tsx` | Vista agregada |
| Create Case Modal | `components/cases/CreateCaseModal.tsx` | Form de criação |
| State Transition Panel | `components/cases/StatePanel.tsx` | Alterar estado com justificação |
| Case Members Panel | `components/cases/MembersPanel.tsx` | Ver e gerir equipa |
| Activity Timeline | `components/cases/ActivityTimeline.tsx` | Timeline de actividade |
| Case Card | `components/cases/CaseCard.tsx` | Card reutilizável na lista |
| Case Filters | `components/cases/CaseFilters.tsx` | Painel de filtros |

### Migrações (Alembic)

| Migração | O que cria |
|---|---|
| `001_create_organizations` | Tabela organizations + RLS |
| `002_create_cases` | Tabela cases + índices + RLS |
| `003_create_case_members` | Tabela case_members + RLS |
| `004_create_state_transitions` | Tabela case_state_transitions |
| `005_create_audit_log` | Tabela audit_log (append-only) |
| `006_create_number_sequences` | Tabela case_number_sequences + sequences |
| `007_create_search_indexes` | Índices GIN para full-text search |
| `008_create_audit_triggers` | Triggers PostgreSQL para audit automático |

---

## API Contracts

### Casos

```
POST   /api/v1/cases                          Criar caso
GET    /api/v1/cases                          Listar casos (filtros via query params)
GET    /api/v1/cases/:id                      Detalhe de um caso
PATCH  /api/v1/cases/:id                      Actualizar caso (título, descrição, tags)
POST   /api/v1/cases/:id/transitions          Transição de estado
```

### Membros

```
GET    /api/v1/cases/:id/members              Listar membros
POST   /api/v1/cases/:id/members              Atribuir membro
DELETE /api/v1/cases/:id/members/:userId      Remover membro
```

### Actividade

```
GET    /api/v1/cases/:id/activity             Log de actividade (paginado)
GET    /api/v1/cases/:id/activity/export      Exportar log com assinatura HMAC
```

### Dashboard

```
GET    /api/v1/dashboard/summary              Contagens por estado + casos sem actividade
```

---

## Sequência de Implementação

### Fase 0 — Fundação (bloqueante para tudo o resto)
1. Setup do projecto (estrutura de directorias, dependências, Docker)
2. Configuração PostgreSQL + Alembic
3. Migrações 001-006 (schema completo)
4. RLS Middleware — propaga org_id para contexto
5. Migração 007-008 (índices + triggers)

### Fase 1 — Core Backend [P com Fase 2 frontend]
6. Models SQLAlchemy + Pydantic schemas
7. State Machine (`domain/case_state_machine.py`)
8. Motor de numeração (`domain/number_formatters.py`)
9. Case Repository + Case Service
10. Case Router (POST + GET /cases, GET /cases/:id)

### Fase 2 — Frontend Base [P com Fase 1 backend]
11. Setup Next.js + Tailwind + shadcn/ui primitivos
12. API client (fetch wrapper com auth headers)
13. CaseCard + CaseFilters (componentes sem dados reais — mock)
14. Cases List Page (com mock data)

### Fase 3 — Features Secundárias
15. Case Member Service + Repository + Router
16. Audit Log Service + Repository + Router
17. Exportação HMAC do log
18. PATCH /cases/:id + POST /cases/:id/transitions

### Fase 4 — UI Completa
19. CreateCaseModal
20. StateTransitionPanel (com justificação obrigatória)
21. MembersPanel
22. ActivityTimeline
23. CaseDetail Page completa

### Fase 5 — Dashboard + Pesquisa
24. Full-text search (tsvector + GIN index + API)
25. Dashboard summary endpoint
26. Dashboard Page frontend

---

## Markers de Paralelização

- **[P]** Fase 1 (backend core) e Fase 2 (frontend base) podem correr em paralelo após Fase 0 completa
- **[P]** Case Member Service (15) e Audit Log Service (16) são independentes — podem correr em paralelo
- **[P]** Frontend ActivityTimeline (22) e Dashboard Page (25) são independentes após API contracts definidos

---

## Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Gap em RLS policy — leak de dados entre orgs | Média | Crítico | Testes de integração obrigatórios que simulam cross-org access. Cada query testada com 2 organizações. |
| Race condition na numeração de casos | Baixa | Médio | `SELECT ... FOR UPDATE` no sequence counter. Testar com load test. |
| Audit log corrompido ou manipulável | Baixa | Crítico | Permissões BD restritas (app user sem UPDATE/DELETE em audit_log). Export HMAC verificável. |
| Performance da search degradar com volume | Média | Médio | Índice GIN criado desde Fase 0. Testar com 10K rows antes de ship. |
| Frontend state management complexo (RBAC visual) | Média | Baixo | Context API para permissões do caso actual. Calcular no servidor, não no cliente. |

---

## Validação de Constituição

- **Art. 1 (World-Class):** ✓ Stack escolhida pela melhor ferramenta, não pela mais popular. RLS > código de aplicação para isolamento.
- **Art. 2 (Segurança):** ✓ RLS no motor de BD. RBAC por caso. Audit log imutável. HMAC em exportações.
- **Art. 3 (Spec antes de código):** ✓ Spec clarificada e aprovada antes deste plano.
- **Art. 5 (Design Editorial):** ✓ Next.js + shadcn/ui como primitivos, não template. Dark-first definido.
- **Art. 6 (Integridade de Evidências):** ✓ Audit log append-only com triggers. Sem DELETE em dados forenses.
- **Art. 7 (Rastreabilidade de IA):** ✓ Não aplicável neste módulo — sem IA no Case Management.
- **Art. 8 (Multi-Domínio):** ✓ `forensic_domain` enum extensível. JSONB para campos por domínio. Motor de numeração plugável.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-05-29*
