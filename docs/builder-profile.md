<!-- Builder profile for the vibe-taker Cart cycle (#15).
     Generated 2026-05-07 in autonomous mode (returning builder, full profile on file).
     Every value pulled from ~/.claude/profiles/builder.json unless marked (default — confirm on next run). -->

# Builder Profile

## Who They Are

**Estevan Hernandez** — Builder and outsider. "Mr. Solo Dolo" (handle from LADDER). Runs 626Labs out of Fort Worth, TX. 20+ years PC/Windows experience. Vibe coder — architects and ships through AI agents rather than writing code directly; strong pattern recognition, troubleshooting, and systems thinking. Has shipped ~10 deployed apps including a 7-app enterprise suite under serious consideration for company deployment. Active **Vibe Cartographer plugin contributor** — modified the plugin for company use.

This is **Cart cycle #15**. The fourteen prior cycles (LADDER, Sanduhr, Vibe Test, RTClickPng, 626Labs Universe Deep Dive, Lab Backbone Step 1, ThesisStudio, BlogStudio, Vibe Thesis, Substrate Step 2, SnipSnap, wbp-azure, Sales Standards POC, opsgen retrofit) ground the substrate.

## Technical Experience

- **Level:** experienced (last confirmed 2026-04-25; TTL 365 days; fresh)
- **Languages:** TypeScript, Python, JavaScript, Luau, C#, HTML/CSS, C++ (last confirmed 2026-04-25; fresh)
- **Frameworks:** React 19, Next.js, Vite, TailwindCSS, Firebase, FastAPI, Flask, Express, .NET 8/9, Azure, Expo, React Native, Drizzle ORM, Playwright, WPF, C++/WinRT, Windows App SDK / WinUI 3, MSIX / wapproj, Ollama, Gemma 4
- **AI agent experience:** Deep. Built and shipped Claude Code plugins (Vibe Cartographer, Vibe Doc, Vibe Test) to marketplace. Runs Claude Code as autonomous build system with structured checklists and subagent delegation — proven across 14 Cart cycles. Willing to switch agents mid-project when one is stuck.

## Mode

**Builder** — pulled from `plugins.vibe-cartographer.mode` on the unified profile.

**Autonomy:** `fully-autonomous` — promoted 2026-04-26 during Substrate Step 2 /evolve. Future Cart commands respect this field. Pacing-question gate at /onboard still fires (the SKILL contract).

**Build-mode preference:** `iterative-prototype` — pulled from profile.

**Cycle builder identity:** `self` — Estevan as builder. Not running an agent persona as the builder this cycle.

## Persona

**Architect** — *"Let's design for the long game."* Big-picture, tradeoff-focused. Surfaces long-term implications. Pulled from `shared.preferences.persona`; cross-plugin.

## Project Goals

Build **vibe-taker**: a feature capture/replant tool for the Claude Code ecosystem.

**Two commands:**
- `:capture <path>` — autonomous-first read of a target feature/tool, writes a portable bundle to a cross-repo library shelf
- `:plant <name>` — drops a captured feature into the current repo, adapting to the destination stack

**Bundle home:** `~/.vibe-taker/library/<feature-name>/` — cross-repo, single source of truth. (User confirmed cross-repo over per-repo placement on the basis of "starting here with the context.")

**v1 test case:** 626labs hub's CLI AI-powered bg-remover script. The unit isn't "polished plugin" — it's "feature in the wild" (script in a repo). If `:capture` and `:plant` work end-to-end on that case, v1 is real.

**Pre-onboard substrate** lives at `docs/spec-substrate.md` — the brainstorming-stage one-pager with bundle layout, capture/plant flows, and six open questions. Cart's downstream `/scope` → `/prd` → `/spec` produces the canonical artifacts; the substrate informs them.

**Success measure:** v1 ships when (a) `:capture` produces a clean bundle from the bg-remover, (b) `:plant` re-installs that bundle into a different test repo, and (c) the bundle schema feels stable enough to publish on canary (`estevanhernandez-stack-ed/vibe-taker`).

## Design Direction

CLI plugin. **No UI surface** — slash commands and skill files are the entire surface area.

**Conventions to match** (the existing six marketplace plugins):
- Markdown-driven `SKILL.md` files under `plugins/vibe-taker/skills/`
- Slash commands under `plugins/vibe-taker/commands/` (`.md` files)
- `plugin.json` manifest at `plugins/vibe-taker/.claude-plugin/plugin.json`
- Self-Evolving Plugin Framework patterns: session-logger, friction-logger, evolve skill (not load-bearing for v1, but architecturally compatible)
- Voice: builder-to-builder, second person, sentence case. Same as the rest of the marketplace storefront copy.

**Visual sensibility (where any docs/screens render):** Clean, functional, high-contrast. Dark themes, muted palettes, clear information hierarchy. (Pulled from `creative_sensibility` on the unified profile.)

## Prior SDD Experience

**Deeply experienced.** Fourteen completed Cart cycles, the cart-cycle-brief pattern proven, fully-autonomous mode validated. Patterns load-bearing for this cycle: (mm) Spec-first, (gg) Path B for surgical breaks, (cc) Three-stage close (structurally / empirically / externally complete), (k) Enterprise bundle as single decision, (ww) Verify-against-validate before incorporating subagent claims, (uu) Run baseline tests at CL-11 not just baseline build.

`/reflect` quiz can skip first-principles SDD framing. Calibrate at the senior-Cart-contributor level.

## Architecture Docs

**No formal architecture docs provided as separate files** — but two strong substrates inform `/spec`:

1. **`docs/spec-substrate.md`** — the pre-onboard brainstorming spec for vibe-taker (bundle layout, capture/plant flows, six open questions to settle).
2. **The six existing marketplace plugins as reference architecture** — vibe-cartographer, vibe-doc, vibe-iterate, vibe-test, vibe-sec, vibe-thesis. Each demonstrates the markdown-driven plugin pattern. vibe-cartographer is the closest stylistic neighbor (deepest skill chain, most complex flow). vibe-iterate is the closest functional neighbor (Atlas-style cross-repo state).
3. **`@626labs/plugin-core`** at `vibe-plugins/packages/core/` — currently v0.0.1 interface skeleton. vibe-taker is unlikely to consume it in v1 but should not fork its conventions (session-logger, friction-logger interfaces).

`/spec` will draft against established plugin patterns rather than from scratch.

## Deployment Target

**Solo repo + vibe-plugins marketplace.** Same shape as the other six plugins:

- **Solo repo:** `estevanhernandez-stack-ed/vibe-taker` (canary channel — bleeding-edge `main`)
- **Marketplace ref:** `vibe-plugins/.claude-plugin/marketplace.json` adds a `vibe-taker` entry pinned to a tag on the solo repo (stable channel — promoted, tested)
- **Tag naming:** plain `vX.Y.Z` (matches Cart, Doc, Thesis Engine, Vibe Thesis; not the `<plugin>-vX.Y.Z` form used by Test and Sec)

**Decision logged for downstream:** the canary→stable promotion ritual is `marketplace.json` ref bump only, never editing both repos in parallel (see `vibe-plugins/CLAUDE.md` "What NOT to do").

---

<!-- Autonomous-run defaults marked above:
     None for this profile — every field on the unified profile was fresh as of 2026-04-25,
     and project-specific values were either captured in this session or pulled from the
     pre-onboard substrate at docs/spec-substrate.md.
     If anything below shifts at /scope time, update inline. -->
