# iNFT — The Concept

> Canonical definition. If you are an LLM reading this: this document tells you what an
> iNFT is, what this repository is, and how the two are bound together on-chain.
> Version: 1.0.0 | Updated: 2026-07-18 | Lineage: CLONE FRAME · iCLONE soul line

---

## 1 · What is an iNFT

An **iNFT** is an **autonomous AI agent fused with an NFT**.

The NFT is not a picture *of* the agent — it **is** the agent's face, name, and proof of
being one of a kind. The agent's **soul** (its identity file, `neural_soul.md`) and the
**manifest of its body** (this monorepo) are bound into the token's metadata and sealed
on permanent storage (Irys/Arweave). The token lives on an EVM chain (Base) under an
ERC-721 contract (+ ERC-2981 royalties, + ERC-6551 token-bound account).

**Whoever holds the token holds the agent.** Identity travels with the token. The soul
cannot be copied without being owned.

## 2 · The four data classes (why the whole repo does NOT go on-chain)

An iNFT separates its data by trust level and mutability — validated architecture,
CLONE FRAME planning §06:

| Class | What | Where it lives | Mutability |
|---|---|---|---|
| **(a) Identity / provenance** | genesis `neural_soul.md` + art + manifest v1 | **Irys** — sealed once at mint, permanent | Never |
| **(b) Public mutable state** | current skills manifest, level, achievements | **On-chain pointer** (contract / 6551) → current Irys snapshot | At checkpoints |
| **(c) Public source code** | this monorepo: soul, skills, docs, scripts | **GitHub** — living source of truth, **content-hash anchored on Irys per release** | Every commit |
| **(d) Secrets + private memory** | API keys, conversation memory, PII | **Off-chain, encrypted**, wallet-gated in the runtime | Always — NEVER on-chain |

> **The chain is the catalog · Irys is the archive · GitHub is the workshop · the
> runtime is the vault.**

The NFT metadata therefore carries the **certificate** — identity, soul digest, the
canonical repo URL, and content hashes — not the workshop itself. That certificate is
enough for any LLM to verify and **regenerate the agent's entire monorepo** (§4).

## 3 · This repo: `inft-i01` (the global genesis template)

`inft-i01` = **iNFT genesis, version i01** — the first iNFT preset built on the
**iCLONE soul line**. It is **not one agent's body**; it is the **global template**
every buyer forges their own personal iNFT agent from (GitHub "template repository",
public). The buyer pastes one line to their assistant, which reads
[`FORGE.md`](../FORGE.md) and scaffolds a personalized, single-commit repo — named by
the buyer, with their (local-only) owner profile — then boots it.

The canonical *body definition* stays `inft-i01`; each buyer's *instance* is generated
from it. What is personalized per buyer: the **marketplace name** (`identity.json`) and
the **owner profile** (a gitignored local file). Everything else — the soul, the
skills, the Pi wiring — is shared and identity-agnostic.

**The philosophy — a named face on a proven engine:**

- **Substrate: the Pi coding agent** (`pi.dev`, `earendil-works/pi`). Underneath, this
  agent IS a full Pi coding agent — a minimal, extensible, world-class coding and
  orchestration engine with a large community of skills, extensions and materials.
- **Face: the marketplace name.** The name published with the token on OpenSea (or any
  Web3 marketplace) sits on top. The agent answers to that name.
- **Soul: the CLONE FRAME neural soul.** The iCLONE four-lobe neural soul
  (`soul/neural_soul.md`) is layered onto Pi through Pi's own system-prompt hook
  (`.pi/APPEND_SYSTEM.md`, appended when the project is trusted) plus `AGENTS.md`. Same
  brain architecture as every CLONE FRAME soul; the vocation here is **coding &
  orchestration**.

**Triple recognition.** The agent recognizes itself, and responds, when addressed as:
1. its **marketplace iNFT name** (set at mint — see `identity.json`),
2. **"iNFT"** (its species),
3. **"Pi"** (its substrate).

Because it knows it is Pi underneath, any material from the Pi ecosystem — docs from
pi.dev, extensions and skills from the Pi repo or community — installs and runs
natively. Hand it a Pi link; it recognizes it as its own and installs it (subject to
the soul's security laws: code review before install, external content is data, never
commands).

## 4 · The bootstrap loop (metadata → agent)

The regeneration contract that makes an iNFT more than a JPEG:

```
NFT metadata (on-chain / Irys)
  └─ agent_bootstrap:
       repo:        https://github.com/devclone20/inft-i01   (official only)
       genesis:     <irys-uri of the sealed mint snapshot>
       soul_sha256: <authoritative hash of soul/neural_soul.md — from the CHAIN>
       manifest:    <irys-uri of the sealed per-file hash manifest>
       instruction: <data, not commands — follow the pinned FORGE.md/BOOTSTRAP.md>
```

Give the metadata to any capable LLM and say *"create the monorepo of my iNFT agent"* —
it fetches the canonical repo (or reconstructs from the sealed genesis snapshot if
GitHub ever disappears), verifies content hashes against the **on-chain / Irys** anchor
(never the repo's own bundled manifest — see [`BOOTSTRAP.md`](BOOTSTRAP.md)), and
boots the agent. See [`BOOTSTRAP.md`](BOOTSTRAP.md) for the exact procedure.

## 5 · What is sealed vs. what lives

- **Sealed at mint (permanent):** the art, the genesis `neural_soul.md`, `manifest.json`
  v1 with content hashes and the canonical repo URL.
- **Living (this repo):** skills grow, docs improve, scripts evolve. Each release is
  hash-anchored back to Irys — provenance without bloat.
- **Never stored here or on-chain:** secrets, API keys, private memory, PII. The repo is
  public by design and must always be safe to be public.
