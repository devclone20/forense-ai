# Plan: Evidence Ingestion

> Gerado por SPEC-DRIVEN em 2026-06-02
> Baseia-se em: `.specify/specs/evidence-ingestion/spec.md` (Aprovada ✓)
> Integra com: Case Management (casos + audit_log) · Platform Foundation (auth + RLS)
> Próximas migrações a partir de: 014

---

## Decisão de Arquitectura Central — Storage Plugável

Esta é a decisão que define toda a arquitectura do módulo.

O utilizador escolhe o backend de armazenamento no onboarding. A plataforma abstrai completamente o backend — o código de negócio não sabe se está a escrever em disco local ou em S3.

### Padrão: Storage Provider Interface

```
StorageProvider (ABC)
├── LocalStorageProvider      → filesystem local (air-gapped, on-premise)
├── S3StorageProvider         → AWS S3, Cloudflare R2, Wasabi (boto3)
├── MinIOStorageProvider      → MinIO auto-hospedado (boto3 com endpoint custom)
└── ReplicatedStorageProvider → Local primário + S3 replicação assíncrona
```

Cada provider implementa:
```python
async def store(file_id, stream) -> StorageRef       # guarda, devolve referência
async def retrieve(ref: StorageRef) -> AsyncStream   # lê sem expor URL
async def verify_exists(ref: StorageRef) -> bool     # verifica presença
async def compute_hash(ref: StorageRef) -> str       # recalcula SHA-256 para integridade
async def get_size(ref: StorageRef) -> int           # bytes usados
```

A `StorageRef` é uma string opaca que o provider sabe interpretar — path local, S3 key, etc. Nunca exposta ao utilizador ou ao frontend.

### Onboarding de Storage (novo passo no registo de organização)

Após criar a organização, o Admin é guiado num wizard com 3 perguntas:
1. "Onde quer guardar as evidências?" → opções com descrição de cada uma
2. "Qual o limite máximo por ficheiro?" → input com sugestões (500MB · 5GB · 50GB · Sem limite)
3. "Qual a capacidade total da organização?" → input com sugestões (50GB · 500GB · 5TB · Sem limite)

Credenciais S3 são encriptadas com Fernet antes de guardar na BD (mesmo padrão do `mfa_secret`).

---

## Stack — Sem novas dependências de runtime significativas

| Biblioteca | Para quê | Nota |
|---|---|---|
| `boto3` | S3-compatible storage (AWS, R2, MinIO, Wasabi) | Já standard; uma lib para todos os S3 |
| `aiofiles` | Streaming assíncrono para storage local | Mantém FastAPI non-blocking |
| `python-magic` | Detecção de tipo MIME real (não confiar na extensão) | Segurança: evita upload de executáveis disfarçados |
| `Pillow` | Geração de thumbnails para imagens | Opcional — apenas se preview activado |

Frontend: `react-dropzone` para upload com drag-and-drop e progress bar.

---

## Arquitectura do Upload (crítica para ficheiros grandes)

O upload usa **streaming multipart** — o ficheiro nunca está completamente em memória:

```
Browser → FastAPI (stream) → HashingStream (calcula SHA-256 on-the-fly)
                                        ↓
                              StorageProvider.store()
                                        ↓
                              BD: registo de evidência com hash
```

1. FastAPI recebe o ficheiro como `UploadFile` (async generator)
2. `HashingStream` envolve o stream — calcula SHA-256 em chunks enquanto escreve
3. Após escrita completa, hash está disponível sem ter de ler o ficheiro uma segunda vez
4. BD regista a evidência — **atómica**: ou tudo guardado ou nada registado

Se o upload falha a meio: o ficheiro parcial é apagado do storage, nenhum registo na BD.

---

## Componentes a Criar

### Backend — Novas Migrações

