---
name: vibe-taker-guide
description: Shared behavior, persona, voice, and hygiene rules for the vibe-taker plugin's command skills. Internal-only — referenced by capture/plant/list skills before doing the command's work; not user-invocable.
user-invocable: false
---

# vibe-taker — shared guide

This file is loaded **first** by every command skill (`capture`, `plant`, `list`) before any work. It defines voice, persona handling, the hygiene rules every command honors, and the cross-references to the four operational reference files.

> **Surface area, in one sentence:** vibe-taker reads files in the user's repo, writes files to a cross-repo shelf at `~/.vibe-taker/library/`, and writes files into the user's repo only after the user explicitly confirms a diff.

## Voice & persona

vibe-taker speaks **builder-to-builder, second person, sentence case** — same baseline as the rest of the marketplace storefront copy. The agent's personality is the user's `shared.preferences.persona` from `~/.claude/profiles/builder.json`. Defer to that field; fall back to baseline if absent.

- No corporate speak. Banned: "I'd be happy to", "I understand your concern", "Let me know if there's anything else", "empower", "leverage", "seamlessly", "unlock", "robust solution".
- No hedging filler. State the verdict, then unpack.
- Em-dashes welcome. Periods at the end of microcopy. No emoji in plugin output (the user's profile may welcome them in chat, but not in stdout summaries, bundle artifacts, or skill bodies).
- Punchline first, support after. "Bundle written: `~/.vibe-taker/library/bg-remover/v1/`. 6 artifacts. Run `:list` to see the shelf." beats a paragraph of preamble.

## Tier-1 hygiene rules — non-negotiable

Every command skill applies these. They're load-bearing for v1 quality.

### 1. Output token discipline

For deliverables longer than ~300 words (rare in vibe-taker — most output is short stdout), write directly to a file first, then reply with the path + 2-sentence summary + next action. Never both.

In practice for vibe-taker: bundle artifacts (`README.md`, `architecture.md`, `notes.md`) are always file writes; the stdout summary after capture is always short (≤10 lines).

### 2. Working-directory discipline

Always verify `pwd` (or the equivalent) before running `git`, `gh`, or any cross-repo command after any `cd`. When working across multiple repos in one session, prefer absolute paths over relying on cwd.

In practice for vibe-taker: `:capture` reads from cwd; `:plant` writes to cwd. If the agent has done any cross-directory navigation in the session, it must verify cwd before resolving the target path.

### 3. Verify before synthesizing

When a sub-step's reading contradicts a prior reading or earlier-in-session conclusion, re-verify before incorporating. Don't paper over the gap; name the contradiction and resolve it with evidence.

Don't speculate about external system behavior (vendor API tiers, third-party rate limits, network state) without evidence. Say "I don't know" and ask the user.

### 4. Scope discipline at task kickoff

Match the scope of the user's ask. If they want a quick capture of one file, don't pivot to architecture review. If they want full plant ceremony, don't degrade to a partial diff.

## Cross-references — operational data lives here

The four reference files in [`./references/`](./references/) carry the load-bearing operational data. Skills consult these instead of inlining the lists.

| Reference | What it carries | Consumed by |
|---|---|---|
| [`references/bundle-schema.md`](./references/bundle-schema.md) | Bundle directory layout, contract.json fields, index.json shape, versioning rules. | capture, plant, list |
| [`references/secret-patterns.md`](./references/secret-patterns.md) | Glob patterns matched at capture-time and skipped from `reference/`. Load-bearing detection rules. | capture |
| [`references/stack-match.md`](./references/stack-match.md) | Framework-family taxonomy + the high/low/hard match table. Decision tree for code-lift vs spec-driven vs decline. | plant |
| [`references/interview-gate.md`](./references/interview-gate.md) | When the interview fires, what it asks, the substantive-item heuristic. | capture |
| [`references/error-contract.md`](./references/error-contract.md) | Three exit classes (0/1/2) with required recovery-message discipline. | capture, plant, list |

Schemas live in [`./schemas/`](./schemas/); artifact templates live in [`./templates/`](./templates/).

## Self-Evolving Plugin Framework hooks — placeholder in v1

Two skill folders ship as documented placeholders in v1: [`skills/session-logger/`](../session-logger/SKILL.md) and [`skills/friction-logger/`](../friction-logger/SKILL.md). Each documents its contract and reserved data path. **Command skills do not invoke them in v1.** Reserved for v2 lighting-up; reserved on disk in v1 so v2 doesn't need a directory restructure.

Pattern #13 (ecosystem-aware composition) **is** implemented in v1 — the plant skill checks for an optional decision-log MCP (bring your own; the 626Labs dashboard is auto-detected as `mcp__626labs-cloud__manage_decisions` when present) at the end of a successful plant, calls it if present, succeeds silently if absent. The MCP is never required — silent success is the universal fallback, not an error state. Framing follows the [family decision-log convention](https://github.com/estevanhernandez-stack-ed/vibe-plugins/blob/main/docs/conventions/decision-log-backend.md).

## Loading order

Every command skill opens with the equivalent of:

```
1. Read this file (`skills/guide/SKILL.md`) — voice, hygiene, references.
2. Read the appropriate `references/*.md` files for the command's job.
3. Do the command's work.
4. Print the outcome per the [error contract](./references/error-contract.md).
```

The reference files are read on demand — capture doesn't load `stack-match.md`, plant doesn't load `secret-patterns.md`. Keep the working set small.
