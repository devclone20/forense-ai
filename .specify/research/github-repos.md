# Forense AI — Referências GitHub

> Compilado por SPEC-DRIVEN em 2026-05-29
> Fase: Preparação de terreno (pré-desenvolvimento)
> Objectivo: Referências, integrações potenciais, e datasets de treino

---

## Arquitectura Modular Recomendada

```
Forense AI Platform
├── Digital Forensics Module
│   ├── Sleuth Kit (disk analysis)
│   ├── Autopsy (GUI reference)
│   └── IPED (carving engine)
│
├── Memory & Endpoint Forensics
│   ├── Volatility (RAM analysis)
│   └── MVT (mobile forensics)
│
├── Timeline & Correlation Engine
│   ├── Timesketch (timeline UI/API)
│   └── Hayabusa (log processing)
│
├── OSINT & Research Engine
│   ├── SpiderFoot (200+ intelligence modules)
│   └── Network Forensics (PCAP tools)
│
├── Financial Forensics Module
│   ├── FraudEx (explainable AI)
│   └── Anomaly Detection (Isolation Forest + LLM)
│
├── Medico-Legal Module
│   ├── Image Forensics (BlockLens / DeepForge)
│   └── Metadata & deepfake detection
│
├── Evidence Management
│   └── Blockchain Chain-of-Custody
│
└── AI/Automation Layer
    ├── Triage automation (AIFT reference)
    ├── Report generation
    └── Custom ML pipeline
```

---

## TIER 1 — Core Foundation (Must-Reference)

### AIFT — AI-powered Forensic Investigation Tool
- **URL:** https://github.com/FlipForensics/AIFT
- **Stars:** 800+
- **O que faz:** AI-driven forensic triage para Windows/Linux; upload disk image → relatório forense em minutos
- **Porquê é crítico:** Referência de implementação para pipeline AI + triage automático + geração de relatórios. Processamento local (sem cloud).
- **Usar para:** Template de workflow de análise AI, geração de relatórios, estrutura de triage
- **Licença:** Proprietária (usar como referência, não copiar código)
- **Estado:** Muito activo

### Timesketch (Google)
- **URL:** https://github.com/google/timesketch
- **Stars:** 2.8K+
- **O que faz:** Análise colaborativa de timelines forenses; web UI; suporta múltiplas fontes
- **Porquê é crítico:** Gold standard para reconstrução de timelines. Correlação de eventos cross-domain.
- **Usar para:** Motor de timeline; interface de investigação colaborativa
- **Licença:** Apache 2.0
- **Estado:** Muito activo (Google)

### The Sleuth Kit + Autopsy
- **URL Sleuth Kit:** https://github.com/sleuthkit/sleuthkit — Stars: 3.1K
- **URL Autopsy:** https://github.com/sleuthkit/autopsy — Stars: 2.8K
- **O que faz:** Análise de volumes e file systems; recuperação de evidências de disk images. Autopsy é o GUI completo sobre TSK.
- **Porquê é crítico:** Standard da indústria em forense digital. Referência para o módulo de forense digital.
- **Usar para:** Backbone de forense digital; análise de disk images; file system analysis
- **Licença:** Open Source
- **Estado:** Activo (Basis Technology)

---

## TIER 2 — Especialistas por Domínio

### Volatility Framework
- **URL:** https://github.com/volatilityfoundation/volatility
- **Stars:** 6K+
- **O que faz:** Framework standard para memória forense; extrai artefactos digitais de dumps de RAM
- **Domínio:** Forense digital / endpoint
- **Licença:** Volatility License (open)
- **Estado:** Activo

### MVT — Mobile Verification Toolkit (Amnesty International)
- **URL:** https://github.com/mvt-project/mvt
- **Stars:** 2.5K+
- **O que faz:** Encontra sinais de comprometimento em Android/iOS; extracção forense de artefactos
- **Domínio:** Forense móvel
- **Licença:** MIT
- **Estado:** Muito activo

### SpiderFoot
- **URL:** https://github.com/smicallef/spiderfoot
- **Stars:** 10K+
- **O que faz:** Plataforma OSINT com 200+ módulos e web UI; automação de intelligence gathering
- **Domínio:** OSINT / Pesquisa em bases de dados abertas
- **Usar para:** Motor de pesquisa forense em fontes abertas (AI Research Engine)
- **Licença:** MIT
- **Estado:** Muito activo

### FraudEx
- **URL:** https://github.com/jayvaidya30/fraud-ex-stable
- **Stars:** 200+
- **O que faz:** Analisa documentos financeiros para detectar anomalias com AI explicável (XAI)
- **Domínio:** Forense financeiro
- **Usar para:** Módulo de forense financeiro; padrões de XAI (AI que explica as suas conclusões)
- **Licença:** Open
- **Estado:** Mantido

### Hayabusa (Yamato Security)
- **URL:** https://github.com/Yamato-Security/hayabusa
- **Stars:** 1.8K+
- **O que faz:** Gerador de timelines forenses para Windows event logs baseado em regras Sigma
- **Domínio:** Forense Windows / DFIR
- **Licença:** MIT
- **Estado:** Muito activo

---

## TIER 3 — AI/ML Específico