| Migração | O que cria |
|---|---|
| `014_storage_config.py` | Tabela `storage_configs`: org_id, backend, credentials_encrypted JSONB, max_file_bytes (nullable = sem limite), quota_bytes (nullable), used_bytes, quota_alert_sent_at |
| `015_evidences.py` | Tabela `evidences` + RLS + índices |
| `016_evidence_events.py` | Tabela `evidence_events` (append-only, REVOKE UPDATE/DELETE) |
| `017_evidence_number_seq.py` | Tabela `evidence_number_sequences` (por caso, análogo ao case_number) |
| `018_evidence_search.py` | tsvector em evidences + GIN index + trigger |

### Backend — Novos Ficheiros

| Ficheiro | Responsabilidade |
|---|---|
| `app/storage/__init__.py` | Interface `StorageProvider` ABC + `StorageRef` |
| `app/storage/local.py` | `LocalStorageProvider` — aiofiles, paths organizados por org/case/evidence_id |
| `app/storage/s3.py` | `S3StorageProvider` — boto3 async, suporta AWS/R2/MinIO/Wasabi via endpoint_url |
| `app/storage/replicated.py` | `ReplicatedStorageProvider` — escreve em local + replica para S3 assincronamente |
| `app/storage/factory.py` | `get_storage_provider(org_config) -> StorageProvider` |
| `app/storage/hashing.py` | `HashingStream` — calcula SHA-256 on-the-fly durante streaming |
| `app/models/evidence.py` | `Evidence`, `EvidenceEvent`, `EvidenceNumberSequence`, `StorageConfig` |
| `app/schemas/evidence.py` | `EvidenceCreate`, `EvidenceResponse`, `EvidenceListResponse`, `StorageConfigCreate` |
| `app/repositories/evidence_repository.py` | CRUD evidências + número sequencial atómico |
| `app/repositories/storage_config_repository.py` | CRUD storage configs |
| `app/services/evidence_service.py` | `ingest()`, `get()`, `list()`, `verify_integrity()`, `download_stream()`, `export_chain_of_custody()` |
| `app/services/storage_config_service.py` | `configure()`, `test_connection()`, `get_quota_status()` |
| `app/api/v1/evidences.py` | Endpoints de evidências |
| `app/api/v1/storage_config.py` | Endpoints de configuração de storage (admin) |

### Backend — API Endpoints

```
# Evidências
POST   /api/v1/cases/:case_id/evidences              Upload + registo
GET    /api/v1/cases/:case_id/evidences              Inventário (filtros + paginação)
GET    /api/v1/cases/:case_id/evidences/:id          Detalhe
GET    /api/v1/cases/:case_id/evidences/:id/download Stream do ficheiro original
POST   /api/v1/cases/:case_id/evidences/:id/verify   Verificar integridade
GET    /api/v1/cases/:case_id/evidences/chain-of-custody  Exportar cadeia de custódia

# Storage (admin da organização)
GET    /api/v1/admin/storage/config                  Configuração actual
POST   /api/v1/admin/storage/config                  Configurar/alterar backend
POST   /api/v1/admin/storage/config/test             Testar ligação ao storage
GET    /api/v1/admin/storage/quota                   Ocupação actual vs quota
```

### Frontend — Novas Páginas e Componentes

| Ficheiro | Responsabilidade |
|---|---|
| `app/(dashboard)/cases/[id]/evidences/page.tsx` | Inventário de evidências do caso |
| `app/(dashboard)/cases/[id]/evidences/[eid]/page.tsx` | Detalhe da evidência |
| `app/(dashboard)/admin/storage/page.tsx` | Wizard de configuração de storage |
| `components/evidences/EvidenceDropzone.tsx` | Upload drag-and-drop com progress, validação de tamanho antes do upload |
| `components/evidences/EvidenceTable.tsx` | Tabela inventário com badges de tipo e estado de integridade |
| `components/evidences/EvidenceDetail.tsx` | Hash SHA-256 copiável, metadata, histórico de acessos |
| `components/evidences/IntegrityBadge.tsx` | ✅ Íntegra / ❌ ADULTERADA — visual claro |
| `components/evidences/MetadataForm.tsx` | Campos dinâmicos por domínio forense (Digital/Médico-Legal/Financeiro) |
| `components/storage/StorageWizard.tsx` | Wizard 3 passos: escolha de backend → credenciais → limites → teste |
| `components/storage/QuotaIndicator.tsx` | Barra de progresso ocupação/quota com alerta a 90% |

