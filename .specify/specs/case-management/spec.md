# Spec: Case Management

> Status: **Aprovada ✓**
> Aprovação: 2026-05-29 — Decisões técnicas confirmadas pelo fundador
> Projecto: Forense AI
> Data: 2026-05-29
> Autor: SPEC-DRIVEN

---

## Contexto

Uma investigação forense é composta por múltiplas evidências, múltiplos intervenientes, e múltiplas fases ao longo do tempo. Sem um sistema central que organize e rastreie esta informação, os peritos trabalham em silos, duplicam esforço, e perdem contexto crítico entre sessões de trabalho.

O módulo de Case Management é o núcleo da plataforma Forense AI. Todo o restante — ingestão de evidências, análise com IA, geração de relatórios — orbita em torno de um caso. Um caso é a unidade de organização fundamental. Sem ele, nada tem contexto.

Este módulo resolve três problemas concretos:
1. **Fragmentação** — investigadores perdem-se entre ficheiros, emails e notas avulsas
2. **Falta de rastreabilidade** — não é possível saber quem fez o quê e quando num processo
3. **Colaboração difícil** — partilha de informação entre peritos, magistrados e advogados é manual e insegura

---

## Actores

| Actor | Papel |
|---|---|
| **Perito Forense** | Cria casos, gere investigações, atribui equipa |
| **Investigador** | Trabalha em casos atribuídos, adiciona informação |
| **Supervisor / Magistrado** | Revisa casos, aprova estados, acesso de leitura alargado |
| **Advogado** | Acesso de leitura a casos específicos autorizados |
| **Administrador** | Gere a plataforma, utilizadores e permissões |

---

## User Stories

### Story 1 (P0): Criação de Caso

Como **Perito Forense**, quero **criar um novo caso de investigação e definir o seu contexto inicial** para que **toda a equipa trabalhe com o mesmo enquadramento desde o início**.

**Acceptance Criteria:**
- **Dado** que estou autenticado como Perito Forense
- **Quando** crio um novo caso com título, domínio forense, e descrição
- **Então** o caso fica criado com um número único gerado automaticamente, estado "Aberto", timestamp de criação, e eu fico automaticamente atribuído como responsável

- **Dado** que estou a criar um caso
- **Quando** selecciono o domínio forense
- **Então** posso escolher entre: Digital, Médico-Legal, Financeiro — e o caso fica marcado com esse domínio (afecta templates, análises, e relatórios disponíveis)

- **Dado** que um caso foi criado
- **Quando** qualquer utilizador o consulta
- **Então** o número do caso, data de criação, responsável, domínio, e estado são sempre visíveis

---

### Story 2 (P0): Gestão de Estado do Caso

Como **Perito Forense**, quero **actualizar o estado de um caso** para que **todos os intervenientes saibam em que fase da investigação está**.

**Acceptance Criteria:**
- **Dado** que sou o responsável de um caso
- **Quando** altero o estado do caso
- **Então** posso transitar entre: `Aberto → Em Investigação → Em Revisão → Fechado → Arquivado`
- **E então** cada transição fica registada no log do caso com: quem alterou, quando, e estado anterior/novo
- **E então** transições para trás (ex: Fechado → Em Investigação) são possíveis mas requerem justificação obrigatória

- **Dado** que um caso está "Fechado"
- **Quando** tento adicionar nova evidência
- **Então** o sistema avisa que o caso está fechado e exige reabertura antes de continuar

---

### Story 3 (P1): Atribuição de Equipa

Como **Perito Forense** (responsável do caso), quero **atribuir membros de equipa ao caso com papéis específicos** para que **cada pessoa tenha acesso exactamente ao que precisa — nem mais, nem menos**.

**Acceptance Criteria:**
- **Dado** que sou responsável de um caso
- **Quando** adiciono um utilizador ao caso
- **Então** defino o seu papel neste caso: Investigador, Supervisor, ou Consultor (acesso de leitura)
- **E então** o utilizador recebe notificação da atribuição
- **E então** os seus privilégios são imediatamente limitados ao papel definido para este caso

- **Dado** que um utilizador foi removido de um caso
- **Quando** tenta aceder ao caso
- **Então** não tem acesso — mas o registo histórico da sua participação fica preservado no log de auditoria

✓ **Clarificado:** A atribuição é sempre por utilizador individual. Grupos não estão no âmbito.

---

### Story 4 (P1): Pesquisa e Filtros de Casos

Como **qualquer utilizador autenticado**, quero **pesquisar e filtrar os casos a que tenho acesso** para que **encontre rapidamente o processo certo sem navegar em listas longas**.

**Acceptance Criteria:**
- **Dado** que estou autenticado
- **Quando** acedo à lista de casos
- **Então** vejo apenas os casos a que tenho acesso (os meus + os que me foram atribuídos)

- **Dado** que estou na lista de casos
- **Quando** aplico filtros
- **Então** posso filtrar por: estado, domínio forense, responsável, intervalo de datas, e número do caso

- **Dado** que pesquiso por texto livre
- **Quando** digito um termo
- **Então** a pesquisa cobre: título do caso, número, descrição, e tags associadas

---

### Story 5 (P1): Log de Actividade do Caso

Como **Supervisor / Magistrado**, quero **consultar o histórico completo de actividade de um caso** para que **possa auditar tudo o que aconteceu na investigação, por quem e quando**.

**Acceptance Criteria:**
- **Dado** que acedo a um caso
- **Quando** consulto o log de actividade
- **Então** vejo uma timeline cronológica com: criação, alterações de estado, adições de equipa, ingestões de evidência, análises executadas, e relatórios gerados
- **E então** cada entrada mostra: actor, acção, timestamp, e dados relevantes

