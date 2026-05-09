# Changelog

vibe-taker follows the [vibe-plugins](https://github.com/estevanhernandez-stack-ed/vibe-plugins) tag scheme: plain `vX.Y.Z` (matches Cart, Doc, Thesis Engine).

## v0.1.1 — 2026-05-09

Manifest fix.

### Fixed

- `plugin.json` — `author` was a string (`"Estevan Hernandez <…>"`); the Claude Code marketplace schema requires the object form. Switched to `{"name": "626Labs LLC", "url": "…"}` to match every other plugin in the ecosystem and to keep personal email out of the published manifest. v0.1.0 installs failed validation; v0.1.1 resolves cleanly.
- Added a canary `.claude-plugin/marketplace.json` at the solo repo root so the canary install path (`/plugin install vibe-taker@estevanhernandez-stack-ed/vibe-taker`) advertised in the README actually resolves.
- Normalized keywords + homepage URL to match the rest of the ecosystem.

## v0.1.0 — 2026-05-08

First release. **Take it with you.**

### Added

- **`/vibe-taker:capture <path|file|glob>`** — autonomous read of a target feature; writes a portable bundle to `~/.vibe-taker/library/<feature>/`. Six-artifact bundle schema (`README.md`, `architecture.md`, `contract.json`, `prompts/`, `reference/`, `notes.md`). Interview gate fires only when WHY can't be derived from source alone (KTD-5). Atomic stage-and-`mv` writes (KTD-3). Versioning prompt on slug collision; no `--auto-bump` flag (OQ-1 resolution).
- **`/vibe-taker:plant <name> [--version=vX]`** — drops a captured bundle into the current repo. Stack detect via target manifest. Decision tree (high → code-lift, low → spec-driven, hard → decline, no-manifest → spec-driven with notice). **Mandatory `[y/N]` diff confirmation** before any write (no `--yes` in v1, KTD-7). Per-file atomic write. Opt-in `mcp__626Labs__manage_decisions` integration; fail-silent when MCP absent (Pattern #13).
- **`/vibe-taker:list [--search Q] [--sort name|lang]`** — read-only shelf surface. Default sort by `captured_at` desc. Search across name, summary, tags, source-repo, language. Jaccard 0.70 dedup hint (OQ-2 default; tunable post-ship without schema change).
- **Bundle schema locked at `schema_version: "1.0"`** (KTD-2). JSON Schemas at `plugins/vibe-taker/skills/guide/schemas/{contract,index}.schema.json`. Hand-edits welcome — the schema is the contract, not the agent's output.
- **Shared `guide` skill** documenting voice, persona handling, Tier-1 hygiene rules (output discipline, working-directory discipline, verify-before-synthesizing, scope discipline at task kickoff), and four reference files: `secret-patterns.md`, `stack-match.md`, `interview-gate.md`, `error-contract.md`.
- **Self-Evolving Plugin Framework placeholders** — `session-logger/SKILL.md` and `friction-logger/SKILL.md` ship as documentation-only with reserved data paths under `~/.claude/plugins/data/vibe-taker/`. Command skills do **not** invoke them in v1 (KTD-8).
- **Local-only privacy posture** (KTD-6). Hardcoded `~/.vibe-taker/` shelf; no `--shelf-path` override. First-ever `:capture` writes a privacy notice to `~/.vibe-taker/README.md`.

### Validated

- Round-trip on the 626labs hub bgremove (`tools/bgremove/`) — capture → high-match Python+CLI plant → planted `--help` runs in target.
- Schema-stability check on Sanduhr theming system — capture of a non-CLI feature shape (markdown + JSON schema + Python validator) fits the v1 schema without a bump.

### Known v1 friction signals (carrying to /reflect)

- Slug proposal heuristic doesn't recognize human-canonical names (folder `bgremove` vs PRD-canonical `bg-remover`).
- Prompt extraction misses markdown-as-prompt (`AGENT_PROMPT.md`-style files); current heuristic only catches >100-char string literals passed to LLM SDK calls in source code.
- `entry_points` field semantics are loose for non-code features (docs/configs as entry points validate but stretch the field's intent).
- Multi-language bundles use a stretched `language: "other:multi-X"` form. `--sort=lang` and the stack-match decision tree assume a single primary language.
- Capture interview gate didn't fire on either round-trip target. Worth tracking whether the gate earns its place in real-world use.
- Auto-mode + `AskUserQuestion` confirmation isn't enough for the Claude Code harness's public-surface gate. The first `git push origin v0.1.0` was blocked despite explicit user authorization; re-confirmation succeeded. Future autonomous builds touching public surfaces should budget for this.

### Deferred to v1.x / v2

- `:plant --yes` flag (OQ-4, KTD-7).
- Cross-machine library sync.
- Auto-port across languages (hard-mismatch decline gets a real cross-language re-implementation).
- Self-Evolving Plugin Framework lighting up (Levels 2-3).
- Per-pair in-language framework adapters (Click → Typer, Express → Fastify) — v1 ships zero adapters.
- Shell completion for `:plant <name>` (OQ-7).
