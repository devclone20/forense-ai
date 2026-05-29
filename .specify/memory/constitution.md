# Constituição do Projecto — Forense AI

> Gerado por SPEC-DRIVEN em 2026-05-29
> Stack: A definir (novo projecto)

**Estes artigos são invioláveis. Nenhum agente pode violar a Constituição.**

---

## Artigo 1 — Padrão World-Class

Todo o código, design, e decisão de arquitectura deve atingir o padrão que resistiria à auditoria dos melhores engenheiros do mundo. Se alguém auditasse este codebase para comprar a empresa, não encontraria nada para ter vergonha.

*Consequência de violação:* Rejeição imediata. Retrabalho obrigatório.

---

## Artigo 2 — Segurança Primeiro

Segurança não é uma fase posterior. É uma restrição de design desde o primeiro commit. Dados forenses são sensíveis por natureza — qualquer exposição pode comprometer investigações reais. Nenhuma feature vai para produção sem passar por hm-security. OWASP Top 10 2025 é o baseline mínimo.

*Consequência de violação:* HALT. Nenhum deploy até resolução.

---

## Artigo 3 — Spec Antes de Código

Nenhum agente começa a implementar sem spec.md aprovada. A spec descreve O QUÊ e PORQUÊ — nunca COMO. Detalhes técnicos pertencem ao plan.md.

*Consequência de violação:* HALT. Criar spec primeiro.

---

## Artigo 4 — Test-First

Testes são escritos antes do código de produção. Red → Green → Refactor. Sem testes aprovados, o código não existe.

*Consequência de violação:* PR rejeitado.

---

## Artigo 5 — Design Editorial

Interfaces seguem os padrões: Apple, Airbnb, Linear, Stripe, Vercel. Dark-first. Tipografia editorial. Sensibilidade cinematográfica. Se parece um template, reprovou. Se poderia pertencer a qualquer produto, reprovou.

*Consequência de violação:* hm-designer rejeita. Redesign obrigatório.

---

## Artigo 6 — Integridade de Evidências

A cadeia de custódia digital é sagrada. Toda a evidência ingerida deve ser imutável após registo — hash SHA-256 no momento de ingestão, timestamps auditáveis, log de acesso completo. Nenhuma modificação de evidência sem registo de quem, quando, e porquê.

*Consequência de violação:* A plataforma perde credibilidade legal. HALT imediato.

---

## Artigo 7 — Rastreabilidade de IA

Toda a análise produzida por IA deve ser rastreável à fonte. Cada conclusão deve citar as evidências que a suportam. O sistema nunca produz "factos" sem fonte verificável. Modelos de IA são auxiliares — nunca autoridade final.

*Consequência de violação:* Resultados de IA sem fonte são removidos imediatamente.

---

## Artigo 8 — Multi-Domínio por Design

A arquitectura suporta nativamente múltiplos domínios forenses (digital, médico-legal, financeiro). Nenhuma decisão técnica pode optimizar para um domínio à custa de outro. O sistema é extensível para novos domínios sem reescritas.

*Consequência de violação:* Arquitectura recusada. Redesign obrigatório.

---

## Artigo 9 — Aprendizagem Contínua

Cada sessão termina com `/spec-driven:train`. O sistema aprende com cada projecto. As aprendizagens globais são lidas no início de cada nova feature.

*Consequência de violação:* O sistema não evolui. Erros repetem-se.

---

## Histórico de Revisões

| Data | Versão | Alteração |
|---|---|---|
| 2026-05-29 | 1.0 | Constituição inicial |
