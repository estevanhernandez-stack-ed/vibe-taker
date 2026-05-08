<!-- /prd output for vibe-taker (Cart cycle #15).
     Generated 2026-05-07 in autonomous mode.
     Inputs: docs/scope.md, docs/spec-substrate.md, docs/builder-profile.md.
     Pattern (mm) Spec-first applied for stylistic substrate refs;
     this PRD is the canonical source for stories + acceptance criteria. -->

# vibe-taker — Product Requirements

## Problem Statement

A builder running Claude Code across multiple repos regularly invents a feature in one repo and wishes it into another — a CLI script, an agent prompt, a wired-up integration. Today the move is copy-paste-then-adapt: source files get duplicated by hand, the *intent* (architectural sketch, non-obvious tradeoffs, prompts) gets lost in translation, and the destination Claude session has to re-derive context that already existed three repos over. The cost compounds across cycles — every replant is a fresh re-derivation, and the unwritten intent never accrues anywhere durable.

vibe-taker fixes this by making "capture-and-replant" a one-shot operation: a portable bundle that carries the architectural intent across repo boundaries, plus a planter that adapts to the destination stack.

## Anchor

> **Take it with you.**

A scope-tape-to-monitor sentence: vibe-taker lifts a feature out of one repo as a portable bundle, and plants it into another adapting to the destination stack.

## User Stories

The user across every story is **a Claude Code builder who works across multiple repos** (initial v1 audience: Estevan Hernandez and the small set of canary-channel users on `estevanhernandez-stack-ed/vibe-taker`).

Stories are grouped into four epics that match the slash-command surface plus the bundle-schema contract. **Epic headings are stable addresses for /spec and /checklist** — don't rename without bumping the cross-doc references.

### Epic: Capture

The harder half. Build first.

- **As a builder, I want to point `:capture` at a folder and produce a bundle on the shelf so the feature is portable to other repos.**
  - [ ] Running `/vibe-taker:capture <folder-path>` from any repo writes a new bundle to `~/.vibe-taker/library/<feature-name>/`.
  - [ ] The bundle directory contains all six artifact paths populated: `README.md`, `architecture.md`, `contract.json`, `prompts/` (may be empty if the feature has no AI prompts), `reference/` (verbatim copy of source), `notes.md`.
  - [ ] `~/.vibe-taker/library/index.json` gets a new entry with name, capture-date, source-repo, source-path, tags, and a one-line summary.
  - [ ] On success, the command prints the bundle path and a 3-line summary to stdout.

- **As a builder, I want to capture a single file (`:capture path/to/file.py`) so that lone scripts don't require fake folder wrappers.**
  - [ ] Running with a file argument produces the same bundle layout as folder capture.
  - [ ] `reference/` contains exactly the one file, named the same as in the source.
  - [ ] `architecture.md` notes "single-file feature" instead of multi-component prose.

- **As a builder, I want to capture a glob (`:capture packages/auth/**`) so that a feature spread across a tree can be lifted in one move.**
  - [ ] Running with a glob argument captures all matching files into `reference/` preserving the relative tree under the glob root.
  - [ ] If the glob matches nothing, the command exits with a clear "no files matched" error and writes no bundle.

- **As a builder, I want unsupported targets (a function inside a 3000-line file) to be declined cleanly so I don't get a half-broken bundle.**
  - [ ] Running with a target that includes line-range syntax (`file.py:120-180`) or any in-file selector exits with: *"vibe-taker captures whole files, folders, or globs in v1. Selection-within-a-file isn't supported — extract to its own file first or capture the parent file."*
  - [ ] No bundle is written when the target is declined.

- **As a builder, I want autonomous read to extract architecture, contract, and intent before any interview so I'm not interrogated on things the agent could have figured out.**
  - [ ] `architecture.md` names the entry points, the data flow, and the key files in the original source — derived from reading every file in scope, not from interview.
  - [ ] `contract.json` includes (at minimum): `inputs`, `outputs`, `dependencies`, `env_vars`, `language`, `framework`, `interface_kind` (CLI / library / SKILL / etc.).
  - [ ] `notes.md` contains autonomous-extracted gotchas (e.g., "uses `sharp` library which has known native-binding issues on Apple Silicon") when the source clearly signals them.

- **As a builder, I want the interview gate to fire only when autonomous extraction couldn't capture WHY so I'm not interrupted needlessly.**
  - [ ] If autonomous pass produces a `notes.md` with fewer than 3 substantive items, OR if no `README.md`-like prose exists in source to derive intent from, the interview gate fires.
  - [ ] The interview asks at most 4 questions: (1) what is this *for*?, (2) shelf-name confirmation/override, (3) any non-obvious tradeoffs to preserve?, (4) tags for search.
  - [ ] If autonomous pass produces 3+ substantive notes AND a derivable intent line, the interview gate is skipped and the agent prints "intent derived autonomously — bundle ready at <path>; edit `notes.md` if anything's missing."

- **As a builder, I want re-capturing an existing name to produce a versioned bundle so I don't accidentally overwrite a working feature.**
  - [ ] When `:capture` detects the proposed shelf-name already exists in `index.json`, it pauses and prints: *"<name> already on the shelf. Bump to v2? [y/N]"*
  - [ ] On `y`, the new bundle goes to `~/.vibe-taker/library/<name>/v2/` and the prior bundle moves to `~/.vibe-taker/library/<name>/v1/` if not already versioned. `index.json` records both.
  - [ ] On `n` or empty, the command exits with no changes and prints the path of the existing bundle.

- **As a builder, I want sensitive content (`.env` files, files matching common secret patterns) refused at capture time so secrets never land in the shelf.**
  - [ ] `:capture` skips files matching: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`, `*secret*`, and prints which were skipped.
  - [ ] If skipped files are load-bearing for the feature (named in entry points or imports), the command warns: *"Skipped X secret-like files that look load-bearing. Capture continues with these stubbed in `contract.json` under `env_vars`. Provide them at plant-time."*

### Epic: Plant

Mostly mechanical once the bundle schema is locked. Build second.

- **As a builder, I want `:plant <name>` to drop a captured feature into the current repo so the move from one repo to another is one command.**
  - [ ] Running `/vibe-taker:plant <name>` reads the named bundle from `~/.vibe-taker/library/`.
  - [ ] By default, plants the latest version. `--version=v1` opts to a specific version.
  - [ ] Before any file is written, the agent shows the planned changes as a unified diff and asks for confirmation. **No file is written without explicit user confirmation.**

- **As a builder, I want stack-match detection so a high-match plant uses code-lift-with-adapters and a low-match plant uses spec-driven re-implementation.**
  - [ ] `:plant` reads the target repo's manifests (`package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `*.csproj`, etc.) and compares to the bundle's `contract.json.language` and `contract.json.framework`.
  - [ ] **High match** (same language, similar framework: e.g., Python source → Python target with same major framework, or Node source → Node target): code-lift. Copy `reference/` files into the target with imports rewritten and paths adjusted to local conventions.
  - [ ] **Low match** (same language, different framework — e.g., Express bundle → FastAPI target): spec-driven. Read `architecture.md` + `contract.json`, write fresh code in the target's stack, keep `reference/` in sight as a guide.
  - [ ] **Hard mismatch** (different language): see the next story.
  - [ ] The chosen mode is named in the diff header so the user knows what they're confirming.