---

## Data Model — Tabelas Novas

### `storage_configs`
```sql
CREATE TABLE storage_configs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL UNIQUE REFERENCES organizations(id),
  backend               TEXT NOT NULL CHECK (backend IN ('local','s3','minio','r2','wasabi','replicated')),
  credentials_encrypted JSONB NOT NULL DEFAULT '{}',  -- Fernet encrypted
  max_file_bytes        BIGINT,                        -- NULL = sem limite
  quota_bytes           BIGINT,                        -- NULL = sem limite
  used_bytes            BIGINT NOT NULL DEFAULT 0,
  quota_alert_sent_at   TIMESTAMPTZ,
  configured_by         UUID NOT NULL REFERENCES users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- RLS: apenas admins da org
```

### `evidences`
```sql
CREATE TYPE evidence_type AS ENUM (
  -- Digital
  'ficheiro_sistema','imagem_disco','dump_memoria','log_sistema',
  'capture_rede','artefacto_browser','registo_so','email_mensagem',
  -- Médico-Legal
  'relatorio_medico','fotografia_forense','resultado_laboratorial',
  'registo_hospitalar','laudo_pericial',
  -- Financeiro
  'extrato_bancario','fatura_recibo','contrato',
  'registo_transacao','comunicacao_financeira','relatorio_contabilistico',
  -- Genérico
  'outro'
);

CREATE TABLE evidences (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   UUID NOT NULL REFERENCES organizations(id),
  case_id           UUID NOT NULL REFERENCES cases(id),
  evidence_number   TEXT NOT NULL,                     -- "EV-001"
  title             TEXT NOT NULL,
  description       TEXT,
  evidence_type     evidence_type NOT NULL,
  storage_ref       TEXT NOT NULL,                     -- referência opaca para o StorageProvider
  original_filename TEXT NOT NULL,
  size_bytes        BIGINT NOT NULL,
  mime_type         TEXT NOT NULL,                     -- detectado pelo servidor, não pelo cliente
  sha256_hash       TEXT NOT NULL,                     -- calculado no servidor
  source_origin     TEXT,                              -- onde/como foi recolhida
  collected_at      TIMESTAMPTZ,                       -- data de recolha (≠ ingestão)
  ingested_by       UUID NOT NULL REFERENCES users(id),
  ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  tags              TEXT[] NOT NULL DEFAULT '{}',
  domain_metadata   JSONB NOT NULL DEFAULT '{}',       -- campos específicos por domínio
  search_vector     TSVECTOR,
  UNIQUE(case_id, evidence_number)
);

-- RLS — isolamento por organização + acesso apenas a membros do caso
ALTER TABLE evidences ENABLE ROW LEVEL SECURITY;
CREATE POLICY evidences_org ON evidences
  USING (organization_id = current_setting('app.current_org_id')::uuid);

-- Índices
CREATE INDEX idx_evidences_case      ON evidences(case_id, ingested_at DESC);
CREATE INDEX idx_evidences_hash      ON evidences(sha256_hash);         -- detecção de duplicados
CREATE INDEX idx_evidences_type      ON evidences(case_id, evidence_type);
CREATE INDEX idx_evidences_search    ON evidences USING GIN(search_vector);
CREATE INDEX idx_evidences_tags      ON evidences USING GIN(tags);
```

