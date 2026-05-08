<!-- /spec output for vibe-taker (Cart cycle #15).
     Generated 2026-05-07 in autonomous mode.
     Inputs: docs/prd.md, docs/scope.md, docs/spec-substrate.md, docs/builder-profile.md.
     Architecture reference: the existing six marketplace plugins (vibe-cartographer, vibe-doc, vibe-iterate, vibe-test, vibe-sec, vibe-thesis) — particularly vibe-cartographer (closest stylistic neighbor) and vibe-iterate (closest functional neighbor for cross-repo state).
     Patterns applied:
       - (mm) Spec-first — substrate + PRD carry the input load; spec converts product surface into technical contract.
       - (k) Enterprise bundle as single decision — the bundle schema IS the contract surface; lock it once, version it on change.
     Resolves PRD open questions: OQ-1 (versioning prompt), OQ-3 (stack-match thresholds), OQ-6 (storage path override).
     Defers to v2 / post-ship: OQ-2 (similarity threshold tuning), OQ-4 (--yes flag), OQ-5 (interview-gate threshold tuning), OQ-7 (shell completion). -->

# vibe-taker — Technical Spec

> **Take it with you.** Capture a feature out of one repo as a portable bundle; plant it into another and adapt to the destination stack.

This spec converts the four PRD epics (Capture / Plant / Library management / Bundle schema) into a technical blueprint: stack, plugin source layout, bundle schema, capture algorithm, plant decision tree, error contract, and deployment shape. Every section cross-references the PRD epic it implements.

## Stack

vibe-taker is a **markdown-driven Claude Code plugin** — same shape as the other six plugins on the marketplace storefront. No standalone runtime binary. No Node CLI. No Python entry point.

- **Plugin language: Markdown.** SKILL files instruct the agent; the agent does the work via its native tools (`Bash`, `Read`, `Write`, `Glob`, `Grep`).
- **Manifest:** [`plugin.json`](https://docs.claude.com/en/docs/claude-code/plugins) under `.claude-plugin/`. Schema: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`. Matches the six-plugin pattern exactly.
- **No runtime dependencies installed by the plugin.** Anything we touch (manifests, source files, bundle artifacts) is plain text — JSON, Markdown, source code in whatever language the source repo writes. The plugin reads and writes files; it doesn't compile or execute foreign code.
- **Rationale (Architect read):** The six existing plugins prove this shape is the right primitive. Adding a Node script or Python entry point would create a divergent install path (npm/pip alongside plugin install) and double the surface that can break. Reading and writing files via the agent is the entire job; writing a runtime to wrap that adds plumbing without buying anything.

External tool we touch but don't depend on:

- **626Labs Dashboard MCP** (`mcp__626Labs__manage_decisions`) — opt-in for plant-time decision logging (PRD Plant story 5). Plant succeeds silently if the MCP is unavailable. **No hard dependency.**

## Runtime & Deployment

- **Where it runs:** Anywhere Claude Code does — CLI, VS Code/JetBrains IDE extension, Cowork. The plugin doesn't care which surface invokes it.
- **OS support:** Cross-platform via `~`-prefix path resolution. Windows uses `%USERPROFILE%`; macOS/Linux use `$HOME`. The agent's filesystem tools normalize this.
- **Solo repo:** [`estevanhernandez-stack-ed/vibe-taker`](https://github.com/estevanhernandez-stack-ed/vibe-taker) — canary channel; `main` is bleeding-edge.
- **Marketplace ref:** Pin in [`vibe-plugins/.claude-plugin/marketplace.json`](https://github.com/estevanhernandez-stack-ed/vibe-plugins) — stable channel; bumped via tag.
- **Tag scheme:** plain `vX.Y.Z` (matches Cart, Doc, Thesis Engine; not the `<plugin>-vX.Y.Z` form used by Test and Sec).
- **Promotion ritual:** `marketplace.json` ref bump only. Never edit both repos in parallel (per `vibe-plugins/CLAUDE.md` "What NOT to do").

See `## Deployment — Identity & Signing` below for the per-target field capture.

## Architecture Overview

Three slash commands invoke three skills. Skills read and write to two filesystem locations: the user's repo (capture source / plant target) and the cross-repo shelf at `~/.vibe-taker/library/`.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Claude Code session                          │
│                                                                      │
│   /vibe-taker:capture <path|glob>                                    │
│   /vibe-taker:plant <name>                                           │
│   /vibe-taker:list [--search Q] [--sort name|lang]                   │
│                            │                                         │
│                            ▼                                         │
│   plugins/vibe-taker/skills/{capture,plant,list}/SKILL.md            │
│                            │                                         │
│         ┌──────────────────┼──────────────────┐                      │
│         ▼                  ▼                  ▼                      │
│   ┌──────────┐       ┌──────────┐       ┌──────────┐                 │
│   │ capture  │       │  plant   │       │   list   │                 │
│   └────┬─────┘       └────┬─────┘       └────┬─────┘                 │
│        │                  │                  │                       │
│        ▼                  ▼                  ▼                       │
└────────┼──────────────────┼──────────────────┼───────────────────────┘
         │                  │                  │
         │   ┌──────────────┴──────────┐       │
         ▼   ▼                         ▼       ▼
┌────────────────────────┐    ┌─────────────────────────────────────┐
│  Source / target repo  │    │  ~/.vibe-taker/library/             │
│  (current working dir) │    │  ├── <name>/v1/                     │
│                        │    │  │   ├── README.md                  │
│  reads: source files,  │    │  │   ├── architecture.md            │
│         manifests      │    │  │   ├── contract.json              │
│  writes: planted files │    │  │   ├── prompts/*                  │
│         (after diff)   │    │  │   ├── reference/...              │
│                        │    │  │   └── notes.md                   │
└────────────────────────┘    │  ├── <name>/v2/...                  │
         │                    │  └── index.json                     │
         │                    └─────────────────────────────────────┘
         │ optional, plant-time
         ▼
┌────────────────────────┐
│ 626Labs Dashboard MCP  │
│ manage_decisions(log)  │
└────────────────────────┘
```

**Data flow at a glance:**

- **Capture:** target path → autonomous read → snapshot + analysis → bundle on shelf. One direction. Source repo is read-only.
- **Plant:** bundle on shelf → stack-detect target → stage diff → confirm → write to target repo. Source repo is read-only; target repo is written only after explicit confirmation.
- **List:** `index.json` → terminal stdout. No writes.

## Plugin Source Layout

Mirrors the six-plugin convention. New folders only when they earn their place.

```
vibe-taker/                                    # solo repo root
├── .claude-plugin/
│   └── plugin.json                            # manifest
├── commands/
│   ├── capture.md                             # /vibe-taker:capture
│   ├── plant.md                               # /vibe-taker:plant
│   └── list.md                                # /vibe-taker:list
├── skills/
│   ├── guide/
│   │   ├── SKILL.md                           # shared behavior, persona, voice — internal-only
│   │   ├── references/
│   │   │   ├── bundle-schema.md               # contract.json + index.json + artifact shapes
│   │   │   ├── stack-match.md                 # framework-family table (OQ-3 resolution)
│   │   │   ├── secret-patterns.md             # files to skip at capture time
│   │   │   ├── interview-gate.md              # "3 substantive notes" heuristic + threshold notes
│   │   │   └── error-contract.md              # exit semantics by failure class
│   │   ├── schemas/
│   │   │   ├── contract.schema.json           # JSON Schema for contract.json
│   │   │   └── index.schema.json              # JSON Schema for index.json
│   │   └── templates/
│   │       ├── README.md.template             # bundle README scaffold
│   │       ├── architecture.md.template       # bundle architecture scaffold
│   │       └── notes.md.template              # bundle notes scaffold
│   ├── capture/
│   │   └── SKILL.md
│   ├── plant/
│   │   └── SKILL.md
│   ├── list/
│   │   └── SKILL.md
│   ├── session-logger/                        # placeholder — architecturally compatible, not load-bearing v1
│   │   └── SKILL.md
│   └── friction-logger/                       # placeholder — architecturally compatible, not load-bearing v1
│       └── SKILL.md
├── docs/                                      # planning artifacts (this file lives here too)
│   ├── builder-profile.md
│   ├── scope.md
│   ├── prd.md
│   ├── spec.md
│   └── spec-substrate.md
├── process-notes.md                           # process journal
├── README.md                                  # marketplace storefront copy
└── LICENSE                                    # MIT
```

**Sourcing constraints:**

- `commands/<name>.md` — three-line frontmatter (`description`, `argument-hint`) plus a one-paragraph body that defers to the matching skill.
- `skills/<name>/SKILL.md` — full behavior. Reads `skills/guide/SKILL.md` for shared persona / voice / hygiene before doing the command's work.
- `skills/guide/SKILL.md` is **not** user-invocable (`user-invocable: false` in frontmatter); referenced by the three command skills only.
- `session-logger` and `friction-logger` ship as documented placeholders in v1 — they declare the contract (`start(command, project_dir)`, `log(entry)`) and the data path (`~/.claude/plugins/data/vibe-taker/`), but command skills do **not** invoke them in v1. v2 lights them up. **Architecturally compatible, not load-bearing.**

## Bundle Schema

> Implements `prd.md > Epic: Bundle schema`.

The bundle is the contract surface. Every downstream feature (versioning, sync, marketplace publishing if it ever happens) depends on this being stable. Lock the shape in v1; version the schema on any breaking change.

### Bundle directory layout

```
~/.vibe-taker/library/<feature-name>/<version>/
├── README.md            # human-readable: what it is, when to reach for it, intent
├── architecture.md      # components, data flow, key files in original
├── contract.json        # I/O surface: inputs, outputs, deps, env, language/framework
├── prompts/             # AI prompts if any; one file per prompt; empty dir if none
│   └── <name>.txt
├── reference/           # verbatim snapshot of original source — read-only truth
│   └── <preserved tree>
└── notes.md             # WHY this exists, gotchas, non-obvious tradeoffs
```

- `<feature-name>` is a slug (`[a-z0-9][a-z0-9-]*`) — autonomous proposes; user confirms during interview.
- `<version>` is `v1`, `v2`, … — bumped on re-capture (see [Versioning rules](#versioning-rules)).
- All six artifact paths exist on every bundle. Empty directories use a `.gitkeep`-style placeholder (`empty.txt` with a one-line note) so the absence is unambiguous.

### `contract.json` — load-bearing schema

> JSON Schema lives at `skills/guide/schemas/contract.schema.json`. The schema is the contract; this section is a readable summary.

**Required fields:**

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | `"1.0"` for v1. Bump on breaking change. |
| `name` | string | Slug; matches bundle directory name. |
| `version` | string | `"v1"`, `"v2"`, etc. — matches bundle subdirectory. |
| `language` | string | Primary language detected: `python` / `typescript` / `javascript` / `rust` / `go` / `csharp` / `ruby` / `bash` / `other:<name>`. |
| `framework` | string \| null | Detected framework: `fastapi`, `flask`, `express`, `nextjs`, `react`, `cli-argparse`, `cli-typer`, `cli-click`, `cli-yargs`, `cli-commander`, `none`, etc. `null` when no framework is detectable. |
| `interface_kind` | string | `cli` / `library` / `skill` / `script` / `service` / `bot` / `other`. |
| `inputs` | array of input objects | See input shape below. |
| `outputs` | array of output objects | See output shape below. |
| `dependencies` | array of strings | Package names with version specifiers when discoverable (e.g., `"requests>=2.28"`). Pulled from manifest. |
| `env_vars` | array of env-var objects | See env-var shape below. |
| `source_repo` | string | URL or local path of the source repo at capture time. |
| `source_path` | string | Relative path within `source_repo` of the captured target. |
| `captured_at` | string (ISO 8601) | Capture timestamp. |
| `entry_points` | array of strings | File paths within `reference/` that are program entry points (CLI scripts, exported main functions, etc.). |

**Optional fields:**

| Field | Type | Notes |
|---|---|---|
| `tags` | array of strings | User-supplied search tags. Mirrored in `index.json`. |
| `summary` | string | One-line autonomous-or-interview-supplied summary. Mirrored in `index.json`. |
| `notes_completeness` | object | `{ "substantive_count": int, "interview_fired": bool }` — diagnostics for the interview-gate heuristic. |

**Input object shape:**

```json
{ "name": "image_path", "type": "path", "required": true, "description": "Path to source image" }
```

`type` is one of: `path` / `string` / `int` / `float` / `bool` / `enum:<v1>|<v2>|...` / `stdin` / `flag` / `other`.

**Output object shape:**

```json
{ "name": "transparent_image", "type": "path", "description": "Output path for transparent-bg image" }
```

**Env-var object shape:**

```json
{ "name": "OPENAI_API_KEY", "load_bearing": true, "description": "API key for the bg-removal model" }
```

`load_bearing: true` means the feature won't function without this env var. Plant-time prompts the user to provide if missing in target.

### `index.json` — shelf manifest

> JSON Schema lives at `skills/guide/schemas/index.schema.json`. Pretty-printed, 2-space indent, max ~200 bytes per entry (PRD Bundle-schema story 2).

**Top-level shape:**

```json
{
  "schema_version": "1.0",
  "bundles": [
    {
      "name": "bg-remover",
      "latest_version": "v2",
      "versions": [
        { "version": "v1", "captured_at": "2026-04-30T14:22:01Z", "source_repo": "https://github.com/626labs/hub", "source_path": "tools/bg-remove/" },
        { "version": "v2", "captured_at": "2026-05-07T09:11:43Z", "source_repo": "https://github.com/626labs/hub", "source_path": "tools/bg-remove/" }
      ],
      "tags": ["cli", "image", "ai"],
      "summary": "AI-powered CLI background remover. Takes an image path, returns transparent-bg version.",
      "language": "python",
      "framework": "cli-argparse"
    }
  ]
}
```

- `bundles` is an array, not a map — preserves user-visible ordering and survives hand-edits cleanly.
- `latest_version` is what `:plant <name>` (without `--version`) selects.
- `versions[]` is append-only in normal flow; only `:capture` writes to it, only with `mv`-atomic semantics (see [Atomic writes](#atomic-writes)).

### `architecture.md` — required structure

Every bundle's `architecture.md` opens with:

1. **Summary** (1-3 sentences) — what the feature is and what it does.
2. **Components** (heading) — name each entry point, helper, and external dependency.
3. **Data flow** (heading) — how data moves through the feature. ASCII or prose.

Empty sections are explicit (`None known.` / `Single-file feature — no internal components.`), never absent. PRD Bundle-schema story 1 is the contract.

### `notes.md` — required structure

Every bundle's `notes.md` opens with at minimum:

1. **Why this exists** — autonomous-derived from source `README.md`-like prose, or interview-supplied. Never empty.
2. **Gotchas** — non-obvious tradeoffs, library quirks, known issues. `None known.` is acceptable.

`notes_completeness.substantive_count` in `contract.json` reflects how many gotcha-bullets cleared the heuristic threshold.

### `README.md` — bundle entry point

Renders cleanly on GitHub if the bundle is ever published. Sections:

1. **What it is** (one paragraph).
2. **When to reach for it** (one paragraph).
3. **Plant** — the literal command (`/vibe-taker:plant <name>`).
4. **Reference** — link to `reference/` for the source-of-truth files.

### `prompts/` — AI prompt extraction

When the captured feature calls an LLM, every system prompt and user-template prompt gets extracted into `prompts/<descriptive-name>.txt` verbatim. Detection heuristic: any string literal **>100 chars** passed to a known LLM SDK call (OpenAI, Anthropic, Cohere, Bedrock client, Ollama HTTP request, etc.). False negatives are acceptable in v1 — interview gate fires if `prompts/` is empty *and* dependencies include an LLM SDK.

### Versioning rules (resolves OQ-1)

**Decision: prompt user before bumping.** PRD default holds.

- On `:capture`, after autonomous read produces a proposed slug, check `index.json` for an existing entry with that name.
- If found, the agent prints: *"<name> already on the shelf at <path>. Bump to <next-version>? [y/N]"*
- On `y`, the new bundle goes to `<name>/v<n+1>/`. If the existing bundle was at `<name>/` with no version subdirectory (legacy / first-write), the agent first moves it to `<name>/v1/` and updates `index.json` accordingly, then writes the new bundle to `<name>/v2/`.
- On `n` or empty input, the command exits with no changes and prints the path of the existing bundle.
- **No `--auto-bump` flag in v1.** Reason: the bundle schema is still calibrating; false-bumps are cheaper to recover from with a prompt than with a delete-and-recapture cycle. Tunable post-ship without schema change.

## Library Shelf — `~/.vibe-taker/library/`

> Implements `prd.md > Epic: Library management`.

### Filesystem layout

```
~/.vibe-taker/
├── README.md                          # auto-created on first capture; privacy notice
├── library/
│   ├── <feature-name>/
│   │   └── <version>/                 # see Bundle directory layout
│   ├── ...
│   ├── index.json                     # shelf manifest
│   └── .staging/                      # temp dir for atomic writes (never user-facing)
└── (no config.json in v1 — see OQ-6 resolution)
```

### Atomic writes

All writes that cross more than one file use a stage-and-move pattern:

1. **Bundle capture:** write the new bundle into `~/.vibe-taker/library/.staging/<name>-<version>-<unix-timestamp>/`. On success of every write, `mv` the staging directory to its final destination.
2. **Index update:** write the modified index to `~/.vibe-taker/library/index.json.tmp`. On success, `mv index.json.tmp index.json`.

Result: a half-written bundle never lands on the shelf. A crash mid-capture leaves a stranded `.staging/` directory that the next `:capture` cleans up (any `.staging/<*>` older than 1 hour is removed at start).

### Privacy default — local only (resolves OQ-6)

**Decision: hardcoded `~/.vibe-taker/library/`. No `--shelf-path` override in v1.** PRD default holds.

- First-ever `:capture` writes `~/.vibe-taker/README.md` if absent, with the notice from PRD Library-management story 4.
- Same notice prints to stdout on the first run.
- Cross-machine sync is v2; locking the path in v1 keeps the migration path clean (move the whole `~/.vibe-taker/` directory wholesale, no per-config rewriting).

## Capture Flow Architecture

> Implements `prd.md > Epic: Capture`.

Skill location: `plugins/vibe-taker/skills/capture/SKILL.md`. Invoked by `commands/capture.md` (`/vibe-taker:capture <path|glob>`).

### 1. Target resolution

| Input pattern | Resolution | Behavior |
|---|---|---|
| Single file (`scripts/foo.py`) | One file | `reference/foo.py`. `architecture.md` notes "single-file feature." |
| Folder (`apps/bg-remover/`) | Recursive read of folder | Preserve relative tree under `reference/<basename>/`. |
| Glob (`packages/auth/**`) | All matches under glob root | Preserve relative tree under `reference/` from glob root. Empty match → exit 1, "no files matched" error. |
| In-file selector (`file.py:120-180`) | Decline | Exit 1 with the message in PRD Capture story 4. **No bundle written.** |

The agent must verify the target exists before any bundle is staged. If the path doesn't exist (and isn't a glob), exit 1 with the missing-path error.

### 2. Autonomous read pass

Sequence (no interview yet):

1. **Walk** every file in scope. For each: extension + content sniff for language.
2. **Detect manifests** at any level of the captured tree: `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `*.csproj`, `Gemfile`, `go.mod`. Extract `language` and `framework` and `dependencies`.
3. **Identify entry points** — heuristic by language:
    - Python: files containing `if __name__ == "__main__"`, files registered as `[project.scripts]` in `pyproject.toml`, or single-file scripts with shebangs.
    - Node: files referenced under `"bin"` in `package.json`, files with shebangs, or `index.{js,ts}` at the root.
    - Other: shebanged files; files matching `main.*`, `cli.*`, `__main__.*`.
4. **Extract I/O surface** by static read:
    - **Inputs:** argparse / Typer / Click / yargs / Commander declarations → input objects with name, type, required-flag, description (from help string when present).
    - **Outputs:** writes to `sys.stdout`, file-write calls with explicit paths, return values from named main functions.
    - **Env vars:** regex-grep for `os.environ` / `os.getenv` / `process.env.<X>` / `Deno.env` / `getenv("...")`.
5. **Extract prompts** — strings >100 chars passed to recognized LLM SDK calls. Save each to `prompts/<descriptive-name>.txt`.
6. **Extract intent** — read every `README.md`, `CHANGELOG.md`, top-of-file docstring, top-of-file comment block. Build `notes.md > Why this exists` from this material; build `architecture.md > Summary` from the intersection of source README + entry-point docstrings.
7. **Detect known gotchas** — pattern-match on dependency names against a small known list:
    - `sharp` → "native binding; check Apple Silicon support."
    - `pillow` → "may need libjpeg/zlib system libs at install."
    - `playwright` → "first-run downloads browser binaries; ~300MB."
    - `tensorflow` / `torch` → "GPU optional; CPU fallback can be slow."
    - Any package containing `aws`, `gcp`, `azure` → "cloud SDK; check default region behavior."
    - Add to `notes.md > Gotchas` when matched.

This is the "autonomous-extracted" layer that PRD Capture story 5 expects.

### 3. Interview gate (resolves heuristic threshold for OQ-5)

Fires when **any** of:

- `notes.md > Gotchas` count is < 3 substantive items.
- `architecture.md > Summary` could not be derived (no source README, no top-of-file docstring on any entry point).
- `prompts/` is empty AND the captured dependencies include an LLM SDK (likely missed extraction).
- Autonomous-proposed slug collides with an existing `index.json` entry (versioning prompt firing implies an interactive interview anyway — fold the questions in).

**"Substantive item" definition:** line length ≥30 chars, AND not a near-duplicate (Levenshtein < 8) of any line already in `architecture.md`. Stored in `contract.json.notes_completeness.substantive_count` for diagnostic carry to `/reflect`.

When the gate fires, the interview asks **at most 4** questions, one at a time:

1. **What is this for?** (intent — not what the code does, why it exists)
2. **Shelf name** — autonomous proposes; user confirms or overrides.
3. **Non-obvious tradeoffs to preserve** — anything the spec should remember.
4. **Tags** — for search.

When the gate doesn't fire, the agent prints "intent derived autonomously — bundle ready at <path>; edit `notes.md` if anything's missing." (PRD Capture story 6 final criterion.)

### 4. Bundle generation

Templates in `skills/guide/templates/`. Filled in from autonomous-extracted + interview-supplied material:

- `README.md.template` → `<bundle>/README.md`
- `architecture.md.template` → `<bundle>/architecture.md`
- `notes.md.template` → `<bundle>/notes.md`
- `contract.json` → built directly from analysis (no template — pure data).
- `prompts/*.txt` → written verbatim from extraction.
- `reference/` → `cp -R` of the captured source.

All written into `~/.vibe-taker/library/.staging/<name>-<version>-<unix-timestamp>/`, then `mv`'d to final once every file is in place.

### 5. Versioning detection

Implemented at the top of capture, before any staging:

- Read `index.json`. Look for an entry whose `name` matches the autonomous-proposed slug.
- If found and the `versions[]` array is non-empty, fire the bump prompt (see [Versioning rules](#versioning-rules-resolves-oq-1)).
- The interview folds shelf-name confirmation into question 2 — user can override the slug to side-step the collision.

### 6. Secret-file skip

Glob patterns matched at scan time:

```
.env
.env.*
*.pem
*.key
id_rsa
id_rsa.*
*credentials*
*secret*
```

Patterns live in `skills/guide/references/secret-patterns.md` so they evolve without an SKILL edit.

- Matched files are skipped silently from `reference/` and listed in stdout.
- **Load-bearing detection:** if a skipped file's basename (minus extension) appears in any imported / required / `dotenv.config()`-like call within the rest of the captured tree, it's load-bearing. Add to `contract.json.env_vars` as a stub (`{"name": "...", "load_bearing": true, "description": "Inferred from <captured-file>; provide at plant-time."}`) and warn per PRD Capture story 8.

### Capture exit codes (conceptual contract)

The skill is markdown, not a binary — but the agent's printed outcome corresponds to:

- `0` — bundle written, summary printed.
- `1` — user-facing decline (target not found, glob no-match, in-file selector, name-conflict declined).
- `2` — schema/internal failure (write error, index-corrupt). Always print actionable recovery.

## Plant Flow Architecture

> Implements `prd.md > Epic: Plant`.

Skill location: `plugins/vibe-taker/skills/plant/SKILL.md`. Invoked by `commands/plant.md` (`/vibe-taker:plant <name> [--version=vX]`).

### 1. Bundle load

- Read `~/.vibe-taker/library/index.json`. Find entry by `name` (exact, case-sensitive).
- If absent: exit 1 with "no bundle named '<name>' on the shelf. Run `/vibe-taker:list` to see what's available."
- Resolve version: `--version=vX` if provided and present; else `latest_version`.
- Read `<bundle>/contract.json`. Validate against `contract.schema.json`. On invalid, exit 2 with the schema error and the bundle path.

### 2. Stack detect

Walk the current working directory (one level up if needed) for manifests. Detection priority (first match wins for primary language; multiple manifests can co-exist for monorepos):

| Manifest | Implies |
|---|---|
| `package.json` (with `"type": "module"` or `.ts` files) | Node — TypeScript or JavaScript |
| `pyproject.toml` / `requirements.txt` / `setup.py` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `*.csproj` / `*.sln` | C# |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| (none) | Stack unknown |

Within the primary-language manifest, extract framework (e.g., `package.json` deps containing `express` / `fastify` / `next` / `vite`).

### 3. Stack-match decision tree (resolves OQ-3)

> Reference table lives at `skills/guide/references/stack-match.md`.

| Source language | Target language | Source framework family | Target framework family | Match level | Plant mode |
|---|---|---|---|---|---|
| Python | Python | Web (FastAPI/Flask/Django) | Web (any of those) | High | code-lift |
| Python | Python | CLI (argparse/Typer/Click) | CLI (any of those) | High | code-lift with arg-parser adapter |
| Python | Python | Data (pandas/jupyter) | Data (any) | High | code-lift |
| Python | Python | Web | CLI | Low | spec-driven |
| Python | Python | (no framework) | (no framework) | High | code-lift |
| Node | Node | Web (Express/Hapi/Koa/Fastify) | Web (any of those) | High | code-lift |
| Node | Node | CLI (yargs/Commander) | CLI (any of those) | High | code-lift |
| Node | Node | React | Vue / Svelte | Low | spec-driven |
| Node | Node | Next.js | Vite + React | Low | spec-driven |
| Rust | Rust | (any) | (any) | High | code-lift |
| Go | Go | (any) | (any) | High | code-lift |
| Python | Node | * | * | Hard | decline |
| Node | Python | * | * | Hard | decline |
| * | * | * | * (different language) | Hard | decline |
| * | (no manifest detected) | * | n/a | Low (fallback) | spec-driven, with notice |

**Framework-family taxonomy:**

- **Web / server:** Express, Fastify, Hapi, Koa, FastAPI, Flask, Django, Sinatra, Rails, Gin, Actix, Rocket.
- **Web / client:** React, Vue, Svelte, Solid, Angular.
- **Web / fullstack:** Next.js, Nuxt, SvelteKit, Remix.
- **CLI:** argparse, Typer, Click (Python); yargs, Commander, Oclif (Node); Cobra (Go); Clap (Rust).
- **Data / ML:** pandas, NumPy, Jupyter, scikit-learn, PyTorch, TensorFlow.
- **Build tooling:** Vite, esbuild, Webpack, Parcel, Rollup, Turbopack.
- **Game / 3D:** Three.js, R3F, Babylon, Unity (C#), Roblox/Luau.
- **Mobile:** React Native, Expo, Flutter.

Same family → high match. Different family same language → low match. Different language → hard.

The chosen mode is named in the diff header (PRD Plant story 2 final criterion): *"Mode: code-lift (high stack match — Node→Node, Express→Fastify framework adapter)"* or *"Mode: spec-driven (low stack match — Python web feature → Python CLI target)"*.

### 4. Code-lift mode

Used on **high** stack match.

1. Copy `<bundle>/reference/` files into the target, preserving relative tree under a target-conventional location:
    - Python with `pyproject.toml` + a top-level `src/<package>/` → place files under `src/<package>/<feature>/`.
    - Node with `src/` → `src/<feature>/`.
    - No conventional location → root of target with a `<feature>/` directory.
2. Rewrite imports:
    - Python: `from .` and `from <pkg>.` paths adjusted to target package name from `pyproject.toml`'s `[project].name` or `[tool.poetry].name`.
    - Node: `import './<rel>'` paths adjusted to target's `tsconfig.json#paths` if present, else relative.
3. Adapt within-family framework call sites only when an adapter exists (e.g., `argparse` → `Typer` migration of one flag declaration). When no adapter is wired, fall back to spec-driven for that file.
4. Generate the diff.

### 5. Spec-driven mode

Used on **low** stack match (same language, different framework family) and on **no-manifest fallback**.

1. Read `<bundle>/architecture.md` + `<bundle>/contract.json` + `<bundle>/notes.md`.
2. Read `<bundle>/reference/` for shape and intent — but as a guide, not a copy source.
3. Generate fresh code in the target's stack matching the bundle's contract (same inputs, same outputs, same env vars).
4. Generate the diff.

### 6. Hard-mismatch decline

Used on **different language**.

- Print the message from PRD Plant story 3 verbatim, with bundle paths interpolated.
- **No file is written.** Exit 1.
- Recovery path is in the message: surface `architecture.md` + `reference/` for manual port, or capture a target-language-native version into a new bundle.

### 7. Diff confirmation

Single mandatory checkpoint. PRD Plant story 1 is explicit: *"No file is written without explicit user confirmation."*

- Stage all writes in memory (or a temp directory under the target — `.vibe-taker-staging/` ignored via session-only convention; never committed).
- Render the unified diff to stdout. Header line names the mode and stack-match level.
- Prompt: *"Apply this diff? [y/N]"*. On `n` or empty, exit 0 with no writes.
- On `y`, write each file. Atomic per-file (write to `<path>.tmp` + `mv`).

**No `--yes` flag in v1** (resolves OQ-4 deferral): the diff format itself is still being validated; auto-confirm before validating the format would let bad diffs land silently.

### 8. Dashboard decision-log integration

Opt-in / fail-silent. PRD Plant story 5.

- After successful plant, check whether `mcp__626Labs__manage_decisions` is in the agent's runtime tool list.
- If yes, call:

  ```
  action: log
  body:
    title: "Planted <bundle-name> v<version> into <target-repo-or-path>"
    description: |
      Source: <bundle.source_repo> (<bundle.source_path>)
      Target: <cwd>
      Mode: <code-lift | spec-driven>
      Stack match: <high | low | hard-decline-was-overridden>
    tags: ["vibe-taker", "plant", "<bundle.language>"]
    projectId: <bound-project-id-if-current-repo-bound-else-null>
  ```

- If the tool is unavailable, plant succeeds silently. **No retry, no error.**

### Plant exit codes (conceptual contract)

- `0` — diff applied, plant succeeded (or user declined diff).
- `1` — user-facing decline (bundle not found, hard mismatch, version not found).
- `2` — schema/internal failure (corrupt bundle, stack-detect error mid-flight). Print actionable recovery.

## List Flow Architecture

> Implements `prd.md > Epic: Library management`, stories 1-3.

Skill location: `plugins/vibe-taker/skills/list/SKILL.md`. Invoked by `commands/list.md` (`/vibe-taker:list [--search Q] [--sort name|lang]`).

### 1. Default print

- Read `~/.vibe-taker/library/index.json`. Validate against `index.schema.json`.
- If absent: exit 0 with "Library is empty. Run `/vibe-taker:capture <path>` to add your first bundle."
- If corrupt: exit 2 with "Library index missing or corrupt at <path>. Re-capture a feature to rebuild, or restore from backup."
- Print each bundle as one block:

  ```
  bg-remover (v2)        python · cli-argparse        2026-05-07
    AI-powered CLI background remover. Takes an image path, returns transparent-bg version.
    tags: cli, image, ai
  ```

- Default sort: `captured_at` of `latest_version` descending.

### 2. Search

`--search <query>` is case-insensitive substring match across:

- `name`
- `summary`
- `tags` (any tag matches)
- `source_repo`
- `language`

Empty result → "no matches" + exit 0.

### 3. Dedup hint — Jaccard similarity (resolves OQ-2 default)

**Decision: 70% Jaccard token similarity on summaries.** PRD default holds. Tunable post-ship without schema change.

- For each pair of bundles, compute Jaccard token similarity over `summary` strings (lowercase, split on non-alphanumeric, drop stop-words).
- If similarity ≥ 0.70, append `[similar to: <other-name>]` to both bundles' listings.
- Best-effort, runs at `:list` time only — never at `:capture` time. PRD Library-management story 3 is explicit on this.

### Sort flags

- `--sort=name` — alphabetical by `name`.
- `--sort=lang` — group by `language`, then alphabetical within group.
- (Default) — `captured_at` descending.

## Slash Command Surface

### `commands/capture.md`

```
---
description: "Capture a feature out of the current repo as a portable bundle on the cross-repo shelf."
argument-hint: "<path|file|glob> — folder, single file, or glob. In-file selectors not supported in v1."
---

Use the **capture** skill to lift the target feature into a portable bundle at `~/.vibe-taker/library/`.
Reads source, snapshots reference code, extracts architecture and contract, derives intent autonomously,
and only fires the interview gate when WHY can't be extracted from source alone.

**No prerequisites — `:capture` is the entry point of the round-trip.**
```

### `commands/plant.md`

```
---
description: "Plant a captured feature from the shelf into the current repo. Adapts to the destination stack."
argument-hint: "<name> [--version=vX] — bundle name, optional version pin (default: latest)."
---

Use the **plant** skill to drop the named bundle into the current repo.
Detects target stack, picks code-lift (high match) or spec-driven (low match) or declines (hard mismatch).
Always shows the diff and asks for confirmation before any write.

**Prerequisites:** The named bundle must exist on the shelf. Run `/vibe-taker:list` to see what's available.
```

### `commands/list.md`

```
---
description: "List bundles on the cross-repo shelf with one-line summaries. Supports search and sort."
argument-hint: "[--search <query>] [--sort name|lang]"
---

Use the **list** skill to surface what's on the shelf at `~/.vibe-taker/library/`.
Default sort is most-recently-captured first. Search is substring across name, summary, tags, source-repo, language.
Flags near-duplicates (≥70% summary similarity) so the shelf doesn't sprawl.

**No prerequisites.** If the library is empty, prints a message and exits.
```

## Skill Files

### `skills/guide/SKILL.md` — shared behavior

Internal-only (`user-invocable: false`). Loaded by every command skill before doing the command's work. Defines:

- **Voice and persona handling** — defer to user's `shared.preferences.persona` from `~/.claude/profiles/builder.json`, fall back to "builder-to-builder, second person, sentence case" baseline matching the rest of the marketplace.
- **Tier-1 hygiene rules** — output discipline (write-to-file before chat for any deliverable >300 words; in vibe-taker that's mostly never — most output is short stdout summaries), working-directory discipline (verify `pwd` before any cross-repo command), verify before synthesizing (when a sub-step's reading contradicts a prior reading, re-verify before incorporating).
- **Cross-references** — bundle-schema reference, stack-match reference, error contract.
- **Self-Evolving Plugin Framework hooks** — placeholder; v1 documents the contract, doesn't invoke.

### `skills/capture/SKILL.md`

Implements [Capture Flow Architecture](#capture-flow-architecture). Reads `skills/guide/SKILL.md` first. Uses `Bash` for filesystem ops, `Read` / `Glob` / `Grep` for source analysis, `Write` for bundle generation.

### `skills/plant/SKILL.md`

Implements [Plant Flow Architecture](#plant-flow-architecture). Reads `skills/guide/SKILL.md` first. Stack-detect via `Read` on manifests; diff render in stdout; writes via `Write` after explicit `[y/N]` confirmation.

### `skills/list/SKILL.md`

Implements [List Flow Architecture](#list-flow-architecture). Read-only — no writes. Reads `index.json`, formats stdout.

### `skills/session-logger/SKILL.md` — placeholder

Documents the contract:

- `start(command, project_dir)` returns a sessionUUID.
- Terminal append at command end with outcome + key decisions + artifact path.
- Data path: `~/.claude/plugins/data/vibe-taker/sessions/<date>.jsonl`.

In v1, command skills do **not** call this. Reserved for v2 (Self-Evolving Plugin Framework Level 2).

### `skills/friction-logger/SKILL.md` — placeholder

Documents the contract:

- `log(entry)` appends one JSON line per friction event.
- Triggers table lives at `skills/guide/references/friction-triggers.md` (also placeholder in v1).
- Data path: `~/.claude/plugins/data/vibe-taker/friction.jsonl`.

In v1, command skills do **not** call this. Reserved for v2 (Self-Evolving Plugin Framework Level 3).

## Self-Evolving Plugin Framework Compatibility

vibe-taker is **architecturally compatible** with the framework but does **not** implement Levels 2-3 in v1.

| Level | Pattern | v1 status |
|---|---|---|
| 1 | Profile (per-user, per-plugin) | Reads `shared.preferences.persona` from `~/.claude/profiles/builder.json` (read-only); no plugin-scoped block in v1. |
| 2 | Session logger | Skill placeholder + reserved data path. Not invoked. |
| 3 | Friction logger | Skill placeholder + reserved data path. Not invoked. |
| 4 | Memory decay | n/a in v1 (no plugin-scoped profile fields to decay). |
| 6 | Friction log read | n/a in v1 (no log to read). |
| 8 | Plugin self-test | n/a in v1; consider for v1.x post-ship. |
| 13 | Ecosystem-aware composition | Implemented for the Dashboard MCP (plant decision-log) — present-and-use vs absent-and-fail-silent. |
| 14 | Wins logger | n/a in v1. |

**Why placeholders, not full omission:** the data paths (`~/.claude/plugins/data/vibe-taker/...`) and skill folder names are reserved in v1 so v2 can light them up without a directory restructure. If we left them out entirely, v2 would need a migration step on user disks.

## Error / Exit-Code Conventions

> Reference: `skills/guide/references/error-contract.md`.

The plugin runs as markdown SKILLs, not as a process — so "exit codes" are the conceptual outcome the agent prints, not a literal `process.exit(N)`. Three classes:

| Class | Conceptual code | Examples | Recovery message required? |
|---|---|---|---|
| Success | `0` | Bundle written, plant applied, list printed, decline accepted by user. | No (success print is enough). |
| User-facing decline / soft failure | `1` | Target not found, glob no-match, in-file selector, name conflict declined, bundle not on shelf, hard language mismatch on plant. | Yes — the print includes the exact recovery action (run X, edit Y, capture Z). |
| Internal / schema failure | `2` | Index corrupt, contract.json schema invalid, write to shelf failed, mid-flight stack-detect crash. | Yes — print path, expected schema/state, recovery (re-capture, hand-edit, restore from backup). |

**Discipline rule:** every class-1 and class-2 exit MUST print a one-line recovery action. Bare error messages without actionable recovery are a bug — file it as friction at `/reflect`.

## Dependencies & External Services

vibe-taker is intentionally light on dependencies. The plugin itself depends on **Claude Code's native tools** (`Bash`, `Read`, `Write`, `Glob`, `Grep`, `Edit`). That's it.

External services touched at runtime:

| Service | Purpose | Optional? | Notes |
|---|---|---|---|
| 626Labs Dashboard MCP (`mcp__626Labs__manage_decisions`) | Plant-time decision log | Yes — plant succeeds silently if absent. | PRD Plant story 5; pattern #13. |

External services consumed by **bundles** (not by vibe-taker itself) at plant time depend on the bundle's `contract.json.env_vars` and `contract.json.dependencies`. vibe-taker surfaces them at plant-confirmation; the user provides them as part of their target repo's setup.

## Deployment — Identity & Signing

Target: **GitHub release** (canary `main` of `estevanhernandez-stack-ed/vibe-taker`) → `vibe-plugins` marketplace ref bump (stable).

| Field | Value |
|---|---|
| Repo slug | `estevanhernandez-stack-ed/vibe-taker` |
| Release tag scheme | `vX.Y.Z` (plain — matches Cart, Doc, Thesis Engine) |
| Signing | None (markdown plugin; no binary to sign) |
| `GITHUB_TOKEN` scope | `contents: write` for tag/release creation |
| Release-asset upload paths | n/a — plugin is consumed via repo ref, not asset download |
| Marketplace ref location | `vibe-plugins/.claude-plugin/marketplace.json` → `vibe-taker` entry pinned to a tag |

**Promotion ritual** (logged here so `/checklist` and `/build` honor it):

1. Cut and tag `vX.Y.Z` on `estevanhernandez-stack-ed/vibe-taker:main`.
2. Push the tag.
3. Create a GitHub release for the tag (release notes from the tag's commit messages).
4. In `vibe-plugins/`, edit `.claude-plugin/marketplace.json` to bump the `vibe-taker` entry's ref to the new tag. Commit. Push.
5. **Never edit both repos in parallel within the same session.** Per `vibe-plugins/CLAUDE.md` "What NOT to do."

`superpowers:vibe-launch` — if installed at `/build` time, defer release-cutting to it. PRD doesn't require it; if absent, the agent runs `gh release create` directly.

## Key Technical Decisions

Each is a fork point that downstream commands and reviewers should see explicitly.

### KTD-1 — Markdown-only plugin runtime

**Decision:** vibe-taker ships zero runtime executables. All logic lives in markdown SKILL files; the agent does file I/O via its native tools.

**Why:** Matches the six-plugin convention exactly. Adds no install path beyond plugin install. Halves the surface that can fail silently.

**Tradeoff accepted:** Heavier reasoning in SKILL prose (the agent has to follow the algorithm at run time, not call into a tested function). Mitigated by: explicit algorithm sections in this spec, a JSON Schema for `contract.json` so the agent has a typed target, and templates for the artifact files so the agent fills slots rather than improvising structure.

### KTD-2 — Bundle schema is the contract surface, locked in v1

**Decision:** `contract.json` schema, `index.json` schema, and the six-artifact bundle directory layout are the v1 contract. Every downstream feature (versioning bump, `:diff`, `:update`, sync, marketplace publishing if it ever happens) depends on this being stable. `schema_version: "1.0"` is reserved; bumps require a migration note.

**Why:** Per (k) Enterprise bundle as single decision — capturing the surface once, with all the fields the round-trip actually needs, is cheaper than retrofitting fields after second-feature capture. PRD Bundle-schema epic gates the v1 ship.

**Tradeoff accepted:** Extra fields in v1 that may go unused (e.g., `notes_completeness` is diagnostic, not load-bearing for any v1 flow). Future versions can deprecate; v1 prefers carrying spare capacity to needing a 1.1 schema bump in the first month.

### KTD-3 — Atomic write pattern (stage + `mv`)

**Decision:** All bundle writes go through `~/.vibe-taker/library/.staging/<name>-<version>-<unix-timestamp>/` then `mv` to final. `index.json` writes go through `index.json.tmp` then `mv`.

**Why:** A half-written bundle on the shelf is worse than a missing bundle — the user can't tell at a glance which artifacts are valid. Atomic moves make every shelf state internally consistent.

**Tradeoff accepted:** Extra disk I/O on capture (write-then-move vs write-in-place). Negligible in practice; bundle sizes are small (kilobytes to low megabytes).

### KTD-4 — Stack-match table is the truth, framework-family edges are conservative

**Decision:** Hard mismatch = different primary language exactly. Low match = same language, different framework family. High match requires same language *and* same framework family.

**Why:** Resolves OQ-3. Same-language-different-framework auto-translation (e.g., Express→FastAPI) is plausible but lossy in v1; declining gracefully and giving the user the spec to port manually is more honest. Cross-language is not even on the table for v1.

**Tradeoff accepted:** Some genuinely-translatable cases (e.g., Click → Typer in Python) get downgraded to spec-driven instead of code-lift. Acceptable in v1; v1.x can introduce per-pair adapters incrementally without changing the schema.

### KTD-5 — Versioning prompts the user, no auto-bump

**Decision:** Resolves OQ-1. Re-capturing an existing slug always prompts `[y/N]` before bumping. No `--auto-bump` flag in v1.

**Why:** Bundle schema is calibrating in v1. False bumps from auto-mode are recovered with a delete-and-rename, which is friction. Prompted bumps cost a beat and recover with a single keystroke.

**Tradeoff accepted:** Slightly more interactive than ideal for power users. Tunable post-ship; `--auto-bump` is a v1.x candidate.

### KTD-6 — Hardcoded shelf path, no `--shelf-path` override

**Decision:** Resolves OQ-6. `~/.vibe-taker/library/` is hardcoded; no override in v1.

**Why:** Cross-machine sync is v2. Locking the path in v1 means the v2 sync work moves the whole `~/.vibe-taker/` directory wholesale; no per-config rewriting, no migration script.

**Tradeoff accepted:** Users with non-standard home setups can't relocate the shelf. Edge case; can introduce in v1.x without breaking compatibility.

### KTD-7 — `:plant --yes` deferred to v2

**Decision:** Resolves OQ-4 deferral. v1 always shows the diff and prompts; no auto-confirm.

**Why:** The diff format itself is being validated in v1. Auto-confirm before validating the format would let bad diffs land silently — inverse of the bug we're solving.

**Tradeoff accepted:** Power-user friction on repeated plants. Acceptable; v2 lights `--yes` once the diff format has shipped through a real-world cycle.

### KTD-8 — Self-Evolving Plugin Framework: placeholders only in v1

**Decision:** session-logger and friction-logger SKILLs ship as documented placeholders with reserved data paths. Command skills do not invoke them.

**Why:** Per scope and PRD — Self-Evolving Plugin Framework lighting up is a v2 concern; v1 ships the round-trip and validates the bundle schema. Reserving paths and folder names in v1 saves a v2 directory restructure.

**Tradeoff accepted:** No durable session memory in v1. Process-notes.md and decision-log MCP fill the gap for this Cart cycle.

## Open Issues

Carry-over from PRD; resolved at the indicated stage.

| OQ | Description | Resolution stage | v1 status |
|---|---|---|---|
| OQ-1 | Versioning prompt vs auto-bump | /spec (resolved) | Locked: prompt user, no `--auto-bump` flag. KTD-5. |
| OQ-2 | Dedup similarity threshold | post-ship | Default 70% Jaccard; tunable without schema change. |
| OQ-3 | Stack-match high/low/hard threshold | /spec (resolved) | Locked: framework-family table. KTD-4. |
| OQ-4 | `:plant --yes` flag | v2 | Deferred. KTD-7. |
| OQ-5 | Interview-gate "3 substantive notes" threshold | post-ship | Default ≥30 chars + Levenshtein < 8 dedup; first friction signal at /reflect. |
| OQ-6 | Bundle storage path override | /spec (resolved) | Locked: hardcoded path, no override. KTD-6. |
| OQ-7 | Shell completion for `:plant <name>` | post-ship | Deferred. `:list` is the discovery surface in v1. |

**New issues surfaced in /spec writing (none rise to OQ status):**

- **Adapter coverage on code-lift mode.** v1 wires zero in-language framework adapters (Click→Typer, Express→Fastify). They're feasible and small; if a builder cycles through a clear case at `/reflect`, the first adapter is a v1.x candidate. Until then, those cases fall through to spec-driven, which is correct but wastes the high stack-match signal.
- **Prompt extraction false negatives.** The 100-char heuristic + LLM-SDK-call list will miss edge cases (string concatenation across multiple variables, prompts loaded from external files). Acceptable in v1; the interview gate fires when `prompts/` is empty AND deps include an LLM SDK, which is the safety net.
- **Single-language assumption inside captured bundles.** A target with both Python and Node sub-trees captures cleanly enough (autonomous read does both), but `contract.json.language` only holds one primary. Mostly fine; multi-language bundles route to spec-driven on plant regardless. Worth re-examining at second-feature capture.

## Cross-references

- Product surface and acceptance criteria: [`docs/prd.md`](./prd.md).
- Scope axes and explicit cuts: [`docs/scope.md`](./scope.md).
- Capture / plant flow narrative + bundle directory layout (substrate): [`docs/spec-substrate.md`](./spec-substrate.md).
- Builder profile (audience, deployment target, conventions): [`docs/builder-profile.md`](./builder-profile.md).
- Reference architecture — six existing marketplace plugins; closest stylistic neighbor [vibe-cartographer](https://github.com/estevanhernandez-stack-ed/vibe-cartographer); closest functional neighbor [vibe-iterate](https://github.com/estevanhernandez-stack-ed/vibe-iterate).
- Default architecture patterns (fallback, used selectively for the CLI Tool shape): [`vibe-cartographer/plugins/vibe-cartographer/architecture/default-patterns.md`](https://github.com/estevanhernandez-stack-ed/vibe-cartographer/blob/main/plugins/vibe-cartographer/architecture/default-patterns.md).