- **As a builder, I want hard mismatches (cross-language plant) to gracefully decline with a recovery path so v1 doesn't auto-port lossily.**
  - [ ] When `contract.json.language` differs from the target's primary language, `:plant` exits with: *"vibe-taker bundles capture <source-lang>; your target repo is <target-lang>. v1 doesn't auto-port across languages — too lossy. Here's the architecture sketch (`<bundle-path>/architecture.md`) and reference code (`<bundle-path>/reference/`); port manually, or capture a <target-lang>-native version of this feature into a new bundle."*
  - [ ] No file is written.

- **As a builder, I want plant into a target with no detectable stack (no manifests) to fall back to a sensible default rather than crashing.**
  - [ ] When no manifest is detected in target, `:plant` defaults to **low-match / spec-driven** mode and prints: *"No manifest detected in target — falling back to spec-driven re-implementation. Reference code in <bundle-path>/reference/ for guidance."*

- **As a builder, I want plant to log a decision to the 626Labs Dashboard (when reachable) so the move is durable beyond the local terminal.**
  - [ ] On successful plant, if `mcp__626Labs__manage_decisions` is available in the runtime, the agent calls it with: action `log`, body naming what was planted, source bundle, source path, target repo, plant mode (code-lift / spec-driven), tagged with the bound project ID if the current repo is bound.
  - [ ] If the dashboard tool is unavailable, the plant succeeds silently without the log call.

