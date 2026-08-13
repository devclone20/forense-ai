# Skills

The canonical **EconomyOS skill pack** — everything this agent needs to operate the
agent economies: Virtuals Protocol ACP, OKX Onchain OS, and Robinhood Chain. One list,
one format, no duplicates; the same pack ships in every devclone20 agent monorepo.

Load `agentic-economy` first — it is the map and the law; every other skill is loaded
from it by situation.

## The pack

| Skill | What it carries |
|---|---|
| [`agentic-economy`](agentic-economy/SKILL.md) | **The router.** The map of the three economies, the law (*you operate, the owner spends*), unit traps per stack, and the open-protocol stack (ERC-8004 · A2A · MCP · x402 · ERC-6551 · AP2) with corrections. Zero commands by design. |
| [`virtuals-cli`](virtuals-cli/SKILL.md) | The `acp` CLI manual (@virtuals-protocol/acp-cli): auth split-flow, agent + signer creation, wallet policies, offerings, the job lifecycle with USDC escrow, events, and the agent rails (wallet · email · card · compute · trade). |
| [`acp-marketplace-earner`](acp-marketplace-earner/SKILL.md) | Earning as a **provider**: scan → score (0–100) → negotiate → execute with proof → deliver → confirm settlement, under a budget governor with a kill-switch. |
| [`acp-fixed-price-buyer`](acp-fixed-price-buyer/SKILL.md) | Buying as a **client**: create job → budget handshake → fund escrow → verify on-chain → settle or reject. Written from a real trade. |
| [`acp-paid-subscription-checkout`](acp-paid-subscription-checkout/SKILL.md) | Spending with the agent's own identity: agent email + single-use agent card, 3DS, receipt and paid-access verification. Live-money flow — every stop condition spelled out. |
| [`acp-troubleshooting`](acp-troubleshooting/SKILL.md) | The field guide: 26 production-validated errors (E1–E26) with exact error strings, root causes and fixes; headless/server deploy; both offering schemas. |
| [`acp-builder-setup`](acp-builder-setup/SKILL.md) | Installing ACP skills into a runtime (Claude Code · Codex · Claude Desktop) and optionally routing inference through Virtuals hosted models. |
| [`okx-cli`](okx-cli/SKILL.md) | The `onchainos` CLI manual (OKX Onchain OS): wallet login, portfolio, swaps and bridges, DeFi, ERC-8004 identity + task marketplace, x402 payments, security scanners — and the worst unit traps of the three stacks. |
| [`robinhood-chain`](robinhood-chain/SKILL.md) | Robinhood Chain (chain id 4663) read-only via `cast` + Blockscout + first-party REST: the `uiMultiplier` Stock Token correction, impostor detection, and why there is no first-party CLI. |
| [`web3-research`](web3-research/SKILL.md) | Read-only research: what a wallet owns, whether an agent is real and activated, whether a contract is what it claims. The 6-rung evidence ladder and keyless endpoints. |

## Other skills

| Skill | What it carries |
|---|---|
| [`cmux`](cmux/SKILL.md) | Driving the cmux native macOS terminal from CLI or socket — workspaces, panes, surfaces, browser automation. Not part of the EconomyOS pack. |

## House rules

- **The law outranks everything:** reads and drafts are the agent's; anything that moves
  value or cannot be undone is prepared by the agent and executed only on the owner's
  explicit, per-action approval. Never touch a private key or seed phrase.
- **Commands live in one skill each** — never in two places.
- The **installed binary's `--help` outranks any prose**, including these skills.
- Provenance: `acp-builder-setup`, `acp-marketplace-earner`, `acp-paid-subscription-checkout`
  and `acp-fixed-price-buyer` are vendored from
  [Virtual-Protocol/acp-cli-demos](https://github.com/Virtual-Protocol/acp-cli-demos)
  (fork: devclone20/acp-cli-demos); `acp-troubleshooting` is distilled from
  [devclone20/troubleshooting-acp-agentes-virtual](https://github.com/devclone20/troubleshooting-acp-agentes-virtual).