### Financial Anomaly Detection com DeepSeek + Isolation Forest
- **URL:** https://github.com/Jabonsote/Financial-Anomaly-Detection-with-DeepSeek-and-Isolation-Forest
- **Stars:** 80+
- **O que faz:** Isolation Forest + LLM local para detecção de anomalias; gera relatórios PDF de auditoria
- **Porquê relevante:** Padrão de integração LLM local (sem cloud) + análise financeira + PDF reports
- **Licença:** Open

### BlockLens
- **URL:** https://github.com/sejeeswarank/BlockLens
- **Stars:** 200+
- **O que faz:** Detecta se imagem é real, gerada por AI, editada, ou screenshot; verificação blockchain
- **Domínio:** Forense de imagem / médico-legal
- **Licença:** Open

### DeepForge
- **URL:** https://github.com/mwasifanwar/DeepForge
- **Stars:** 300+
- **O que faz:** Framework de detecção de deepfakes combinando ML ensemble com redes neuronais profundas
- **Domínio:** Forense de imagem / autenticidade de media
- **Licença:** Open

### ForensicSight (ACM Research)
- **URL:** https://github.com/ACM-Research/ForensicSight
- **Stars:** 60+
- **O que faz:** Computer Vision (YOLOv7) para detectar manchas de sangue em superfícies
- **Domínio:** Forense médico-legal (Computer Vision)
- **Licença:** Open

---

## Chain of Custody & Evidence Integrity

### 0xRuchiKaraShunti (CIDECODE 2.0 Winner)
- **URL:** https://github.com/Sampriti2803/0xRuchiKaraShunti
- **O que faz:** Dual storage (Local + IPFS), fuzzy hashing, blockchain privada com RBAC
- **Porquê relevante:** 4º lugar CIDECODE 2.0; cadeia de custódia imutável + detecção de adulteração
- **Usar para:** Referência para sistema de cadeia de custódia blockchain

### BCHOC — Blockchain Chain of Custody
- **URL:** https://github.com/chaincode-nc/BCHOC
- **Stars:** 300+
- **O que faz:** Formulário digital de cadeia de custódia em blockchain; check-in/out, dispose, destroy
- **Licença:** MIT

### EviGuard
- **URL:** https://github.com/NxOp/EviGuard
- **Stars:** 100+
- **O que faz:** Gestão de evidências digitais com interface para profissionais legais e peritos
- **Licença:** Open

---

## Datasets para Treino de IA

| Dataset | URL | O que contém | Para treinar |
|---|---|---|---|
| DFRWS 2006 Challenge | https://github.com/dfrws/dfrws2006-challenge | 50MB ficheiros reais (JPEG, ZIP, HTML, MS Office) — completos e fragmentados | File carving, detecção de tipos |
| FaceForensics++ | https://github.com/ondyari/FaceForensics | Vídeos reais e manipulados à larga escala | Detecção de deepfakes |
| CTF Forensics (Trail of Bits) | https://github.com/trailofbits/ctf | Desafios forenses com datasets e soluções | Treino geral, validação de modelos |
| CompDec (GovDocs) | https://github.com/AlexGustafsson/compdec | Detecção de algoritmos de compressão em fragmentos | Classificação forense de ficheiros |
| Graph Fraud Detection Papers | https://github.com/safe-graph/graph-fraud-detection-papers | Papers + datasets de Bitcoin forensics, fraude financeira | Forense financeiro, graph ML |

---

## OSINT & Investigação Web

| Ferramenta | URL | Stars | Para usar em |
|---|---|---|---|
| SpiderFoot | https://github.com/smicallef/spiderfoot | 10K+ | AI Research Engine (core) |
| theHarvester | https://github.com/laramies/theHarvester | 11K+ | Gathering emails, subdomínios, IPs |
| Recon-ng | https://github.com/lanmaster53/recon-ng | 4K+ | Reconnaissance modular |
| awesome-osint | https://github.com/jivoi/awesome-osint | 12K+ | Referência de ferramentas OSINT |

---

## Listas Curadas (Awesome Lists)

| Lista | URL | Stars | Valor |
|---|---|---|---|
| awesome-incident-response | https://github.com/meirwah/awesome-incident-response | 6K+ | 50+ ferramentas DFIR |
| awesome-osint | https://github.com/jivoi/awesome-osint | 12K+ | OSINT completo |
| awesome-memory-forensics | https://github.com/digitalisx/awesome-memory-forensics | 400+ | RAM analysis tools |
| awesome-pcaptools | https://github.com/caesar0301/awesome-pcaptools | 800+ | Network forensics |
| Awesome Deepfakes Detection | https://github.com/Daisy-Zhang/Awesome-Deepfakes-Detection | 1K+ | Detecção de deepfakes |
| Graph Fraud Detection Papers | https://github.com/safe-graph/graph-fraud-detection-papers | 2K+ | Forense financeiro + ML |

---

## Notas de Licenciamento

- **MIT / Apache 2.0** — Permissivo. Uso comercial autorizado. (SpiderFoot, Timesketch, Hayabusa, MVT)
- **GPL-3.0** — Copy-left. Cuidado com integração directa em produto fechado. (Live-Forensicator, IPED)
- **Proprietário** — Apenas referência de arquitectura, nunca copiar código. (AIFT, Forensic Explorer)
- **Open (sem licença clara)** — Verificar caso a caso antes de integrar.

---

*Gerado por SPEC-DRIVEN | Forense AI | 2026-05-29*
