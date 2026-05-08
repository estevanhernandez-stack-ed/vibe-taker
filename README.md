# vibe-taker — solo repo

> **Take it with you.** Capture a feature out of one repo as a portable bundle; plant it into another and adapt to the destination stack.

This is the solo repo for the **vibe-taker** Claude Code plugin. The plugin source lives under [`plugins/vibe-taker/`](./plugins/vibe-taker/) — same shape as the other plugins on the [vibe-plugins marketplace](https://github.com/estevanhernandez-stack-ed/vibe-plugins).

## Install

Stable channel (recommended):

```
/plugin install vibe-taker@vibe-plugins
```

Canary channel (this repo's `main`, bleeding-edge):

```
/plugin install vibe-taker@estevanhernandez-stack-ed/vibe-taker
```

## What's where

| Path | What it is |
|---|---|
| [`plugins/vibe-taker/`](./plugins/vibe-taker/) | The plugin itself — `plugin.json`, `commands/`, `skills/`, `LICENSE`, plugin storefront `README.md`. |
| [`docs/`](./docs/) | Planning artifacts: scope, PRD, spec, checklist, builder profile. The full technical spec is at [`docs/spec.md`](./docs/spec.md). |
| [`process-notes.md`](./process-notes.md) | Process journal across this Cart cycle. |

## How it works

Three slash commands invoke three skills, plus a shared `guide` skill that carries the voice/persona/hygiene baseline:

- **`/vibe-taker:capture <path>`** — Lift the target feature into a portable bundle at `~/.vibe-taker/library/<feature>/`. Reads source, snapshots reference code, extracts architecture and contract, derives intent autonomously.
- **`/vibe-taker:plant <name>`** — Drop the named bundle into the current repo. Detects target stack, picks code-lift or spec-driven, declines on hard mismatch. Always shows the diff before any write.
- **`/vibe-taker:list`** — Surface what's on the shelf. Supports `--search` and `--sort name|lang`.

## Channels

- **Canary:** `estevanhernandez-stack-ed/vibe-taker:main` — bleeding-edge `main`.
- **Stable:** `vibe-plugins/.claude-plugin/marketplace.json` pinned to a tag.
- Tag scheme: plain `vX.Y.Z` (matches Cart, Doc, Thesis Engine).

## License

MIT — see [`plugins/vibe-taker/LICENSE`](./plugins/vibe-taker/LICENSE).
