---
description: "List bundles on the cross-repo shelf with one-line summaries. Supports search and sort."
argument-hint: "[--search <query>] [--sort name|lang]"
---

Use the **list** skill to surface what's on the shelf at `~/.vibe-taker/library/`.
Default sort is most-recently-captured first. Search is substring across name, summary, tags, source-repo, language.
Flags near-duplicates (≥70% summary similarity) so the shelf doesn't sprawl.

**No prerequisites.** If the library is empty, prints a message and exits.
