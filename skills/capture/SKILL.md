---
name: vibe-taker-capture
description: Capture a feature out of the current repo as a portable bundle on the cross-repo shelf. Reads source, snapshots reference code, extracts architecture and contract, derives intent autonomously, fires the interview gate only when WHY can't be derived.
---

# vibe-taker — capture skill

> Implements [`spec.md > Capture Flow Architecture`](../../docs/spec.md#capture-flow-architecture) and [`prd.md > Epic: Capture`](../../docs/prd.md#epic-capture).

The harder half of vibe-taker. Read the target with no human input first; only ask the user when WHY can't be derived from source alone.

## Loading order — do this every time the skill fires

1. **Read** [`skills/guide/SKILL.md`](../guide/SKILL.md) for shared voice, hygiene, and references catalog. Persona and Tier-1 hygiene rules apply universally.
2. **Read** [`skills/guide/references/bundle-schema.md`](../guide/references/bundle-schema.md) — what artifacts you're producing and what shape they take.
3. **Read** [`skills/guide/references/secret-patterns.md`](../guide/references/secret-patterns.md) — what to skip and how to detect load-bearing secrets.
4. **Read** [`skills/guide/references/interview-gate.md`](../guide/references/interview-gate.md) — when to interview, what to ask.
5. **Read** [`skills/guide/references/error-contract.md`](../guide/references/error-contract.md) — class-0/1/2 outcome shapes.

Then execute the phases below in order.

## Argument parsing

The command form is `/vibe-taker:capture <path|file|glob>`. The argument is a single token (path, filename, or glob pattern). No flags in v1.

**Special case — in-file selector** (e.g., `file.py:120-180`, `module.ts#function`, anything with `:<number>` or `#<symbol>` after a path): **decline immediately**. Print verbatim:

```
[exit 1] vibe-taker captures whole files, folders, or globs in v1. Selection-within-a-file isn't supported — extract to its own file first or capture the parent file.
```

Exit class-1. **No bundle written.** PRD Capture story 4.

## Phase 1 — target resolution

| Input pattern | Resolution | Behavior |
|---|---|---|
| Single file (`scripts/foo.py`) | One file | `reference/foo.py`. `architecture.md` notes "single-file feature." |
| Folder (`apps/bg-remover/`) | Recursive read of folder | Preserve relative tree under `reference/<basename>/`. |
| Glob (`packages/auth/**`) | All matches under glob root | Preserve relative tree under `reference/` from glob root. Empty match → exit 1, "no files matched" error. |
| In-file selector | Decline | (Handled in argument parsing above.) |

**Verify before proceeding:** if the path doesn't exist (and isn't a glob), exit class-1:

```
[exit 1] Target `<path>` not found. Pass an existing path or a glob.
```

If the input looks like a glob (contains `*`, `?`, `[`, `**`) and matches zero files, exit class-1:

```
[exit 1] No files matched glob `<pattern>`. Check the pattern or `cd` to the right directory.
```

