# Spec: Platform Foundation

> Status: **Aprovada ✓**
> Clarificações: 2026-06-01
> Aprovação: 2026-06-02 — Argon2 + token rotation + TOTP confirmados pelo fundador
> Projecto: Forense AI
> Data: 2026-06-01
> Autor: SPEC-DRIVEN
> Pré-requisito de: Case Management · Evidence Ingestion · AI Research Engine · Report Generator

---

## Contexto

Toda a plataforma Forense AI assenta numa premissa de segurança: dados forenses são sensíveis e o acesso a eles é regulado por lei. Antes de qualquer funcionalidade operacional existir, a plataforma precisa de saber **quem está a aceder**, **de que organização**, e **com que permissões**.

O Platform Foundation resolve três problemas fundamentais:

1. **Identidade** — quem é este utilizador e a que organização pertence? Sem identidade verificada, o isolamento multi-tenant (RLS) não funciona.
2. **Acesso controlado** — nem todos os utilizadores podem fazer tudo. Um advogado não cria casos; um investigador não fecha casos. As permissões existem desde o primeiro login.
3. **Confiança legal** — uma plataforma forense usada em tribunal precisa de garantir que só pessoas autorizadas acederam a dados sensíveis. Logs de autenticação são parte da cadeia de custódia.

Esta feature é tecnicamente o **pré-requisito de todas as outras** — o JWT gerado aqui carrega o `organization_id` e `user_id` que o middleware de RLS usa para isolar dados entre organizações.

---

## Actores

| Actor | Papel |
|---|---|
| **Admin da Plataforma** | Gere instâncias de organizações a nível global (Anthropic/operador) |
| **Admin da Organização** | Cria e gere a organização, convida utilizadores, define papéis |
| **Utilizador** | Qualquer membro autenticado da organização |

---

## User Stories

### Story 1 (P0): Registo de Organização

Como **Admin da Plataforma**, quero **registar uma nova organização na plataforma** para que **essa organização tenha o seu espaço isolado e possa convidar a sua equipa**.

**Acceptance Criteria:**
- **Dado** que acedo ao endpoint de criação de organização com credenciais de plataforma
- **Quando** submeto nome, slug único, e email do primeiro admin
- **Então** a organização fica criada com espaço isolado, e o primeiro admin recebe convite por email (ou link copiável se email não configurado)
- **E então** a organização tem configuração de numeração de casos com formato padrão `FOR-YYYY-NNNNN`
- **E então** nenhum dado de outras organizações é acessível a partir deste espaço

---

### Story 2 (P0): Convite de Utilizadores

Como **Admin da Organização**, quero **convidar utilizadores por email com um papel predefinido** para que **só pessoas autorizadas tenham acesso e com as permissões certas desde o início**.

**Acceptance Criteria:**
- **Dado** que estou autenticado como Admin da minha organização
- **Quando** envio um convite com email e papel (perito, investigador, supervisor, advogado, consultor)
- **Então** o convidado recebe um link de convite com prazo de validade
- **E então** enquanto o convite não for aceite, o utilizador não existe na plataforma
- **E então** o convite expira ao fim do prazo e não pode ser reutilizado após expiração

- **Dado** que um convite está pendente
- **Quando** o Admin revoga o convite
- **Então** o link fica imediatamente inválido mesmo que ainda esteja dentro do prazo

✓ **Clarificado:** Prazo de convite é configurável por organização. Valor padrão: 7 dias.

---

### Story 3 (P0): Aceitação de Convite e Criação de Conta

Como **utilizador convidado**, quero **aceitar o meu convite e definir a minha password** para que **possa aceder à plataforma com a minha identidade verificada**.

**Acceptance Criteria:**
- **Dado** que tenho um link de convite válido
- **Quando** acedo ao link e defino a minha password
- **Então** a minha conta fica activa com o papel que o Admin definiu
- **E então** o link de convite fica inválido após uso (one-time)
- **E então** sou redirrecionado para o login após definir a password

- **Dado** que acedo a um link de convite já expirado
- **Quando** tento criar a conta
- **Então** recebo mensagem clara de que o convite expirou, com indicação para pedir novo convite ao Admin

---

### Story 4 (P0): Login

Como **qualquer utilizador**, quero **autenticar-me com email e password** para que **a plataforma confirme a minha identidade e me dê acesso ao meu espaço**.

