# Spec: Evidence Ingestion

> Status: **Aprovada ✓**
> Clarificações: 2026-06-02
> Aprovação: 2026-06-02
> Projecto: Forense AI
> Data: 2026-06-02
> Autor: SPEC-DRIVEN
> Depende de: Platform Foundation (auth) · Case Management (casos)
> Consumida por: AI Research Engine · Report Generator

---

## Contexto

Uma investigação forense é tão forte quanto as evidências que a suportam. O problema não é recolher evidências — os peritos já sabem fazê-lo. O problema é **o que acontece depois**: ficheiros perdidos em pastas de email, discos externos sem inventário, imagens sem data de recolha, documentos sem registo de quem os tocou.

Quando um processo vai a tribunal, a defesa ataca a cadeia de custódia. Se não se consegue provar que uma evidência não foi alterada entre a recolha e a apresentação em tribunal, perde-se o caso. Este módulo existe para tornar essa prova irrefutável.

A Evidence Ingestion resolve três problemas concretos:

1. **Integridade** — cada evidência tem um fingerprint criptográfico gerado no momento exacto de entrada no sistema. Qualquer alteração subsequente é detectável.
2. **Rastreabilidade** — sabe-se exactamente quem registou, quando, a partir de que dispositivo, e todos os acessos posteriores.
3. **Catalogação** — evidências têm metadata estruturada que permite pesquisa, filtro e ligação à análise com IA posterior.

Este módulo é o pré-requisito do AI Research Engine e do Report Generator — nenhuma análise ou relatório pode existir sem evidências registadas.

---

## Actores

| Actor | Papel |
|---|---|
| **Investigador** | Regista evidências nos casos a que está atribuído |
| **Perito Forense** | Regista evidências, valida integridade, gere o inventário do caso |
| **Supervisor / Magistrado** | Consulta evidências em modo de leitura, verifica integridade |
| **Advogado / Consultor** | Consulta evidências autorizadas em modo de leitura |

---

## User Stories

### Story 1 (P0): Registar Evidência por Upload

Como **Investigador ou Perito Forense**, quero **fazer upload de um ficheiro como evidência de um caso** para que **fique permanentemente registado com o seu fingerprint e metadata, ligado ao processo de investigação**.

**Acceptance Criteria:**
- **Dado** que estou autenticado e atribuído ao caso
- **Quando** faço upload de um ficheiro
- **Então** o sistema calcula o hash SHA-256 do ficheiro **no servidor, após recepção completa**
- **E então** a evidência fica registada com: número de evidência único (ex: `EV-001`), nome original do ficheiro, tamanho, tipo MIME, hash SHA-256, timestamp de ingestão, quem registou
- **E então** o ficheiro original é armazenado de forma imutável — não pode ser substituído, editado, ou apagado
- **E então** o evento de ingestão é registado no audit log do caso

- **Dado** que faço upload de um ficheiro já registado neste caso (mesmo hash SHA-256)
- **Quando** o sistema detecta o duplicado
- **Então** avisa que este ficheiro já existe como `EV-XXX` e pede confirmação antes de registar como cópia separada

---

### Story 2 (P0): Metadata e Classificação

Como **Investigador ou Perito Forense**, quero **classificar e descrever uma evidência no momento de registo** para que **qualquer membro da equipa perceba o contexto sem ter de abrir o ficheiro**.

**Acceptance Criteria:**
- **Dado** que estou a registar uma evidência
- **Quando** preencho a metadata
- **Então** posso definir: título descritivo, tipo de evidência (ver taxonomia abaixo), descrição livre, fonte/origem da recolha, data de recolha (pode ser diferente da data de ingestão), tags
- **E então** o tipo de evidência determina campos adicionais opcionais específicos do domínio forense do caso

**Taxonomia de tipos de evidência:**
- **Digital:** ficheiro de sistema, imagem de disco, dump de memória, log de sistema, capture de rede (PCAP), artefacto de browser, registo de sistema operativo, email/mensagem
- **Médico-Legal:** relatório médico, fotografia forense, resultado laboratorial, registo hospitalar, laudo pericial
- **Financeiro:** extracto bancário, factura/recibo, contrato, registo de transacção, comunicação financeira, relatório contabilístico

---

### Story 3 (P0): Verificação de Integridade

Como **Perito Forense ou Supervisor**, quero **verificar que uma evidência não foi alterada desde o registo** para que **possa afirmar com certeza perante o tribunal que a evidência é autêntica**.

