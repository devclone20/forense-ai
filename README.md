<p align="center">
  <img src="docs/assets/hero.svg" width="100%" alt="Forense AI — multi-domain forensic case management: evidence hashed with SHA-256 as it streams in, and a chain of custody that only grows">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-d47ba8?style=flat-square&labelColor=161b22" alt="Python 3.12">
  <img src="https://img.shields.io/badge/backend-fastapi%20%C2%B7%20sqlalchemy%202.0%20async-6ea8ff?style=flat-square&labelColor=161b22" alt="FastAPI + SQLAlchemy 2.0 async">
  <img src="https://img.shields.io/badge/database-postgresql%2016%20%2B%20rls-b18bf5?style=flat-square&labelColor=161b22" alt="PostgreSQL 16 with row level security">
  <img src="https://img.shields.io/badge/frontend-next.js%2014%20%C2%B7%20typescript-5ed3d8?style=flat-square&labelColor=161b22" alt="Next.js 14 and TypeScript">
  <img src="https://img.shields.io/badge/tests-87%20pytest-e8b86d?style=flat-square&labelColor=161b22" alt="87 pytest tests">
  <img src="https://img.shields.io/badge/licence-MIT-8b949e?style=flat-square&labelColor=161b22" alt="MIT licence">
</p>

# Forense AI

**Forense AI is a multi-domain forensic case management platform — digital, medico-legal and financial.**
An organisation opens a case, uploads the artifacts it has lawfully collected, and the platform does the
part humans get wrong: it hashes every file the moment it arrives, seals it in the organisation's own
storage backend, and records every hand it passes through in a ledger the application is not allowed to
edit. Case numbers are atomic. Status changes are a validated state machine. The audit trail is
append-only at the database, not by convention.

