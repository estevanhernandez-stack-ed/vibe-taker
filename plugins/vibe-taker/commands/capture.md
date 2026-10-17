---
description: "Capture a feature out of the current repo as a portable bundle on the cross-repo shelf."
argument-hint: "<path|file|glob> — folder, single file, or glob. In-file selectors not supported in v1."
---

**Load the full instructions first:** read `${CLAUDE_PLUGIN_ROOT}/skills/capture/SKILL.md` in full and follow it. This file is only the entry point; the skill is the complete instruction set, and this command shadows it, so it will not load on its own.

Use the **capture** skill to lift the target feature into a portable bundle at `~/.vibe-taker/library/`.
Reads source, snapshots reference code, extracts architecture and contract, derives intent autonomously,
and only fires the interview gate when WHY can't be extracted from source alone.

**No prerequisites — `:capture` is the entry point of the round-trip.**