**Acceptance Criteria:**
- **Dado** que acedo a uma evidência registada
- **Quando** clico em "Verificar Integridade"
- **Então** o sistema recalcula o hash SHA-256 do ficheiro armazenado e compara com o hash registado no momento de ingestão
- **E então** mostra o resultado: ✅ **Íntegra** (hashes coincidem) ou ❌ **ADULTERADA** (hashes divergem)
- **E então** o resultado da verificação fica registado no audit log com timestamp

- **Dado** que o hash diverge
- **Quando** o sistema detecta adulteração
- **Então** alerta imediato visível para todos os membros do caso — não apenas para quem verificou

---

### Story 4 (P1): Inventário de Evidências do Caso

Como **qualquer membro do caso**, quero **ver todas as evidências registadas num caso** para que **tenha uma visão completa do que está disponível para a investigação**.

**Acceptance Criteria:**
- **Dado** que acedo ao detalhe de um caso
- **Quando** navego para o inventário de evidências
- **Então** vejo lista com: número, título, tipo, tamanho, quem registou, data de ingestão, estado de integridade
- **E então** posso filtrar por: tipo de evidência, data, quem registou, estado de integridade
- **E então** posso ordenar por: data de ingestão, número, tamanho

---

### Story 5 (P1): Detalhe e Download de Evidência

Como **qualquer membro do caso**, quero **aceder ao detalhe de uma evidência e descarregar o ficheiro original** para que **possa analisá-lo com as ferramentas adequadas**.

**Acceptance Criteria:**
- **Dado** que acedo ao detalhe de uma evidência
- **Quando** a página carrega
- **Então** vejo: toda a metadata, hash SHA-256 (visível e copiável), histórico completo de acessos, estado de integridade
- **E então** cada download é registado no audit log (quem, quando, IP)

- **Dado** que faço download de uma evidência
- **Quando** o ficheiro chega ao meu dispositivo
- **Então** o nome do ficheiro descarregado inclui o número de evidência (ex: `EV-001_nome_original.ext`) para rastreabilidade

---

### Story 6 (P2): Cadeia de Custódia Exportável

Como **Perito Forense**, quero **exportar a cadeia de custódia de uma evidência ou de todo o caso** para que **possa apresentar um documento formal e verificável em contexto legal**.

**Acceptance Criteria:**
- **Dado** que acedo ao inventário de evidências de um caso
- **Quando** exporto a cadeia de custódia
- **Então** recebo um documento (PDF ou CSV) com: todas as evidências, hashes, timestamps de ingestão, histórico completo de acessos e verificações, assinatura digital do documento (HMAC, à semelhança do audit log)

- **Dado** que o documento de cadeia de custódia é gerado
- **Quando** qualquer pessoa verifica a assinatura
- **Então** consegue confirmar que o documento não foi modificado após exportação

---

## Requisitos Funcionais

- DEVE calcular o hash SHA-256 **no servidor** após recepção completa do ficheiro — nunca confiar em hash calculado pelo cliente
- DEVE tornar o ficheiro imutável após ingestão — sem overwrite, sem delete, sem edit
- DEVE registar no audit log do caso: ingestão, cada acesso, cada download, cada verificação de integridade
- DEVE gerar número de evidência sequencial e único por caso: `EV-001`, `EV-002`, etc.
- DEVE suportar os três domínios forenses com campos de metadata específicos por domínio
- DEVE detectar e alertar para ficheiros duplicados (mesmo hash SHA-256) dentro do mesmo caso
- DEVE permitir verificação de integridade a qualquer momento por qualquer membro do caso
- DEVE registar o resultado de cada verificação de integridade no audit log
- PODE gerar thumbnail para imagens no momento de ingestão (para preview sem download)
- NÃO DEVE permitir que um ficheiro armazenado seja modificado ou eliminado por qualquer utilizador — incluindo admins
- NÃO DEVE expor o URL directo de armazenamento — todos os acessos são mediados pela API com autenticação
- DEVE suportar múltiplos backends de armazenamento (local, S3-compatible) através de uma interface plugável — a escolha é feita pelo Admin no onboarding
- DEVE apresentar ao Admin, no onboarding da organização, as opções de armazenamento disponíveis e solicitar a configuração de limites (por ficheiro e quota total)
- DEVE mostrar em tempo real a ocupação actual vs quota da organização
- DEVE alertar o Admin quando a quota atingir 90% de utilização
- NÃO DEVE aceitar uploads que excedam o limite por ficheiro configurado pela organização — com mensagem de erro clara antes do upload começar

