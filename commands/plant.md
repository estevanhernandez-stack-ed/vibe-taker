---
description: "Plant a captured feature from the shelf into the current repo. Adapts to the destination stack."
argument-hint: "<name> [--version=vX] — bundle name, optional version pin (default: latest)."
---

Use the **plant** skill to drop the named bundle into the current repo.
Detects target stack, picks code-lift (high match) or spec-driven (low match) or declines (hard mismatch).
Always shows the diff and asks for confirmation before any write.

**Prerequisites:** The named bundle must exist on the shelf. Run `/vibe-taker:list` to see what's available.
