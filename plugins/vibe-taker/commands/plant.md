---
description: "Plant a captured feature from the shelf into the current repo. Adapts to the destination stack."
argument-hint: "<name> [--version=vX] — bundle name, optional version pin (default: latest)."
---

**Load the full instructions first:** read `${CLAUDE_PLUGIN_ROOT}/skills/plant/SKILL.md` in full and follow it. This file is only the entry point; the skill is the complete instruction set, and this command shadows it, so it will not load on its own.

Use the **plant** skill to drop the named bundle into the current repo.
Detects target stack, picks code-lift (high match) or spec-driven (low match) or declines (hard mismatch).
Always shows the diff and asks for confirmation before any write.

**Prerequisites:** The named bundle must exist on the shelf. Run `/vibe-taker:list` to see what's available.
