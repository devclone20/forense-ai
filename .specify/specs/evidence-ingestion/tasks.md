# Tasks: Evidence Ingestion

> Gerado por SPEC-DRIVEN em 2026-06-02
> Gate: DESBLOQUEADO ✓

---

## Fase 0 — Storage Abstraction + Migrações (BLOQUEANTE)

| ID | Task | [P] | Est. | Deps |
|---|---|---|---|---|
| T001 | `app/storage/__init__.py` — `StorageProvider` ABC + `StorageRef` dataclass | — | 1h | — |
| T002 | `app/storage/hashing.py` — `HashingStream` calcula SHA-256 on-the-fly em chunks | [P] | 1h | T001 |
| T003 | `app/storage/local.py` — `LocalStorageProvider` (aiofiles, paths org/case/ev) | [P] | 2h | T001 |
| T004 | `app/storage/s3.py` — `S3StorageProvider` (boto3, endpoint_url p/ MinIO/R2/Wasabi) | [P] | 2h | T001 |
| T005 | `app/storage/replicated.py` — escreve em local + replica para S3 assincronamente | [P] | 2h | T003, T004 |
| T006 | `app/storage/factory.py` — `get_storage_provider(org_config)` | — | 30m | T003–T005 |
| T007 | Migração 014 — `storage_configs` + RLS | [P] | 1h | — |
| T008 | Migração 015 — `evidences` + RLS dupla + índices | [P] | 1.5h | — |
| T009 | Migração 016 — `evidence_events` append-only + REVOKE | [P] | 1h | — |
| T010 | Migração 017 — `evidence_number_sequences` | [P] | 30m | — |
| T011 | Migração 018 — search trigger + quota trigger | — | 1h | T008 |
| T012 | Testes unitários: `HashingStream` · `LocalStorageProvider` · `S3StorageProvider` (mock) | — | 2h | T002–T004 |

---

## Fase 1 — Backend Core [P com Fase 2]

| ID | Task | [P] | Est. | Deps |
|---|---|---|---|---|
| T013 | `app/models/evidence.py` — `Evidence`, `EvidenceEvent`, `EvidenceNumberSequence`, `StorageConfig` | — | 1.5h | F0 |
| T014 | `app/schemas/evidence.py` — request/response schemas + `StorageConfigCreate` | [P] | 1h | T013 |
| T015 | `app/repositories/evidence_repository.py` — CRUD + número atómico (`ON CONFLICT DO UPDATE`) | — | 2h | T013 |
| T016 | `app/repositories/storage_config_repository.py` — CRUD + quota update atómico | [P] | 1h | T013 |
| T017 | `app/services/storage_config_service.py` — `configure()`, `test_connection()`, `get_quota_status()` | — | 2h | T015, T016 |
| T018 | `app/services/evidence_service.ingest()` — stream + hash + quota check + duplicate detect + BD | — | 3h | T015, T017 |
| T019 | `app/services/evidence_service.verify_integrity()` — recalcular hash, comparar, evento + alerta | [P] | 2h | T015 |
| T020 | `app/services/evidence_service.download_stream()` — stream autenticado + evento de download | [P] | 1.5h | T015 |
| T021 | `app/services/evidence_service.export_chain_of_custody()` — CSV + HMAC-SHA256 | [P] | 2h | T015 |
| T022 | `app/api/v1/evidences.py` — todos os endpoints (upload multipart, list, detail, download, verify, export) | — | 3h | T018–T021 |
| T023 | `app/api/v1/storage_config.py` — GET/POST config + test + quota | — | 1.5h | T017 |
| T024 | `AuditActionEnum` em `case.py` — adicionar `evidence_added` | — | 30m | F0 |
| T025 | Testes integração: ingest + hash verify + RLS + duplicate + quota enforcement | — | 3h | T022, T023 |

---

## Fase 2 — Frontend [P com Fase 1]

| ID | Task | [P] | Est. | Deps |
|---|---|---|---|---|
| T026 | `components/storage/StorageWizard.tsx` — 3 passos: backend → credenciais → limites → teste | — | 3h | F0 |
| T027 | `components/storage/QuotaIndicator.tsx` — barra ocupação/quota + alerta 90% | [P] | 1h | T026 |
| T028 | `components/evidences/EvidenceDropzone.tsx` — drag-and-drop + validação pré-upload + progress | — | 2.5h | F0 |
| T029 | `components/evidences/MetadataForm.tsx` — campos dinâmicos por domínio forense | [P] | 2h | F0 |
| T030 | `components/evidences/IntegrityBadge.tsx` — ✅ Íntegra / ❌ ADULTERADA | [P] | 30m | F0 |
| T031 | `components/evidences/EvidenceTable.tsx` — tabela inventário com badges + filtros | [P] | 2h | T029, T030 |
| T032 | `app/(dashboard)/cases/[id]/evidences/page.tsx` — inventário do caso | — | 1.5h | T031 |
| T033 | `app/(dashboard)/cases/[id]/evidences/[eid]/page.tsx` — detalhe + hash + histórico acessos | — | 2h | T030 |
| T034 | `app/(dashboard)/admin/storage/page.tsx` — wizard + quota indicator | — | 1h | T026, T027 |

---

## Fase 3 — Polish + Testes E2E

| ID | Task | [P] | Est. | Deps |
|---|---|---|---|---|
| T035 | Teste E2E: upload → verify integrity → download → export chain | — | 2h | F1, F2 |
| T036 | Teste: adulteração detectada → alerta visível para todos os membros do caso | — | 1h | T035 |
| T037 | Teste: quota excedida → upload bloqueado com mensagem clara | — | 30m | T035 |
| T038 | Commit final + push: `feat(evidence): Evidence Ingestion complete` | — | 30m | F3 |

---

## Implement Gate ✓

- [x] spec.md — APROVADA 2026-06-02
- [x] plan.md — storage plugável + streaming + hashing on-the-fly
- [x] data-model.md — migrações 014-018 definidas
- [x] tasks.md — este ficheiro

**GATE: DESBLOQUEADO ✓**

---

*SPEC-DRIVEN | Forense AI | 2026-06-02*