Resolve to a list of absolute file paths in scope. Carry the **glob root** (deepest directory that's a literal prefix of the glob) as `reference_root` — preserved tree under `reference/` is relative to this.

## Phase 2 — autonomous read pass

Walk every file in scope. **No interview yet.** This is the autonomous-extraction layer PRD Capture story 5 expects.

### 2.1 Language sniff

For each file:

- **By extension first:** `.py → python`, `.ts/.tsx → typescript`, `.js/.mjs/.cjs/.jsx → javascript`, `.rs → rust`, `.go → go`, `.cs → csharp`, `.rb → ruby`, `.sh/.bash → bash`.
- **Shebang fallback** for extensionless files.
- **Aggregate** to a primary language (most-frequent non-config extension across the captured tree). Carry the count distribution to inform `notes.md` if multi-language.

### 2.2 Manifest detect

Scan the captured tree for:

| Manifest | Implies |
|---|---|
| `package.json` | Node — read `dependencies`, `devDependencies`, `bin`, `[engines]`, `type`. |
| `pyproject.toml` | Python — read `[project].dependencies`, `[project.scripts]`, `[tool.poetry]`. |
| `requirements.txt` | Python — line-per-dep with optional version pins. |
| `Cargo.toml` | Rust — read `[dependencies]`, `[[bin]]`. |
| `*.csproj` | C# — XML `<PackageReference>`. |
| `Gemfile` | Ruby — `gem '<name>', '<version>'`. |
| `go.mod` | Go — `require` block. |

Extract `language`, `framework`, `dependencies` for `contract.json`. Framework is the highest-signal dep present:

- Python: `fastapi` / `flask` / `django` / `pandas` / `click` / `typer` / `argparse` (always available, treat as `cli-argparse` only when the entry-point uses it).
- Node: `express` / `fastify` / `next` / `react` / `vue` / `svelte` / `yargs` / `commander`.
- Rust: any crate name in the family table.
- Go: any in family table.

If multiple matches, prefer the framework most strongly bound to the entry-point file. If still ambiguous, pick the first hit and note the ambiguity in `notes.md`.

### 2.3 Entry-point identification

Heuristic by language:

- **Python:** files containing `if __name__ == "__main__"`, files registered as `[project.scripts]` in `pyproject.toml`, or single-file scripts with shebangs.
- **Node:** files referenced under `"bin"` in `package.json`, files with shebangs, or `index.{js,ts}` at the root, or files with a top-level `commander` / `yargs` invocation.
- **Rust:** `[[bin]]` entries in `Cargo.toml`, `src/main.rs`.
- **Go:** files with `package main` and a `func main()`.
- **Other:** shebanged files; files matching `main.*`, `cli.*`, `__main__.*`.

Record absolute paths within the captured tree. Will be relativized to `reference/` paths in `contract.json.entry_points`.

### 2.4 I/O surface extraction

By language and framework:

**Python:**

- `argparse.ArgumentParser` calls — extract `add_argument` declarations (name, type, required, help).
- `click` decorators (`@click.command`, `@click.option`, `@click.argument`).
- `typer` function signatures and `typer.Option` / `typer.Argument` annotations.
- `sys.argv` direct usage → input shape `[{"name":"argv","type":"other","description":"raw sys.argv passthrough"}]`.

**Node:**

- `yargs` chain (`.option`, `.command`, `.demandCommand`).
- `commander` chain (`.option`, `.argument`, `.command`).
- Direct `process.argv` indexing → similar `argv` passthrough input.

**Outputs:**

- Writes to `sys.stdout` / `console.log` (with shape detection — if it's JSON-shaped, mark as structured stdout).
- File-write calls with explicit paths: `open(path, "w")`, `Path(path).write_text`, `fs.writeFileSync`.
- Return values from named main functions when statically inferrable.

**Env vars:** regex-grep across all captured files (not just entry points) for:

- `os.environ\[["']([A-Z_][A-Z0-9_]*)["']\]`
- `os\.getenv\(["']([A-Z_][A-Z0-9_]*)["']`
- `process\.env\.([A-Z_][A-Z0-9_]*)`
- `Deno\.env\.get\(["']([A-Z_][A-Z0-9_]*)["']`
- `getenv\("([A-Z_][A-Z0-9_]*)"\)` (C-family)

Each unique env-var name → an entry in `contract.json.env_vars`. Default `load_bearing: true` when the env var is read **without** a default fallback in the same call (`os.getenv("X", "default")` → `load_bearing: false`); otherwise `true`.

### 2.5 Prompt extraction

For every file:

- Find string literals **>100 characters** passed as an argument to a known LLM SDK call. Recognized SDK call sites:
  - **OpenAI:** `openai.ChatCompletion.create`, `openai.chat.completions.create`, `client.chat.completions.create`, `client.responses.create`.
  - **Anthropic:** `anthropic.messages.create`, `client.messages.create`.
  - **Cohere:** `cohere.chat`, `co.chat`.
  - **Bedrock:** `bedrock.invoke_model`, `boto3.client("bedrock-runtime")...invoke_model`.
  - **Ollama:** HTTP POST to `/api/generate` or `/api/chat` with a `prompt`/`messages` body.
  - **Generic:** any function call with the literal argument name `prompt=`, `system=`, `messages=`, `instructions=`.
- Each matched string → `prompts/<descriptive-name>.txt`. Name the file from the variable name when the prompt is assigned (`SYSTEM_PROMPT = "..."` → `system_prompt.txt`); from the call site otherwise (`anthropic_system.txt`).

Save the prompts in-memory at this phase. Files write happens in Phase 7 (item 6).

### 2.6 Intent extraction

Read every:

- `README.md`, `README.rst`, `README.txt` in scope.
- `CHANGELOG.md`.
- Top-of-file docstring (Python: triple-quoted at top of file; JS/TS: leading `/** ... */`).
- Top-of-file comment block.

Build:

- `notes.md > Why this exists` — synthesize from intent material. Lead with a 1-2 sentence "what this is for, beyond what the code does" line, then bullets for non-obvious context.
- `architecture.md > Summary` — 1-3 sentences derived from the intersection of source README + entry-point docstrings.
- `summary` (one-liner for `index.json` and `README.md` of the bundle) — distill the architecture summary.

If **no intent material exists** (no README, no docstrings, no top comments), set `architecture.md > Summary = null` for now — the interview gate will fire in Phase 5 (item 6).

### 2.7 Gotcha pattern-match

Walk `dependencies`. For each, check the known list:

| Dep matches | Gotcha bullet to add |
|---|---|
| `sharp` | "Uses `sharp` — native binding; check Apple Silicon support; first-install often pulls platform-specific binaries." |
| `pillow` / `PIL` | "Uses Pillow — may need libjpeg/zlib system libs at install on minimal base images." |
| `playwright` | "Uses Playwright — first-run downloads browser binaries (~300 MB)." |
| `tensorflow` / `torch` / `pytorch` | "Uses ML framework — GPU optional; CPU fallback can be slow on large inputs." |
| Contains `aws` | "Cloud SDK — check default region behavior; `AWS_REGION` env var typically required." |
| Contains `gcp` / `google-cloud-` | "Cloud SDK — service-account credentials typically required (`GOOGLE_APPLICATION_CREDENTIALS`)." |
| Contains `azure` | "Cloud SDK — check default Azure region/subscription resolution." |
| `selenium` | "Uses Selenium — needs a separate WebDriver binary on PATH." |
| `ffmpeg-python` / `imageio-ffmpeg` | "Wraps `ffmpeg` — system binary required (not pulled by pip)." |

Add matched bullets to `notes.md > Gotchas`. Multiple matches → multiple bullets. No matches → `Gotchas` may end up empty (interview gate will fire on `< 3 substantive items` in Phase 5).

## Phase 3 — secret-file skip

Apply the patterns from [`secret-patterns.md`](../guide/references/secret-patterns.md). For every file in scope:

1. **Match basename and repo-relative path** against the glob list (case-insensitive on Windows).
2. **Apply carve-outs** — `.env.example`, `.env.sample`, `.env.template`, `.env.local.example`, the secret-patterns reference itself, documented loader files.
3. **If matched and not carved out: skip** the file from `reference/`. Add to a `skipped[]` list in memory.

For each skipped file, **before discarding**:

1. Compute basename minus extension; convert to UPPER_SNAKE.
2. Search the **non-skipped** captured files for:
   - `import` / `require` / `from … import` of the basename.
   - `dotenv.config()`, `load_dotenv()`, `dotenv.load()` calls.
   - `os.environ[…]` / `os.getenv(…)` / `process.env.<X>` references whose key matches a pattern derived from the basename or earlier-extracted env vars.
3. **If a match is found, mark the skipped file as load-bearing.** Add a stub to `contract.json.env_vars`:
   ```json
   { "name": "<INFERRED_NAME>", "load_bearing": true, "description": "Inferred from skipped <repo-relative-path>; provide at plant-time." }
   ```
4. **Print a warning** in the stdout summary (Phase 4) per PRD Capture story 8:

   > Skipped X secret-like files that look load-bearing. Capture continues with these stubbed in `contract.json` under `env_vars`. Provide them at plant-time.

The print itself happens in the summary; this phase only marks state.

## Phase 4 — stdout summary (no bundle written yet in this phase)

> **Item 5 boundary:** the work above produces in-memory analysis. The next phases (interview gate, bundle generation, atomic write, versioning) live in **item 6**. For dry-run / debugging — and for the item-5 verify step — print the analysis to stdout and stop.

Print one block to stdout:

```
=== vibe-taker:capture analysis (dry run) ===

target:        <input arg as given>
reference_root: <resolved abs path>
files in scope: <count>
language:      <python|typescript|...>
framework:     <fastapi|express|cli-argparse|null>
interface_kind: <cli|library|...>
entry_points:  <comma-separated relative paths>
inputs:        <count>
outputs:       <count>
env_vars:      <count>
prompts:       <count>  (skipped to file in Phase 7)
gotchas:       <count>
slug-proposed: <slug>
summary:       "<one-line summary or null>"

skipped (secret-like):  <comma-separated paths or "none">
load-bearing skipped:    <comma-separated names or "none">

next: Phase 5+ in item 6 — interview gate (when fired) → bundle generation → atomic write.
```

In the dry-run posture (item 5 work in isolation), exit class-0 here. The bundle does not land on the shelf in this phase. Item 6 connects the rest of the pipeline and the dry-run header is removed.

<!-- ITEM 5 BOUNDARY — phases below land in item 6. -->
