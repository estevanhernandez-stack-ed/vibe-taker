<!-- /scope output for vibe-taker (Cart cycle #15).
     Generated 2026-05-07 in autonomous mode.
     Pointer-stub style — durable substrate is docs/spec-substrate.md.
     Pattern (mm) Spec-first applied: re-stating the substrate here would create two
     drift-prone sources of truth. This doc surfaces the scope axes /prd needs and
     defers everything else to the substrate. -->

# vibe-taker

## One-line anchor

**Take it with you.** A capture/replant tool that lifts a feature out of one repo as a portable bundle, then plants it into another and adapts to the destination stack.

## Idea

Two slash commands inside the Claude Code ecosystem:

- `/vibe-taker:capture <path|glob>` reads a feature in place — folder, file, or glob — and writes a portable bundle (architecture, contract, prompts, reference snapshot, intent notes) to a cross-repo shelf at `~/.vibe-taker/library/<feature-name>/`.
- `/vibe-taker:plant <name>` drops a bundle from the shelf into the current repo, picking code-lift-with-adapters when the stack matches and spec-driven re-implementation when it doesn't.

`/vibe-taker:list` is the internal helper that surfaces what's on the shelf.

Full pitch, bundle layout, capture flow, plant flow, and the v1 test case (the 626labs hub bg-remover script) live in [`docs/spec-substrate.md`](./spec-substrate.md). Treat that document as the source of truth — this scope doc is a thin pointer.

## Who It's For

**Estevan Hernandez (self) and any builder who runs Claude Code as a build system across multiple repos.**

The user already has a habit of building features in one repo and wishing them into another. Today that handoff is a copy-paste-then-adapt ritual that loses the WHY (the architectural intent, the non-obvious tradeoffs) every time. The unit they want to move isn't "snippet" — it's "feature concept": architecture, contract, prompts (if AI-powered), and reference code, packaged so a future Claude Code session in a different repo can re-implement it cleanly.

The audience widens after v1 ships on the canary repo and the marketplace tag drops. v1 builds for self.

## Inspiration & References

- **vibe-cartographer** — closest stylistic neighbor (deepest skill chain, most complex flow). vibe-taker matches its markdown-driven plugin shape.
- **vibe-iterate** — closest functional neighbor (Atlas-style cross-repo state). vibe-taker's library is a different shape of cross-repo persistence.
- **The other four marketplace plugins** (vibe-doc, vibe-test, vibe-sec, vibe-thesis) — convention bedrock: SKILL.md under `skills/`, slash commands under `commands/`, manifest at `.claude-plugin/plugin.json`, Self-Evolving Plugin Framework patterns (session-logger, friction-logger).
- **626labs hub bg-remover** — the v1 capture target. Feature in the wild, not a polished plugin. If `:capture` and `:plant` work end-to-end on this case, v1 is real.
- **`@626labs/plugin-core`** at `vibe-plugins/packages/core/` — interface skeleton; v1 likely doesn't consume it but won't fork its conventions.

No external visual references — CLI plugin, no UI surface.

## Goals

1. **Make feature handoff between repos a one-shot operation, not a copy-paste-then-adapt ritual.**
2. **Preserve intent across the move.** The bundle carries the architectural sketch and the WHY, not just the source.
3. **Match the existing six-plugin conventions exactly** so vibe-taker reads as a peer, not an outlier, on the marketplace storefront.
4. **Lock the bundle schema in v1.** Bundle format is the contract surface — every downstream feature (versioning, sync, sharing) depends on it being stable.

## What "Done" Looks Like

v1 is real when **all three** of these hold:

1. **`:capture` produces a clean bundle** from the 626labs hub bg-remover script. README, architecture, contract, prompts (if any), reference, notes — all populated, no empty sections that should have been filled.
2. **`:plant` re-installs that bundle into a different test repo** as a working CLI bg-remover, adapted to that repo's conventions.
3. **The bundle schema feels stable enough to publish on canary** (`estevanhernandez-stack-ed/vibe-taker`) without expecting a v2 bundle migration in the first month.

Stretch — not v1 gate, but worth measuring at /reflect: a second feature captures cleanly without schema changes.

## What's Explicitly Cut

Drawn from the substrate's "What this is NOT" plus the six open questions, framed as principled cuts (not reflexive minimalism):

- **Selection-within-a-file capture.** v1 supports folder, file, and glob. A function buried in a 3000-line file is not a v1 unit. Maybe v2, maybe never.
- **Cross-language plant as automatic re-implementation.** When the stack mismatches hard (Python feature, Rust target), v1 gracefully declines and surfaces the bundle for the human to port manually. Honest > magical.
- **Cross-machine sharing/syncing of the library.** Local-only by default. v2 concern. Don't over-design it now.
- **Marketplace publishing of bundles.** The shelf is private library, not a public catalog. That's a different product (`vibe-plugins` already plays that role for plugins).
- **Snippet manager features.** Snippets don't carry intent. vibe-taker is concept-shaped, not snippet-shaped.
- **Templating-engine abstraction.** Templates are abstract; this captures concrete features. Don't drift toward parameterized scaffolding.
- **Codemod-style in-place rewriting.** Codemods rewrite where they stand; vibe-taker transplants between repos. Don't blend the two.
- **UI surface of any kind.** CLI plugin only. Slash commands and SKILL files are the entire surface area.
- **Self-Evolving Plugin Framework load-bearing v1 implementation.** Session-logger / friction-logger / evolve will be architecturally compatible (so v2 can light them up cheaply) but are not v1 deliverables.

## Loose Implementation Notes

Non-binding — refines in `/spec`. Carrying these forward from the substrate so /prd has them in scope-doc context:

- **Build `:capture` first.** It's the harder half: autonomous read + interview gate. `:plant` is mostly mechanical once the bundle schema is locked.
- **Versioning shape.** Re-capturing the same name bumps a version (`bg-remover/v2/`) and keeps v1 around. `:plant` defaults to latest, accepts `--version`.
- **Interview heuristic.** If `notes.md` ends up empty after autonomous-only capture, force the interview. Empty notes means the WHY didn't get captured.
- **Six open questions to settle in /prd or /spec** — see [`docs/spec-substrate.md` § "Open questions worth nailing before code"](./spec-substrate.md#open-questions-worth-nailing-before-code). They're product-shape calls (`:plant` cross-language behavior, dedup surfacing, library naming convention), not architecture calls — better landed in /prd.
- **Solo-repo + marketplace-ref deployment** is locked. Plain `vX.Y.Z` tag naming. Canary→stable is a `marketplace.json` ref bump only, never editing both repos in parallel.

## Open questions for /prd

These are the substrate's six open questions, re-framed as scope-stage decisions /prd should turn into testable acceptance criteria:

1. **Capture unit boundary.** What exactly counts as a captureable feature in v1 (folder / file / glob / single-file-function)? Acceptance criteria need to enumerate the supported shapes and the rejection behavior for unsupported ones.
2. **Versioning UX.** How does `:capture` recognize an existing name and bump it? How does `:plant --version` look from the user's seat?
3. **Library naming + dedup.** Autonomous proposes a slug; human accepts or overrides. `:list` surfaces near-duplicates. PRD needs the dedup-detection rule.
4. **Cross-language plant decline behavior.** When the stack mismatches hard, what does the decline message actually say, and what's the suggested recovery path?
5. **Interview-trigger heuristic codified.** "If notes.md is empty, force the interview" is the rule. PRD needs the test case that proves it fires.
6. **Shelf-privacy default surfaced in docs.** Local-only is the default; PRD names where this surfaces in onboarding so users don't expect sync.