### `evidence_events` (append-only)
```sql
CREATE TYPE evidence_event_type AS ENUM (
  'ingested','viewed','downloaded','integrity_verified',
  'integrity_alert','chain_exported'
);

CREATE TABLE evidence_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,
  evidence_id     UUID NOT NULL REFERENCES evidences(id),
  event_type      evidence_event_type NOT NULL,
  actor_id        UUID REFERENCES users(id),
  actor_name      TEXT NOT NULL,                  -- snapshot
  ip_address      INET,
  metadata        JSONB NOT NULL DEFAULT '{}',    -- hash result para verify, filename para download
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

REVOKE UPDATE, DELETE ON evidence_events FROM forense_app_user;

CREATE INDEX idx_ev_events_evidence ON evidence_events(evidence_id, occurred_at DESC);
CREATE INDEX idx_ev_events_case     ON evidence_events(organization_id, occurred_at DESC);
```

### `evidence_number_sequences`
```sql
CREATE TABLE evidence_number_sequences (
  case_id   UUID NOT NULL REFERENCES cases(id),
  counter   BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (case_id)
);
-- Atómico: INSERT ... ON CONFLICT DO UPDATE SET counter = counter + 1 RETURNING counter
```

---

## Sequência de Implementação

### Fase 0 — Storage Abstraction + Migrações (bloqueante)
1. `[P]` `app/storage/__init__.py` — `StorageProvider` ABC + `StorageRef`
2. `[P]` `app/storage/hashing.py` — `HashingStream` (zero I/O, testável)
3. `[P]` `app/storage/local.py` — `LocalStorageProvider`
4. `[P]` `app/storage/s3.py` — `S3StorageProvider` (boto3, suporta endpoint_url)
5. `app/storage/factory.py` — `get_storage_provider()`
6. Migrações 014-018

### Fase 1 — Backend Core [P com Fase 2]
7. Models + Schemas
8. `evidence_repository.py` — incluindo número atómico
9. `storage_config_service.py` — configure, test_connection, quota
10. `evidence_service.ingest()` — streaming + hashing + quota check + duplicate detection
11. `evidence_service.verify_integrity()` — recalcular hash, comparar, registar evento
12. `evidence_service.download_stream()` — stream autenticado, regista evento
13. `evidence_service.export_chain_of_custody()` — CSV + HMAC
14. API endpoints evidências + storage config

### Fase 2 — Frontend [P com Fase 1]
15. `StorageWizard.tsx` — 3 passos: backend → credenciais → limites
16. `EvidenceDropzone.tsx` — drag-and-drop, validação pré-upload, progress bar
17. `EvidenceTable.tsx` + `IntegrityBadge.tsx`
18. `MetadataForm.tsx` — campos dinâmicos por domínio
19. Inventário page + Detalhe page

### Fase 3 — Storage Admin + Polish
20. `QuotaIndicator.tsx` + alerta 90%
21. `app/(dashboard)/admin/storage/page.tsx`
22. Testes: upload + hash verify + RLS isolation + duplicate detection + quota enforcement

---

## Riscos Técnicos

| Risco | Prob | Impacto | Mitigação |
|---|---|---|---|
| Upload de ficheiro grande interrompido deixa ficheiro parcial | Média | Médio | Transacção: guardar no storage → só então escrever na BD; cleanup de ficheiros sem registo |
| MIME type falsificado pelo cliente | Média | Alto | `python-magic` detecta tipo real pelo conteúdo, não pela extensão |
| Credenciais S3 expostas em logs | Baixa | Crítico | Fernet encrypt antes de BD; nunca em logs; mascarar em responses |
| Quota não actualizada em tempo real (concurrent uploads) | Média | Baixo | Incremento atómico em `storage_configs.used_bytes` via `UPDATE ... SET used_bytes = used_bytes + :size` |
| Storage local sem espaço em disco | Baixa | Alto | Verificar espaço disponível antes de aceitar upload; alerta proactivo |

---

## Impacto nos Módulos Existentes

**Case Management:** o `AuditActionEnum` em `models/case.py` precisa de adicionar `evidence_added` — um evento de ingestão é registado no audit log do caso (além do `evidence_events` próprio).

**Platform Foundation:** nenhuma alteração necessária — usa RLS e auth existentes.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-06-02*
