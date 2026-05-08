# vibe-taker — feature capture & replant

> Status: spec draft. No code yet. Lives here until it earns a solo repo.

## The pitch

You point vibe-taker at a feature or tool — a directory, a file, a script, doesn't matter — and it captures the *shape* of that feature into a portable bundle on your local shelf. Later, in a different repo, you tell vibe-taker to plant it, and it adapts to the destination stack.

The unit isn't "snippet." It's "feature concept" — architecture, contract, prompts (if AI-powered), and a reference code snapshot, packaged so a future Claude session in another repo can re-implement it cleanly.

Tagline candidate: *Take it with you.*

## Two commands

- `/vibe-taker:capture <path|glob>` — read the target, write a bundle to the shelf. Autonomous-first; interviews only for the soft parts (WHY, intent, non-obvious tradeoffs, shelf naming).
- `/vibe-taker:plant <name>` — in any repo, drop a captured feature into the current codebase. Detects target stack, picks code-lift-with-adapters vs spec-driven re-implementation based on stack match.

A third internal helper:

- `/vibe-taker:list` — readable index of what's on the shelf with one-line summaries, plus search by tag/intent.

## The shelf — `~/.vibe-taker/library/`

Cross-repo, single home, full context lives here. Decided: starting here is best — context is centralized, not scattered across source repos.

```
~/.vibe-taker/
├── library/
│   ├── <feature-name>/
│   │   ├── README.md          # human-readable: what it is, when to reach for it, intent
│   │   ├── architecture.md    # components, data flow, key files in original
│   │   ├── contract.json      # I/O surface: inputs, outputs, deps, env, language/framework
│   │   ├── prompts/           # AI prompts if any, one file per prompt
│   │   ├── reference/         # read-only snapshot of original code
│   │   └── notes.md           # non-obvious tradeoffs, gotchas, decisions (interview output)
│   └── index.json             # shelf manifest — names, tags, capture date, source repo
└── config.json                # user prefs: default stack hints, capture verbosity, etc
```

`index.json` is what `:list` reads and what `:plant` matches against for fuzzy lookup.

## Capture flow

1. **Target.** User runs `/vibe-taker:capture <path-or-glob>`. Path can be a folder (`apps/bg-remover/`), a single file (`scripts/bg-remove.py`), or a wildcard (`packages/auth/**`). If no arg, ask what to capture.
2. **Autonomous read.** Walk the target. Identify language(s), framework(s), entry points, dependencies (package.json / pyproject / Cargo.toml / requirements). Read every file in scope. Infer the architecture sketch and the I/O surface.
3. **Snapshot.** Copy original files into `reference/` verbatim. This is the fallback truth if the spec misses nuance.
4. **Interview gate.** Only ask questions a human alone can answer:
   - What's this feature *for*? (intent, not what the code does)
   - What's the right shelf name? (autonomous can propose; human picks)
   - Any non-obvious tradeoffs the spec should preserve?
   - Tags for future search?
5. **Write the bundle.** Generate README, architecture, contract, prompts, notes. Append to `index.json`.
6. **Confirm.** Show the user the bundle path and a 3-line summary. Done.

## Plant flow

1. User in target repo runs `/vibe-taker:plant <name>`.
2. Read the bundle from the shelf.
3. **Stack-match decision.** Read target repo's package.json / pyproject / etc. Compare to bundle's `contract.json`.
   - **High match** (same language, similar framework) → code-lift-with-adapters: copy reference code, rewrite imports/paths, adjust to local conventions.
   - **Low match** (different language or framework) → spec-driven re-implementation: read the spec, write fresh code in the target stack, use reference as guide only.
4. Draft the integration as a diff. User reviews before commit. Always.
5. Optional: log a decision to the 626Labs Dashboard naming what was planted and from where.

## Test case — the bg-remover

The 626labs hub repo has a CLI AI-powered bg-remover script that isn't a published plugin — it lives as a tool inside the repo. This is the *feature in the wild* case and the right shape for the v1 test:

- **Capture target:** `/vibe-taker:capture <path-to-bg-remover>` against the 626labs hub clone.
- **Expected bundle output:**
  - `README.md` — "AI-powered CLI background remover. Takes an image path, returns a transparent-bg version. Uses <model X> via <API Y>."
  - `architecture.md` — single-file CLI, args parsed via Y, calls model via Z, writes to disk.
  - `contract.json` — input: image path. Output: image path. Deps: <list>. Env: API key var. Language: Python (or whatever).
  - `prompts/` — if there's a system prompt for the model, captured here.
  - `reference/bg-remove.py` — the original script verbatim.
  - `notes.md` — interview answers: why this exists, what the alternative was, gotchas (e.g., "model X struggles with hair fringe — accepted").
- **Plant target:** any repo where you want a CLI bg-remover. `:plant bg-remover` adapts the script to fit (rename, relocate, wire to the target's CLI conventions).

If `:capture` and `:plant` work end-to-end on this case, the v1 is real.

## Open questions worth nailing before code

1. **What is a "feature" exactly?** A folder is easy. A function buried in a 3000-line file is hard. v1 should support folder/file/glob; "selection within a file" can come later or never.
2. **Versioning.** Features evolve. Re-capturing the same name should bump a version (`bg-remover/v2/`) and keep v1 around. `:plant` defaults to latest, accepts `--version`.
3. **Library naming + dedup.** Autonomous proposes a slug, human accepts or overrides. `:list` surfaces near-duplicates so the shelf doesn't sprawl.
4. **Cross-language plant.** Spec-driven re-implementation when languages don't match is the hard mode. v1 might gracefully decline and surface the bundle for the human to port manually. Honest > magical.
5. **Interview triggers.** When does autonomous *not* know enough to skip the interview? Heuristic: if `notes.md` ends up empty after autonomous-only capture, force the interview. Empty notes means we didn't capture WHY.
6. **Shelf privacy.** The library is local-only by default. Sharing/syncing across machines is a v2 concern; don't over-design it now.

## What this is NOT

- Not a marketplace. (That's `vibe-plugins`.)
- Not a snippet manager. (Snippets don't carry intent.)
- Not a templating engine. (Templates are abstract; this captures concrete features.)
- Not a codemod tool. (Codemods rewrite in place; this transplants between repos.)

The closest neighbor is `vibe-cartographer`'s feature-mapping work — but Cart maps what *is*; vibe-taker captures what's *transferable*.

## Suggested next moves

1. **Validate the spec on paper.** Walk through the bg-remover capture mentally; does the bundle layout cover everything you'd want? Adjust before code.
2. **Decide the plugin home.** Solo repo `vibe-taker` (consistent with the others) — create empty, scaffold via `plugin-dev:create-plugin`, develop on `main`, tag for stable promotion when v1 lands.
3. **Build `:capture` first.** It's the harder half (autonomous read + interview gate). `:plant` is mostly mechanical once the bundle schema is locked.
4. **Test case is the bg-remover.** Don't write any other tests until that one works end-to-end.
