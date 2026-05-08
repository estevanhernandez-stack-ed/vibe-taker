---
name: vibe-taker-plant
description: Plant a captured bundle from the shelf into the current repo. Detects target stack, picks code-lift (high match) or spec-driven (low match) or declines (hard mismatch). Always shows the diff before any write.
---

# vibe-taker — plant skill

> Implements [`spec.md > Plant Flow Architecture`](../../docs/spec.md#plant-flow-architecture) and [`prd.md > Epic: Plant`](../../docs/prd.md#epic-plant).

The mostly-mechanical half — once the bundle schema is locked, plant reads, detects, decides, stages, confirms, writes. The mandatory checkpoint is the diff `[y/N]`. **No file is written without explicit user confirmation.**

## Loading order — do this every time the skill fires

1. **Read** [`skills/guide/SKILL.md`](../guide/SKILL.md) — voice, hygiene, references catalog.
2. **Read** [`skills/guide/references/bundle-schema.md`](../guide/references/bundle-schema.md) — what the bundle's contract.json carries.
3. **Read** [`skills/guide/references/stack-match.md`](../guide/references/stack-match.md) — the decision tree, framework families, decline message.
4. **Read** [`skills/guide/references/error-contract.md`](../guide/references/error-contract.md) — class-0/1/2 outcome shapes.

Then execute the phases below in order.

## Argument parsing

Form: `/vibe-taker:plant <name> [--version=vX]`.

- `<name>` — required. The bundle slug.
- `--version=vX` — optional. If absent, plant uses `index.json.bundles[i].latest_version`.

Reject any other flags in v1 (no `--yes`, no `--shelf-path` per KTD-6/KTD-7). Print:

```
[exit 1] Unknown flag `<flag>`. v1 supports: `<name>` [--version=vX]
```

## Phase 1 — bundle load

1. **Read** `~/.vibe-taker/library/index.json`. If absent or unparseable JSON, exit class-2:

   ```
   [exit 2] Library index missing or corrupt at ~/.vibe-taker/library/index.json. Re-capture a feature to rebuild, or restore from backup.
   ```

2. **Validate** the index against `skills/guide/schemas/index.schema.json`. Same class-2 path on validation failure with the schema error appended.

3. **Find** the entry whose `name == <input-name>` (exact, case-sensitive). On absent:

   ```
   [exit 1] No bundle named '<name>' on the shelf. Run `/vibe-taker:list` to see what's available.
   ```

4. **Resolve version:**
   - If `--version=vX` was passed, look up the matching entry in `versions[]`. On absent:

     ```
     [exit 1] Bundle `<name>` exists but version `<vX>` not found. Available: <comma-separated versions>.
     ```

   - If `--version` was absent, use `latest_version`.

5. **Read** `~/.vibe-taker/library/<name>/<version>/contract.json`. Parse JSON.
6. **Validate** the contract against `skills/guide/schemas/contract.schema.json`. On validation failure, exit class-2:

   ```
   [exit 2] Bundle `<bundle-path>/contract.json` failed schema validation: <error>. Hand-edit the file or re-capture the source.
   ```

7. Carry `contract.language`, `contract.framework`, `contract.interface_kind`, `contract.entry_points`, `contract.env_vars` into the working state for downstream phases.

## Phase 2 — target stack detect

Walk the **current working directory** (and one level up if cwd has nothing) for manifests, in priority order:

| Manifest | Implies | Framework derivation |
|---|---|---|
| `package.json` (with `"type": "module"` OR `.ts` files anywhere in cwd tree) | Node — TypeScript or JavaScript | Read `dependencies` for highest-signal dep: `express`/`fastify`/`hapi`/`koa` (web/server), `react`/`vue`/`svelte` (web/client), `next`/`nuxt` (web/fullstack), `yargs`/`commander`/`oclif` (CLI). |
| `pyproject.toml` / `requirements.txt` / `setup.py` | Python | Read deps for `fastapi`/`flask`/`django` (web), `pandas`/`jupyter` (data), `click`/`typer`/explicit `argparse` usage in entry points (CLI). |
| `Cargo.toml` | Rust | `[dependencies]` lookup for `actix-web`/`rocket` (web), `clap` (CLI). |
| `go.mod` | Go | `require` block: `gin`/`echo` (web), `cobra`/`urfave/cli` (CLI). |
| `*.csproj` / `*.sln` | C# | XML `<PackageReference>` lookup. |
| `Gemfile` | Ruby | Gemfile parse for `rails`/`sinatra`. |
| `composer.json` | PHP | `require` lookup. |

If multiple manifests co-exist (monorepo), pick the one closest to cwd (cwd wins over parent). Carry `target.language`, `target.framework`, `target.framework_family`.

If **no manifest detected** in cwd or one level up: set `target.language = null`, `target.framework = null`. The decision tree handles this as the no-manifest fallback.

## Phase 3 — decision tree

Apply the table from [`stack-match.md`](../guide/references/stack-match.md):

```
match_level = compute_match(contract.language, contract.framework, target.language, target.framework, target.framework_family)
```

Where:

- **High** — `contract.language == target.language` AND same framework family. Mode: `code-lift`. (v1 ships zero adapters; same-language same-family code-lift keeps the source's framework choice.)
- **Low** — `contract.language == target.language`, different framework family. Mode: `spec-driven`.
- **Hard** — `contract.language != target.language` (and target.language is not null). Mode: `decline`.
- **Fallback** — `target.language is null` (no manifest). Mode: `spec-driven` with notice.

The chosen `mode` and `match_level` are named in the diff header (Phase 7).

## Phase 4 — hard-mismatch decline path

Triggered when `match_level == "hard"`. **No file is written.**

Print verbatim, substituting `<source-lang>` (= `contract.language`), `<target-lang>` (= `target.language`), `<bundle-path>` (= `~/.vibe-taker/library/<name>/<version>/`):

```
vibe-taker bundles capture <source-lang>; your target repo is <target-lang>. v1 doesn't auto-port across languages — too lossy. Here's the architecture sketch (<bundle-path>/architecture.md) and reference code (<bundle-path>/reference/); port manually, or capture a <target-lang>-native version of this feature into a new bundle.
```

Exit class-1.

## Phase 5 — no-manifest fallback notice

Triggered when `match_level == "fallback"`. Print before continuing into spec-driven mode (Phase 6 in item 8):

```
No manifest detected in target — falling back to spec-driven re-implementation. Reference code in <bundle-path>/reference/ for guidance.
```

Then proceed to Phase 6 (item 8) with `mode = spec-driven`, `match_level = fallback`.

## Decision header — render at the top of the diff

When Phases 1-3 leave us in `code-lift` (high) or `spec-driven` (low or fallback), the diff (rendered in Phase 7, item 8) is preceded by:

```
Mode: <code-lift | spec-driven>
Stack match: <high | low | hard-decline | fallback>
Bundle: <name> <version>  ·  source: <contract.language>/<contract.framework or none>
Target: <target.language or "no manifest">/<target.framework or "—">
```

This is what the user reads before answering the `[y/N]` prompt.

## Phase boundary — items 7/8

Phases 1-5 land at one of:

- **Class-1 decline** (hard mismatch) — exit clean, no further work.
- **Header printed** with `mode`, `match_level`, ready for code-lift or spec-driven generation in Phase 6 (item 8).

Item 8 picks up at Phase 6 and runs through the diff render, the mandatory `[y/N]` checkpoint, the per-file atomic write, and the dashboard decision-log integration.

<!-- ITEM 7 BOUNDARY — phases below land in item 8. -->
