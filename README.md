# Forense AI

Multi-domain forensic case management platform. Digital. Medico-Legal. Financial.

> Stack: Python 3.12 + FastAPI + SQLAlchemy 2.0 async · PostgreSQL 16 + RLS · Next.js 14 App Router + TypeScript strict

---

## Quickstart

### Prerequisites
- Docker + Docker Compose
- Python 3.12
- Node.js 20+

### 1. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 2. Install backend and run migrations

```bash
cd backend
pip install -e ".[dev]"
cp ../.env.example .env          # set SECRET_KEY and AUDIT_HMAC_KEY
DATABASE_URL_SYNC=postgresql://forense_app:dev_only_password@localhost:5432/forense_ai \
  alembic upgrade head
```

### 3. Start API server

```bash
uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

### 4. Start frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
# App: http://localhost:3000
```

---

## Architecture

```
[Browser] → [Next.js 14 App Router] → [FastAPI /api/v1] → [PostgreSQL 16 + RLS]
                                            │
                               set_config(app.current_org_id)
                               per session, before every query
```

### Three inviolable invariants

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | Multi-tenant RLS | PostgreSQL policy on every table; org_id set from JWT middleware |
| 2 | Immutable audit log | DB trigger + REVOKE UPDATE/DELETE on app_user role |
| 3 | Atomic case numbers | INSERT ... ON CONFLICT DO UPDATE counter+1 RETURNING counter |

---

## Running tests

```bash
# Create test DB
docker exec forense_ai_db createdb -U forense_app forense_ai_test

cd backend
pytest tests/ -v
```

Critical: `test_rls.py` must pass before any deploy.

---

## Modules

| Module | Path |
|--------|------|
| Domain (state machine, formatters) | `backend/app/domain/` |
| Repositories (RLS-aware data access) | `backend/app/repositories/` |
| Services (business logic + audit) | `backend/app/services/` |
| API (thin HTTP adapters) | `backend/app/api/v1/` |
| Frontend | `frontend/app/(dashboard)/` |

---

## Case lifecycle

```
aberto -> em_investigacao -> em_revisao -> fechado -> arquivado
              ^                  ^              ^
        (justificacao)     (justificacao)  (justificacao)
```

Backward transitions require justification. Only admins can reopen archived cases.

---

## Project structure

```
.specify/          # SPEC-DRIVEN — specs, planos, constituição, research
  memory/          # constituição + feature log
  specs/           # specs por feature
  research/        # referências GitHub e dados de treino
```

## Modules roadmap

- Case Management — implemented (this commit)
- Platform Foundation — spec em preparação
- Evidence Ingestion — spec em preparação
- AI Research Engine — spec em preparação