> **Forense is also an iNFT** — a Pi coding agent under the Forense neural soul, fused with an NFT
> (whoever holds the token holds the agent). This repo is its body, forged from the
> [inft-i01](https://github.com/devclone20/inft-i01) template. Boot it via Pi
> (`bash scripts/setup.sh` → `bash scripts/boot.sh`) or type `forense` in the CLONE FRAME iT terminal.
> → **[INFT.md](INFT.md)** · [AGENTS.md](AGENTS.md)

---

## What this is not

This is custody tooling for evidence an organisation already holds. It is not an acquisition tool.

- **It collects nothing on its own.** There is no crawler, no scraper and no external data source in this
  repository. Every artifact exists because an authenticated member of an organisation uploaded it into a
  case, and the row records who did it, from which IP and when.
- **Automation is owner-gated.** The agent layer never self-starts a scan, an ingest or a monitor — see
  `soul/neural_soul.md`.
- **The AI is never the authority.** Article 7 of `.specify/memory/constitution.md` requires every
  AI-produced conclusion to cite the evidence that supports it; a claim with no artifact behind it is a
  hypothesis, not a finding.
- **Nothing is quietly destroyed.** Originals are sealed, the ledgers are append-only, and the single
  delete path in the storage layer exists only to clean up a file whose ingest failed.

---

## Quickstart

Prerequisites: Docker + Docker Compose · Python 3.12 · Node.js 20+

```bash
# 1. PostgreSQL 16
docker-compose up -d postgres

# 2. Backend + migrations
cd apps/backend
pip install -e ".[dev]"
cp ../../.env.example .env          # set SECRET_KEY, AUDIT_HMAC_KEY, ENCRYPTION_KEY, RECOVERY_SECRET_KEY
DATABASE_URL_SYNC=postgresql://forense_app:dev_only_password@localhost:5432/forense_ai \
  alembic upgrade head

# 3. API
uvicorn app.main:app --reload --port 8000     # docs: http://localhost:8000/docs

# 4. Frontend
cd ../frontend
npm install
cp ../../.env.example .env.local
npm run dev                                    # app: http://localhost:3000
```

---

## Evidence ingestion

<p align="center">
  <img src="docs/assets/01-evidence-ingest.svg" width="100%" alt="Ingest pipeline: preflight quota checks, tee_stream hashing and storing in one pass, MIME and duplicate guards, then three append-only writes in one transaction">
</p>

An upload is never buffered in memory. `tee_stream` forks the byte stream so `hash_stream` computes the
SHA-256 while the storage provider writes the object — same pass, 64 KiB chunks, arbitrary file size.
The hash then decides everything downstream: a file whose digest already exists in the case is rejected
with `409`, and the digest is what integrity verification compares against for the rest of the case's life.

Storage is per organisation and admin-configured: `local`, `s3`, `r2`, `wasabi` or `minio`, with the
credentials held as a Fernet-encrypted JSONB blob (`app/storage/factory.py`).

---

## Chain of custody

<p align="center">
  <img src="docs/assets/02-chain-of-custody.svg" width="100%" alt="evidence_events is append-only with six event types; verification re-reads and re-hashes the object; the chain-of-custody export is a HMAC-SHA256 signed CSV">
</p>

Six event types, all appended, never updated: `ingested`, `viewed`, `downloaded`, `integrity_verified`,
`integrity_alert`, `chain_exported`. Verification re-reads the stored object through the provider and
compares the digest — on a mismatch it writes the alert row first, then the verification row, so a failed
check can never be silent. The export is a chronological CSV of the case's events, signed with
HMAC-SHA256 under `AUDIT_HMAC_KEY`, and exporting is itself an event.

---

## Case lifecycle

<p align="center">
  <img src="docs/assets/03-case-lifecycle.svg" width="100%" alt="Case state machine: aberto, em_investigacao, em_revisao, fechado, arquivado, with justification-gated backward transitions and admin-only reopening of archived cases">
</p>

`app/domain/case_state_machine.py` is a pure module — zero I/O, fully unit-tested. Forward moves are free;
the three backward moves each require a written justification; `arquivado` is terminal and only an admin
may reopen it. Case numbers come from an atomic per-org, per-year counter and default to
`FOR-{YYYY}-{NNNNN}`, with a template formatter for organisations that need their own
(`{YYYY}`, `{YY}`, `{NNNNN}`, `{N}`).

---

## Tenancy and immutability

<p align="center">
  <img src="docs/assets/04-tenancy-and-immutability.svg" width="100%" alt="JWT claims set app.current_org_id per session; row level security policies on ten tables; audit_log, auth_log and evidence_events are append-only by database privilege">
</p>

### Three inviolable invariants

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | Multi-tenant isolation | RLS policies on the ten tenant tables; `app.current_org_id` set from the JWT before any query |
| 2 | Immutable audit trail | `REVOKE UPDATE, DELETE` plus a trigger that raises on mutation (`audit_log`, `auth_log`, `evidence_events`) |
| 3 | Atomic case numbers | `INSERT ... ON CONFLICT DO UPDATE counter + 1 RETURNING counter` |

Auth is HS256 JWT with 15-minute access tokens, argon2 password hashing, TOTP MFA with the secret
encrypted at rest, and a 5-request-per-minute-per-IP limiter on the auth paths. Refresh tokens rotate on
every use and carry reuse detection: replaying a revoked token revokes its entire family and writes the
event to `auth_log`.

---

## API surface — `/api/v1`

| Group | Routes |
|---|---|
| Auth | `/auth/login` · `/auth/mfa/{setup,enable,verify}` · `/auth/refresh` · `/auth/logout` · `/auth/recovery/{request,confirm}` |
| Account | `/account/me` · `/account/password` · `/account/mfa/backup-codes/regenerate` |
| Admin | `/admin/users` · `/admin/storage` · `/invites` |
| Cases | `/cases` · `/cases/{case_id}` · `/cases/{case_id}/transitions` · `/cases/{case_id}/members` · `/cases/{case_id}/activity` |
| Evidence | `/cases/{case_id}/evidences` · `/{ev_id}` · `/{ev_id}/download` · `/{ev_id}/verify` · `/chain-of-custody` |

---

## Map

<p align="center">
  <img src="docs/assets/05-repo-map.svg" width="100%" alt="Repository map: the agent layer (identity, soul, .pi, scripts, skills, metadata) and the application layer (apps/backend, apps/frontend), plus the .specify spec layer">
</p>

| Layer | Path |
|---|---|
| Domain — state machine, formatters, password, tokens, TOTP | `apps/backend/app/domain/` |
| Repositories — RLS-aware data access | `apps/backend/app/repositories/` |
| Services — business logic + audit | `apps/backend/app/services/` |
| Storage — provider abstraction + streaming hash | `apps/backend/app/storage/` |
| API — thin HTTP adapters | `apps/backend/app/api/v1/` |
| Migrations — 18, Alembic | `apps/backend/alembic/versions/` |
| Frontend — Next.js 14 App Router | `apps/frontend/app/` |
| Agent — soul, Pi wiring, skills, NFT metadata | `soul/` `.pi/` `scripts/` `skills/` `metadata/` |
| Specs — constitution, feature log, per-feature specs | `.specify/` |

---

## Tests

```bash
docker exec forense_ai_db createdb -U forense_app forense_ai_test
cd apps/backend
pytest tests/ -v
```

87 tests across seven modules: the state machine (21), auth domain (25), auth service (13), storage
providers (12), evidence service (7), case service (6) and RLS isolation (3).

**`test_rls.py` must pass before any deploy.** It is the test that proves one organisation cannot read
another's rows.

---

## Status

| Module | State |
|---|---|
| Platform Foundation — orgs, users, auth, MFA, invites, recovery | Implemented |
| Case Management — cases, members, transitions, activity, audit | Implemented |
| Evidence Ingestion — storage backends, hashing, custody, export | Implemented |
| AI Research Engine | Named in the roadmap; no spec and no code in this repo yet |

Specs, plans and the feature log live in `.specify/` — this repository is built spec-first, and the
constitution's nine articles are the standard every module is held to.

---

## Licence and security

MIT (declared in `package.json`); `skills/cmux/` ships its own MIT licence. Public repo: no secrets, keys
or PII are committed — every credential is an environment variable, and the model key for the agent layer
is typed into your own terminal via `pi` → `/login`. See [INFT.md](INFT.md) for the agent's security and
privacy notes.