✓ **Clarificado — Armazenamento configurável pelo utilizador:** A plataforma não impõe um backend de armazenamento. No momento de configurar o projecto (organização), o sistema pergunta ao utilizador onde quer guardar as evidências e apresenta as opções disponíveis. A arquitectura é plugável — o utilizador escolhe, a plataforma adapta-se.

**Opções de armazenamento suportadas (apresentadas ao utilizador no onboarding):**
- **Local** — filesystem do servidor (instalações próprias, air-gapped)
- **S3-compatible** — AWS S3, Cloudflare R2, MinIO (auto-hospedado), Wasabi
- **Local + Replicação** — filesystem primário com backup para S3-compatible

A escolha fica registada nas configurações da organização e pode ser migrada futuramente.

✓ **Clarificado — Limite de tamanho configurável pelo utilizador:** No onboarding (ou nas definições da organização), o Admin define os limites de capacidade da sua organização. A plataforma pergunta e sugere valores razoáveis por contexto:
- **Limite por ficheiro** — o Admin define (ex: 500MB, 10GB, 100GB, sem limite)
- **Quota total da organização** — o Admin define a capacidade total
- A plataforma mostra ocupação actual vs quota em tempo real
- Quando a quota está a 90%, o Admin recebe alerta proactivo

---

## Entidades de Dados

- **Evidência**: id, número (`EV-NNN`), caso, título, descrição, tipo de evidência, subtipo/domínio, ficheiro original (referência de armazenamento), nome original, tamanho em bytes, tipo MIME, hash SHA-256, fonte/origem, data de recolha, registado por, registado em, tags, metadata_domínio JSONB
- **Evento de Evidência**: evidência, tipo de evento (ingestão/acesso/download/verificação/alerta), actor, ip, timestamp, resultado (para verificações), metadata
- **Resultado de Verificação de Integridade**: evidência, verificado por, timestamp, hash recalculado, hash original, resultado (íntegra/adulterada)
- **Configuração de Storage da Organização**: organização, backend (local/s3/local+s3), credenciais encriptadas (bucket, region, access key), limite por ficheiro em bytes, quota total em bytes, bytes utilizados actual, alerta de quota enviado em

---

## Edge Cases

- Upload interrompido a meio — o ficheiro parcial não deve ser registado como evidência
- Ficheiro corrompido durante armazenamento — a verificação de integridade posterior detecta e alerta
- Dois investigadores fazem upload do mesmo ficheiro em simultâneo — ambos completam, sistema detecta duplicado e regista ambos com aviso
- Caso fechado — ainda é possível consultar e verificar evidências, mas não registar novas sem reabrir o caso
- Acesso a evidência de caso ao qual o utilizador não pertence — negado a nível de RLS + API

---

## Pressupostos

- Um ficheiro registado como evidência nunca é eliminado — mesmo que o caso seja arquivado
- O hash SHA-256 é calculado no servidor sobre o conteúdo binário exacto do ficheiro
- A numeração `EV-NNN` é sequencial por caso (não global) e não tem lacunas visíveis ao utilizador
- Metadata de domínio (campos específicos de Digital vs Médico-Legal vs Financeiro) é opcional — o utilizador pode registar sem preencher campos específicos

---

## Fora de Âmbito

- Análise automática do conteúdo das evidências com IA — spec `ai-research-engine`
- Geração de relatórios periciais — spec `report-generator`
- Preview inline de ficheiros dentro da plataforma (visualizador de PDF, player de vídeo) — roadmap futuro
- Sincronização com dispositivos externos (câmeras forenses, kits de extracção) — roadmap futuro
- Encriptação das evidências em repouso — roadmap futuro (depende de decisão sobre armazenamento)

---

## Critérios de Sucesso

- O hash SHA-256 de uma evidência registada nunca muda — verificável a qualquer momento
- A cadeia de custódia mostra **todos** os acessos sem excepção — incluindo visualizações e downloads
- Um utilizador sem acesso ao caso não consegue aceder a nenhuma evidência — em nenhum endpoint
- A verificação de integridade de um ficheiro de 1GB completa em menos de 30 segundos
- O inventário de evidências de um caso com 500 itens carrega em menos de 1 segundo

---

## Quality Checklist

- [x] Spec descreve WHAT e WHY — sem HOW
- [x] Todos os requisitos são testáveis
- [x] Critérios de sucesso são mensuráveis
- [x] Máximo 3 `[NEEDS CLARIFICATION]` — todos resolvidos ✓
- [x] Nenhum detalhe de implementação
- [ ] Aprovada pelo utilizador antes de passar a plan.md

---

*Gerado por SPEC-DRIVEN | spec-kit methodology | Forense AI*
