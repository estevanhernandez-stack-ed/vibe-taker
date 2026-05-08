# vibe-taker

> **Take it with you.**

vibe-taker lifts a feature out of one repo as a portable bundle, and plants it into another — adapting to the destination stack.

A Claude Code plugin for builders who work across multiple repos. When you invent a CLI script, an agent prompt, or a wired-up integration in one repo and want it in another, the move today is copy-paste-then-adapt: source files duplicated by hand, the *intent* (architectural sketch, non-obvious tradeoffs, prompts) lost in translation, the destination Claude session re-deriving context that already existed three repos over.

vibe-taker fixes that. One command captures the feature into a portable bundle on a cross-repo shelf. Another command plants it into the destination, picking code-lift (high stack match) or spec-driven re-implementation (low match) automatically — and showing you the diff before any write.

## Install

```
/plugin install vibe-taker@vibe-plugins
```

## Three commands

### `:capture <path|file|glob>`

Lift the target feature into a portable bundle at `~/.vibe-taker/library/<feature-name>/`. Reads source, snapshots reference code, extracts architecture and contract, derives intent autonomously — interviews you only when WHY can't be extracted from source alone.

```
/vibe-taker:capture apps/bg-remove/
```

### `:plant <name>`

Drop the named bundle into the current repo. Detects target stack, picks code-lift (high match) or spec-driven (low match) or declines (hard mismatch). Always shows the diff and asks for confirmation before any write.

```
/vibe-taker:plant bg-remover
```

### `:list`

Surface what's on the shelf. Default sort is most-recently-captured first. Supports `--search <query>` (case-insensitive across name, summary, tags, source-repo, language) and `--sort name|lang`. Flags near-duplicates so the shelf doesn't sprawl.

```
/vibe-taker:list --search image
```

## Bundle layout

Every bundle lands at `~/.vibe-taker/library/<feature-name>/<version>/` with six artifacts:

```
~/.vibe-taker/library/<feature>/v1/
├── README.md          # what it is, when to reach for it
├── architecture.md    # components, data flow, key files
├── contract.json      # I/O surface: inputs, outputs, deps, env
├── prompts/           # AI prompts if any
├── reference/         # verbatim snapshot of original source
└── notes.md           # WHY this exists, gotchas
```

The shelf is **local only** — `~/.vibe-taker/library/` on your machine. No network calls, no sync. Cross-machine sharing is a v2 concern.

## Docs

Full technical spec at [`docs/spec.md`](docs/spec.md). Product surface and acceptance criteria at [`docs/prd.md`](docs/prd.md). What was cut from v1 and why at [`docs/scope.md`](docs/scope.md).

## License

MIT.
