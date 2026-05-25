<p align="center">
  <img alt="Vibe Taker — capture a feature out of one repo, plant it in another, adapted to the destination stack" src="https://626labs.dev/assets/brand/plugins/vibe-taker-banner-1500x500.png" />
</p>

# Vibe Taker

**Take it with you — capture a feature out of one repo as a portable bundle, plant it into another, adapted to the destination stack.**

[![stable](https://img.shields.io/github/v/tag/estevanhernandez-stack-ed/vibe-taker?label=stable&color=17d4fa)](https://github.com/estevanhernandez-stack-ed/vibe-taker/tags)

## What it does

You invent something good in one repo — a CLI script, an agent prompt, a wired-up integration — and you want it in another. The move today is copy-paste-then-adapt: source files duplicated by hand, the *intent* (the architectural sketch, the non-obvious tradeoffs, the prompts) lost in translation, and the destination Claude session re-deriving context that already existed three repos over.

Vibe Taker fixes that with three slash commands and a cross-repo shelf:

- **`/vibe-taker:capture <path|file|glob>`** — Lift the target feature into a portable bundle. Reads source, snapshots the reference code, extracts architecture and contract, and derives the intent autonomously — interviewing you only when the WHY can't be pulled from source alone.
- **`/vibe-taker:plant <name>`** — Drop the named bundle into the current repo. Detects the destination stack and picks code-lift (high match), spec-driven re-implementation (low match), or declines (hard mismatch). Always shows you the diff and asks before any write.
- **`/vibe-taker:list`** — Surface what's on the shelf. Most-recently-captured first, with `--search <query>` (case-insensitive across name, summary, tags, source-repo, language) and `--sort name|lang`. Flags near-duplicates so the shelf doesn't sprawl.

## How it works

- **A bundle is portable intent, not just files.** Every capture lands at `~/.vibe-taker/library/<feature>/<version>/` with six artifacts — a `README.md` (what it is, when to reach for it), `architecture.md` (components, data flow, key files), `contract.json` (the I/O surface: inputs, outputs, deps, env), a `prompts/` folder for any AI prompts, a `reference/` verbatim snapshot of the original source, and `notes.md` for the WHY and the gotchas. The source travels with the reasoning, so the destination session isn't starting cold.
- **Planting is stack-aware.** On `plant`, Vibe Taker reads the destination repo's stack and adapts: a high match lifts the reference code with imports rewritten; a low match re-implements from the architecture + contract instead of forcing a paste; a hard mismatch declines rather than ship something broken.
- **The diff is mandatory.** No bundle ever writes silently. `plant` renders the full diff — mode, stack-match, bundle, target — and waits for your confirmation before touching a file.
- **The shelf is local only.** `~/.vibe-taker/library/` lives on your machine. No network calls, no sync. Cross-machine sharing is a v2 concern.

```text
/vibe-taker:capture apps/bg-remove/   # lift a feature onto the shelf
/vibe-taker:list --search image       # find what you stashed
/vibe-taker:plant bg-remover          # drop it into the current repo (diff first)
```

## Validated on

The bgremove + Sanduhr features. The bgremove round-trip captured a Python bg-removal CLI, planted it into a target repo, and passed a `--help` smoke test on the planted code; the Sanduhr-theming capture served as the schema-stability check — a documented-feature-with-no-CLI shape that the bundle schema absorbed without adding a field.

## Install

**Stable (recommended) — as a Claude Code plugin via the marketplace:**

```text
/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins
/plugin install vibe-taker@vibe-plugins
```

**Canary — track this repo's `main`:**

```text
/plugin install vibe-taker@estevanhernandez-stack-ed/vibe-taker
```

## Part of the Vibe ecosystem

Part of the **[Vibe Plugins](https://github.com/estevanhernandez-stack-ed/vibe-plugins)** marketplace from [626 Labs](https://626labs.dev) — foundations and process pillars for AI-assisted creation.

```text
/plugin marketplace add estevanhernandez-stack-ed/vibe-plugins
```

## License

MIT — *Imagine Something Else.*