**Acceptance Criteria:**
- **Dado** que tenho conta activa
- **Quando** introduzo email e password corretos
- **Então** recebo um access token (JWT) e um refresh token
- **E então** o JWT contém: `user_id`, `organization_id`, `global_role`, `exp`
- **E então** cada chamada à API com o JWT válido tem acesso ao espaço da minha organização

- **Dado** que introduzo password errada
- **Quando** excedo 5 tentativas falhadas
- **Então** a conta fica bloqueada temporariamente com mensagem de erro clara e sem revelar se o email existe

- **Dado** que sou Admin da Organização
- **Quando** faço login com sucesso
- **Então** sou obrigado a completar MFA antes de aceder (o JWT provisório não dá acesso até MFA estar completo)

---

### Story 5 (P0): MFA para Administradores

Como **Admin da Organização**, quero **configurar autenticação de dois factores** para que **o acesso à gestão da organização seja protegido contra comprometimento de password**.

**Acceptance Criteria:**
- **Dado** que sou Admin e ainda não tenho MFA activo
- **Quando** faço login pela primeira vez
- **Então** sou forçado a configurar MFA antes de qualquer outra acção (não é opcional)
- **E então** recebo um QR code para um autenticador TOTP (Google Authenticator, Authy, etc.)

- **Dado** que tenho MFA configurado
- **Quando** faço login com email + password corretos
- **Então** a plataforma pede o código TOTP de 6 dígitos
- **E então** só com código válido recebo o JWT com acesso completo

- **Dado** que perco acesso ao autenticador
- **Quando** tento recuperar
- **Então** o Admin da Plataforma pode revogar e repor o MFA (recovery flow via plataforma)

---

### Story 6 (P1): Refresh de Token

Como **qualquer utilizador autenticado**, quero **renovar o meu access token sem ter de fazer login de novo** para que **a minha sessão de trabalho não seja interrompida por expirações**.

**Acceptance Criteria:**
- **Dado** que o meu access token expirou mas o refresh token ainda é válido
- **Quando** a aplicação usa o refresh token para pedir novo access token
- **Então** recebo novo access token sem nova autenticação
- **E então** o refresh token de utilização única é substituído por um novo (rotation)

- **Dado** que o meu refresh token foi revogado (logout, suspeita de comprometimento)
- **Quando** a aplicação tenta usar o refresh token
- **Então** recebe erro e o utilizador é forçado a fazer login de novo

---

### Story 7 (P1): Gestão de Perfil

Como **qualquer utilizador**, quero **gerir o meu perfil** para que **a minha identidade na plataforma esteja correcta e a minha password segura**.

**Acceptance Criteria:**
- **Dado** que estou autenticado
- **Quando** acedo ao meu perfil
- **Então** posso alterar: nome de exibição, password (requer password actual)
- **E então** não posso alterar o meu email (é o identificador permanente) nem o meu papel (apenas Admin pode)

---

### Story 8 (P1): Gestão de Utilizadores pela Organização

Como **Admin da Organização**, quero **gerir os utilizadores da minha organização** para que **tenha controlo sobre quem tem acesso e com que permissões**.

**Acceptance Criteria:**
- **Dado** que sou Admin
- **Quando** acedo à gestão de utilizadores
- **Então** vejo todos os membros activos, membros suspensos, e convites pendentes

- **Dado** que quero alterar o papel de um utilizador
- **Quando** mudo o papel
- **Então** a mudança é imediata — o utilizador vê as novas permissões na próxima acção

- **Dado** que quero suspender um utilizador
- **Quando** suspendo
- **Então** os tokens activos do utilizador são revogados imediatamente — não consegue fazer mais nenhuma chamada à API

---

### Story 9 (P2): Recuperação de Password

Como **utilizador que perdeu acesso**, quero **recuperar a minha password** para que **não fique permanentemente bloqueado da plataforma**.

**Acceptance Criteria:**
- **Dado** que peço recuperação de password
- **Quando** introduzo o meu email
- **Então** recebo resposta neutra ("se este email existir, receberás instruções") — nunca confirma se o email existe
- **E então** se o email existir, recebo link one-time com prazo de 1 hora
- **E então** após definir nova password, todos os refresh tokens activos são revogados (força login em todos os dispositivos)

---

## Requisitos Funcionais