### Epic: Library management

- **As a builder, I want `:list` to surface what's on the shelf so I can pick something to plant without remembering exact names.**
  - [ ] Running `/vibe-taker:list` prints each bundle: name, version count, last-captured date, language/framework, one-line summary.
  - [ ] Sorted by last-captured date descending by default. `--sort=name` and `--sort=lang` are accepted.
  - [ ] Reads from `index.json`. If the index is missing or corrupt, command exits with: *"Library index missing or corrupt at <path>. Re-capture a feature to rebuild, or restore from backup."*

- **As a builder, I want `:list --search <query>` so the shelf scales past mental-recall.**
  - [ ] Searches across bundle name, summary, tags, source-repo, language. Case-insensitive.
  - [ ] Prints matches in same format as bare `:list`. Empty result prints "no matches" and exits 0.

- **As a builder, I want `:list` to surface near-duplicates so my shelf doesn't sprawl with three bg-removers.**
  - [ ] When a bundle's autonomous-derived summary has ≥70% Jaccard token similarity with another bundle's summary, both are flagged in the listing with `[similar to: <other-name>]`.
  - [ ] Similarity check is best-effort and runs at `:list` time, not at `:capture` time (don't slow down capture for a UI hint).

- **As a builder, I want the shelf to be local-only by default with a clear notice so I never wonder if my captured features hit the network.**
  - [ ] First-ever `:capture` run prints: *"vibe-taker writes to your local home directory only (`~/.vibe-taker/`). No network calls, no sync. Cross-machine sharing is a v2 concern."*
  - [ ] `~/.vibe-taker/README.md` (auto-created on first capture) contains the same notice as a one-paragraph orientation.

### Epic: Bundle schema

The contract surface. Whatever ships in v1 is durable for at least one minor cycle of users without migration.

- **As a downstream Claude Code session, I want a bundle's schema to be unambiguous so I can re-implement the feature reliably.**
  - [ ] `contract.json` validates against a schema (informally documented in `architecture/bundle-schema.md` during /spec). Required fields: `name`, `version`, `language`, `framework`, `interface_kind`, `inputs`, `outputs`, `dependencies`, `env_vars`, `source_repo`, `source_path`, `captured_at`.
  - [ ] `architecture.md` always opens with a 1-3 sentence summary, then a "Components" section, then a "Data flow" section.
  - [ ] `notes.md` always contains at minimum: a "Why this exists" section (autonomous-derived or interview-supplied) and a "Gotchas" section. Empty sections are explicit ("None known."), never absent.

- **As a builder, I want `index.json` to be small and human-readable so I can hand-edit when the agent gets it wrong.**
  - [ ] `index.json` is JSON, pretty-printed with 2-space indentation, max ~200 bytes per entry.
  - [ ] Each entry contains: `name`, `latest_version`, `versions: [{version, captured_at, source_repo, source_path}]`, `tags: []`, `summary` (one line), `language`, `framework`.

## What We're Building

Everything in the four epics above. v1 ships when **all three** of these hold:

1. **Capture works on the bg-remover test case.** `:capture <path-to-bg-remover>` against the 626labs hub repo produces a bundle with all six artifacts populated, autonomous-derived intent, and a clean `index.json` entry.
2. **Plant re-installs into a different test repo.** `:plant bg-remover` into a fresh repo produces a working CLI bg-remover (or a clean decline if the repo's stack hard-mismatches) with the diff shown before any write.
3. **Bundle schema feels stable.** A second feature captures cleanly into the same schema without exposing a "we need a new field" surprise.

## What We'd Add With More Time

- **Selection-within-a-file capture** — pluck a function from a 3000-line file. Hard mode; deferred.
- **Cross-machine library sync** — git-backed library, S3 sync, or Dashboard-hosted shelf. v2 concern; don't over-design.
- **Auto-port across languages** — turn the hard-mismatch decline into a real cross-language re-implementation. Requires substantially better intent capture; v2 minimum.
- **Marketplace publishing of bundles** — `:publish <name>` writes a bundle to a public catalog. Different product than the local shelf.
- **`:diff <name>`** — re-read the source repo and show what's drifted from the bundle since capture. Useful for re-syncing.
- **`:update <name>`** — bump a bundle in place from the source-of-truth repo without going through `:capture` ceremony.
- **Self-Evolving Plugin Framework lighting up** — session-logger, friction-logger, evolve skill. v1 keeps the architecture compatible (file paths, folder names) but doesn't ship implementations.
- **Better summary similarity** — semantic similarity instead of Jaccard tokens for the dedup hint in `:list`.
- **Tag autocomplete in `:capture` interview** — autonomous proposes tags from existing index entries.

## Non-Goals

- **vibe-taker is not a marketplace.** Marketplaces are public, curated, distribution-shaped. The shelf is private, local, capture-shaped. `vibe-plugins` already plays the marketplace role for plugins; bundles aren't plugins.
- **vibe-taker is not a snippet manager.** Snippets don't carry intent. The bundle's contract surface (architecture + WHY + prompts + reference) is the difference; without it, there's no point.
- **vibe-taker is not a templating engine.** Templates are abstract, parameterized scaffolds. Bundles are concrete features with their original implementation. Don't drift toward `<%= name %>` substitution.
- **vibe-taker is not a codemod tool.** Codemods rewrite where they stand. vibe-taker transplants between repos. Don't blend the two — codemods know one stack; vibe-taker knows two and decides between them.
- **vibe-taker has no UI surface in v1.** Slash commands and SKILL files are the entire surface area. No dashboard panel, no web view, no terminal TUI beyond stdout.

## Open Questions

Each below has a proposed default already encoded in acceptance criteria. The default takes effect unless the builder overrides at /spec time. Flagged with whether resolution is needed before /spec or can wait.

- **OQ-1 — Versioning bump prompt vs auto-bump.** *Default: prompt user (`y/N`).* The prompt costs a beat of friction; the auto-bump risks silent shelf sprawl. Architect read: prompt wins because the bundle schema is still calibrating in v1 — false-bumps are cheaper to recover from with a prompt than with a delete-and-recapture. **Resolve at /spec.** If overriding to auto-bump, flag the v1 schema-stability tradeoff.
- **OQ-2 — Dedup similarity threshold.** *Default: 70% Jaccard token similarity on summaries.* Conservative — a 50% threshold would over-flag at v1 size; 90% would never fire. **Can wait for build.** Tunable post-ship without a schema change.
- **OQ-3 — Stack-match high/low/hard threshold definition.** *Default: high = same primary language + framework family overlap (Express vs Hapi both Node-web); low = same language, different framework family; hard = different language.* The framework-family table needs to be enumerated in /spec. **Resolve at /spec.**
- **OQ-4 — `:plant` confirmation step.** *Default: always show diff and require explicit confirmation, no `--yes` flag in v1.* v2 can add `--yes` once the diff format has been validated. **Can wait for build.**
- **OQ-5 — `notes.md` interview-gate threshold ("3 substantive notes").** *Default: 3 items, where "substantive" means line length ≥ 30 chars and not just a re-statement of `architecture.md` content.* Heuristic; tunable. **Can wait for build.** First friction signal to track at /reflect.
- **OQ-6 — Bundle storage location override.** Out of scope for v1 unless the builder pushes back. *Default: hardcoded `~/.vibe-taker/library/`. No `--shelf-path` override.* Cross-machine sync is v2, so config-locking the path is fine. **Resolve at /spec only if pushback.**
- **OQ-7 — Shell completion for `:plant <name>`.** Discoverability nice-to-have. *Default: not in v1.* `:list` is the discovery surface. **Resolve only if Cart cycle has time post-build.**

## Cross-references

- Scope axes and explicit cuts: [`docs/scope.md`](./scope.md).
- Capture / plant flow narrative + bundle directory layout: [`docs/spec-substrate.md`](./spec-substrate.md).
- Builder profile (audience, conventions, deployment target): [`docs/builder-profile.md`](./builder-profile.md).
- Six-plugin reference architecture: vibe-cartographer, vibe-doc, vibe-iterate, vibe-test, vibe-sec, vibe-thesis (see scope.md "Inspiration & References").
