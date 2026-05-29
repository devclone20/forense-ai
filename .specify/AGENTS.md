# AGENTS.md — Forense AI

> Gerado por SPEC-DRIVEN | 2026-05-29 | Stack: A definir
> Este ficheiro é injectado em todos os agentes de IA antes de qualquer tarefa.

---

## Identidade do Projecto

**Nome:** Forense AI
**Objectivo:** Plataforma multi-forense com IA — pesquisa em bases de dados forenses (web/internet), ingestão de evidências, análise com IA, geração de relatórios periciais e gestão de casos/processos. Serve peritos forenses, forças de segurança, magistratura, advogados e equipas de cibersegurança.
**Stack:** Python + FastAPI · PostgreSQL (RLS) · SQLAlchemy 2.0 + Alembic · Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
**Fase actual:** Especificação / Início de desenvolvimento

---

## Constituição Activa

### Art. 1 — Padrão World-Class
Se alguém auditasse este codebase para comprar a empresa, não encontraria nada para ter vergonha.

### Art. 2 — Segurança Primeiro
Dados forenses são sensíveis. OWASP Top 10 2025 é o baseline mínimo. hm-security antes de qualquer deploy.

### Art. 5 — Design Editorial
Dark-first. Tipografia editorial. Referências: Linear, Vercel, Stripe. Se parece um template → reprovou.

### Art. 6 — Integridade de Evidências
Hash SHA-256 no momento de ingestão. Timestamps auditáveis. Log de acesso completo. Cadeia de custódia digital é sagrada.

### Art. 7 — Rastreabilidade de IA
Toda a análise de IA cita a fonte. Conclusões sem evidência verificável são proibidas.

### Art. 8 — Multi-Domínio por Design
Arquitectura suporta nativamente forense digital, médico-legal, e financeiro. Extensível sem reescritas.

Constituição completa: `.specify/memory/constitution.md`

---

## Spec Activa

**Feature em progresso:** Nenhuma
**Status:** Aguarda `/spec-driven:specify`
**Próxima acção:** Criar spec para a primeira feature (recomendado: Core Platform + Case Management)

---

## Stack & Restrições

> Stack ainda não definida. Será escolhida em `/spec-driven:plan` com base nas specs.

**Restrições invioláveis:**
- Evidências são imutáveis após ingestão (hash + timestamp)
- Toda a IA tem source citation obrigatória
- Arquitectura multi-domínio desde o primeiro commit
- Nenhum dado forense em logs não-auditados
- Autenticação robusta (MFA recomendado para acesso a casos ativos)

---

## Padrões de Design

- **Dark-first** — interface desenhada para modo escuro, light como variante
- **Tipografia editorial** — hierarquia clara, espaçamento preciso, densidade de informação controlada
- **Referências:** Linear (gestão de casos), Vercel (dashboard), Stripe (detalhe de dados), Apple (clareza)
- Se parece um template → reprovou
- Se poderia pertencer a qualquer produto → reprovou
- **Domínio forense** — seriedade, credibilidade, precisão visual. Não é um produto consumer.

---

## Módulos do Produto (visão macro)

| Módulo | Descrição |
|---|---|
| **Case Management** | Criação e gestão de casos/processos de investigação |
| **Evidence Ingestion** | Upload, hash, registo e catalogação de evidências |
| **AI Research Engine** | Pesquisa em bases de dados forenses online (web scraping + APIs) |
| **AI Analysis** | Detecção de padrões, anomalias, ligações entre evidências |
| **Report Generator** | Geração assistida de relatórios periciais estruturados |
| **Chain of Custody** | Registo auditável de toda a cadeia de custódia |
| **Multi-Domain Support** | Digital · Médico-Legal · Financeiro |

---

## Coordenação de Agentes

| Agente | Responsabilidade | Quando usar |
|---|---|---|
| **SPEC-DRIVEN** | Contexto, specs, coordenação | Início e fim de cada feature |
| **Rider** | Orquestração multi-agente | Features complexas, multi-ficheiro |
| **hm-engineer** | Validação de código | Antes de qualquer PR |
| **hm-designer** | Validação de UI/UX | Antes de ship de qualquer interface |
| **hm-qa** | Testes e edge cases | Após implementação |
| **hm-security** | Audit de segurança | Antes de qualquer deploy |
| **hm-deploy** | Gate de infraestrutura | Deploy final |

**Sequência padrão de uma feature:**
```
SPEC-DRIVEN:specify → SPEC-DRIVEN:plan → SPEC-DRIVEN:tasks
→ Rider (orquestração) → hm-engineer (validação)
→ hm-designer (se UI) → hm-qa → hm-security
→ hm-deploy → SPEC-DRIVEN:review → SPEC-DRIVEN:train
```

---

## Referências de Implementação

> Repositórios GitHub pesquisados e catalogados em `.specify/research/github-repos.md`

| Tier | Repositório | Domínio | Usar para |
|---|---|---|---|
| 1 | [AIFT](https://github.com/FlipForensics/AIFT) | AI Forense | Template de workflow AI + triage + relatórios |
| 1 | [Timesketch](https://github.com/google/timesketch) | Timeline | Motor de timeline; correlação cross-domain |
| 1 | [Sleuth Kit + Autopsy](https://github.com/sleuthkit/autopsy) | Digital | Backbone de forense digital |
| 2 | [SpiderFoot](https://github.com/smicallef/spiderfoot) | OSINT | AI Research Engine — 200+ módulos |
| 2 | [Volatility](https://github.com/volatilityfoundation/volatility) | Memória | Análise de RAM |
| 2 | [MVT](https://github.com/mvt-project/mvt) | Mobile | Forense móvel Android/iOS |
| 2 | [FraudEx](https://github.com/jayvaidya30/fraud-ex-stable) | Financeiro | XAI para anomalias financeiras |
| 3 | [BlockLens](https://github.com/sejeeswarank/BlockLens) | Imagem | Autenticidade + deepfake + blockchain |
| 3 | [DeepForge](https://github.com/mwasifanwar/DeepForge) | Imagem | Detecção deepfakes ensemble ML |

**Chain of Custody:** [BCHOC](https://github.com/chaincode-nc/BCHOC) · [EviGuard](https://github.com/NxOp/EviGuard) · [0xRuchiKaraShunti](https://github.com/Sampriti2803/0xRuchiKaraShunti)

Referência completa: `.specify/research/github-repos.md`

---

## Aprendizagens Relevantes

> Da memória global — aplicáveis a plataformas com gestão de dados + AI + UI complexa.

- **Dados primeiro, UI depois** — modelar entidades e schemas antes de construir qualquer interface
- **Separar features grandes em sub-sessões** — Case Management, Evidence Ingestion, AI Engine, Reports são cada uma uma sessão separada
- **Rider para features multi-ficheiro** — qualquer feature que toque >3 ficheiros deve ser orquestrada pelo Rider
- **Segurança é design constraint, não afterthought** — hash de evidências, auth, e audit logs são requisitos da Fase 0
- **LLM local para dados sensíveis** — dados forenses não saem para cloud; padrão: Isolation Forest + LLM local (ver Financial Anomaly Detection repo)
- **XAI obrigatório** — toda a conclusão de IA deve ser explicável e rastreável à fonte (Art. 7 da Constituição)

---

*SPEC-DRIVEN | Specification-Driven AI Development*
*Baseado em [github/spec-kit](https://github.com/github/spec-kit)*
