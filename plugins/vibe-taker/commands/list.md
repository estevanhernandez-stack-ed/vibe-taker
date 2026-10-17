---
description: "List bundles on the cross-repo shelf with one-line summaries. Supports search and sort."
argument-hint: "[--search <query>] [--sort name|lang]"
---

**Load the full instructions first:** read `${CLAUDE_PLUGIN_ROOT}/skills/list/SKILL.md` in full and follow it. This file is only the entry point; the skill is the complete instruction set, and this command shadows it, so it will not load on its own.

Use the **list** skill to surface what's on the shelf at `~/.vibe-taker/library/`.
Default sort is most-recently-captured first. Search is substring across name, summary, tags, source-repo, language.
Flags near-duplicates (≥70% summary similarity) so the shelf doesn't sprawl.

**No prerequisites.** If the library is empty, prints a message and exits.