- **Dado** que sou Administrador
- **Quando** exporto o log de auditoria
- **Então** recebo um ficheiro com integridade verificável (não manipulável após exportação)

---

### Story 6 (P2): Visão Dashboard de Casos

Como **Perito Forense**, quero **ver um dashboard com o estado dos meus casos activos** para que **não perca prazos nem deixe casos sem progressão**.

**Acceptance Criteria:**
- **Dado** que acedo ao dashboard
- **Quando** o dashboard carrega
- **Então** vejo: casos por estado (contagens), casos sem actividade nos últimos N dias, e casos atribuídos a mim por prioridade

- **Dado** que clico num caso no dashboard
- **Quando** navego para o caso
- **Então** acedo directamente ao detalhe do caso sem passos intermédios

---

## Requisitos Funcionais

- DEVE gerar automaticamente um número único por caso no momento de criação, no formato `FOR-YYYY-NNNNN` por defeito
- DEVE suportar formatos de numeração configuráveis por organização (motor de numeração extensível sem reescrita)
- DEVE garantir isolamento total de dados entre organizações — uma organização nunca acede a dados de outra (multi-tenancy)
- DEVE registar em log imutável toda a actividade do caso (quem, o quê, quando)
- DEVE suportar os três domínios forenses: Digital, Médico-Legal, Financeiro
- DEVE aplicar controlo de acesso por caso — um utilizador só vê os casos a que tem acesso
- DEVE manter histórico de todas as transições de estado com justificação quando aplicável
- DEVE suportar pesquisa e filtros sobre a lista de casos
- PODE ter campos personalizáveis por domínio forense (campos relevantes para Financeiro diferem de Digital)
- NÃO DEVE permitir eliminação de casos — apenas arquivamento
- NÃO DEVE permitir modificação retroactiva do log de actividade

---

## Entidades de Dados

- **Organização**: identificador único, nome, configuração de numeração de casos (formato, prefixo, contador actual), utilizadores membros
- **Caso**: identificador único, número de caso (formato configurável, único dentro da organização), organização, título, descrição, domínio forense, estado, data de criação, data de última actualização, responsável, classificação de confidencialidade, tags
- **Estado do Caso**: valor do estado, actor que alterou, timestamp, estado anterior, justificação (obrigatória em certas transições)
- **Membro do Caso**: utilizador, papel no caso, data de atribuição, atribuído por, data de remoção (se aplicável)
- **Log de Actividade**: entrada de log, tipo de acção, actor, timestamp, dados da acção (imutável)
- **Utilizador**: identidade, papel global na plataforma, casos atribuídos

---

## Edge Cases

- Criação de caso sem título — DEVE ser bloqueada com mensagem de erro clara
- Utilizador tenta alterar estado de caso ao qual não é responsável — DEVE ser rejeitado com mensagem de permissão
- Dois utilizadores alteram o mesmo caso simultaneamente — última escrita vence com registo de ambas no log
- Caso arquivado acedido — DEVE ser visível em modo de leitura, nunca editável sem desarquivamento explícito
- Pesquisa com termos que não retornam resultados — DEVE apresentar estado vazio informativo, não erro
- Utilizador removido de caso tenta aceder — acesso negado, mas participação histórica preservada

---

## Pressupostos

- Autenticação de utilizadores existe como pré-condição (plataforma tem sistema de auth funcional)
- Um utilizador pode estar em múltiplos casos com papéis diferentes em cada
- O número de caso é único globalmente na plataforma (não por domínio)
- O log de actividade é append-only por design — nenhuma entrada pode ser modificada ou apagada

---

## Fora de Âmbito

- Ingestão de evidências e ligação de ficheiros a casos — tratado em spec `evidence-ingestion`
- Análise com IA das evidências — tratado em spec `ai-analysis-engine`
- Geração de relatórios periciais — tratado em spec `report-generator`
- Notificações por email/push — pode ser incluído numa iteração futura
- Integração com sistemas externos (e.g. sistemas judiciais) — roadmap futuro
- Gestão de utilizadores e administração de conta — tratado em spec `platform-foundation`

---

## Critérios de Sucesso

- Um perito consegue criar um novo caso, atribuir dois investigadores, e mudar o estado em menos de 2 minutos
- O log de actividade mostra 100% das acções executadas num caso, sem excepções
- Um utilizador sem acesso a um caso não consegue aceder ao mesmo — em nenhuma rota, endpoint, ou pesquisa
- A pesquisa de casos retorna resultados em menos de 500ms para bibliotecas com até 10.000 casos
- Todos os campos obrigatórios têm validação — nenhum caso inválido pode ser criado

---

## Quality Checklist

- [x] Spec descreve WHAT e WHY — sem HOW (sem frameworks, linguagens, APIs)
- [x] Todos os requisitos são testáveis
- [x] Success criteria são mensuráveis
- [x] Máximo 3 `[NEEDS CLARIFICATION]` — todos resolvidos ✓
- [x] Nenhum detalhe de implementação
- [ ] Aprovada pelo utilizador antes de passar a plan.md

---

## Clarificações Resolvidas

1. **Atribuição de equipa** — Individual. Sem grupos no âmbito desta spec.

✓ **Clarificado:** Formato padrão: `FOR-YYYY-NNNNN` (ex: `FOR-2026-00001`). O sistema de numeração é configurável por organização — o formato padrão é o acima, mas a plataforma deve suportar formatos alternativos definíveis no futuro sem reescrita do motor de numeração.

✓ **Clarificado:** Multi-tenancy — instância partilhada entre organizações. Cada organização tem o seu espaço isolado (dados, casos, utilizadores), mas correm na mesma infra. Isolamento de dados é obrigatório: uma organização nunca acede a dados de outra.

---

*Gerado por SPEC-DRIVEN | spec-kit methodology | Forense AI*