- DEVE gerar JWT com `user_id`, `organization_id`, `global_role`, `exp` em todos os tokens de acesso
- DEVE garantir que o acesso Admin sem MFA configurado é impossível após o primeiro login
- DEVE revogar imediatamente todos os tokens de um utilizador suspenso ou com password alterada
- DEVE bloquear temporariamente após 5 tentativas de login falhadas consecutivas
- DEVE usar refresh token rotation — cada refresh consome o token e emite um novo
- DEVE registar em audit log todos os eventos de autenticação: login, logout, falha, MFA, convite, suspensão
- DEVE suportar convites one-time com prazo de validade
- PODE ter MFA recomendado (não obrigatório) para papéis não-admin
- NÃO DEVE revelar se um email existe na plataforma em qualquer mensagem de erro
- NÃO DEVE armazenar passwords em texto claro — hashing com algoritmo moderno (bcrypt ou Argon2)
- NÃO DEVE emitir JWT sem `organization_id` válido — é o alicerce do RLS

---

## Entidades de Dados

- **Organização**: já definida no data model de Case Management
- **Utilizador**: já definido — adicionar campos: `password_hash`, `mfa_secret` (encriptado), `mfa_enabled`, `failed_login_attempts`, `locked_until`, `last_login_at`
- **Convite**: token one-time, email, papel, organização, criado por, expira em, usado em (nullable)
- **Refresh Token**: token hash, utilizador, expira em, revogado em (nullable), substituído por (nullable — para rotation chain)
- **Audit Auth Log**: evento (login/logout/fail/mfa/convite/suspensão), utilizador, ip, timestamp, metadata

---

## Edge Cases

- Utilizador tenta usar convite depois de já ter conta — deve ser rejeitado com mensagem clara
- Admin tenta suspender-se a si próprio — deve ser rejeitado (a organização ficaria sem admin)
- Último admin da organização tenta abandonar o papel — deve ser rejeitado
- MFA com código de recuperação (backup codes) — `[NEEDS CLARIFICATION]`
- Login em múltiplos dispositivos em simultâneo — cada dispositivo tem o seu par de tokens, todos válidos até revogação explícita

---

## Pressupostos

- Email é o identificador único e permanente de um utilizador dentro da plataforma
- Um utilizador pertence a uma única organização (sem multi-org por utilizador nesta versão)
- MFA é TOTP — não SMS (SMS é inseguro por SIM swapping, especialmente crítico em contexto forense)
- Os papéis globais são fixos nesta versão: admin, perito, investigador, supervisor, advogado, consultor

---

## Fora de Âmbito

- SSO / SAML / OAuth social login — roadmap futuro
- Billing e subscrições — roadmap futuro
- API keys para integrações máquina-a-máquina — spec separada
- Multi-organização por utilizador — roadmap futuro
- Auditoria avançada de sessões (quais IPs acederam, mapa geográfico) — roadmap futuro

---

## Critérios de Sucesso

- O JWT emitido pelo login contém `organization_id` válido — o middleware RLS do Case Management aceita-o sem modificações
- Um Admin sem MFA não consegue executar nenhuma operação na API após o primeiro login
- Um utilizador suspenso fica incapaz de fazer qualquer chamada à API em menos de 1 segundo após suspensão
- Um utilizador de organização A não consegue obter nenhum dado de organização B — em nenhum endpoint
- Todos os eventos de autenticação aparecem no audit log sem excepções

---

## Quality Checklist

- [x] Spec descreve WHAT e WHY — sem HOW
- [x] Todos os requisitos são testáveis
- [x] Critérios de sucesso são mensuráveis
- [x] Máximo 3 `[NEEDS CLARIFICATION]` — total: 2
- [x] Nenhum detalhe de implementação
- [ ] Aprovada pelo utilizador antes de passar a plan.md

---

## Pontos `[NEEDS CLARIFICATION]`

1. **Prazo de convites** *(Story 2)* — 48 horas, 7 dias, ou configurável por organização?

2. **MFA backup codes** ✓ **Clarificado:** O sistema gera 8 códigos de recuperação one-time no momento de configuração do MFA. Cada código é de uso único. Após uso, o código fica inválido. O Admin pode regenerar o conjunto completo (invalida os anteriores) mediante autenticação.

---

*Gerado por SPEC-DRIVEN | spec-kit methodology | Forense AI*
