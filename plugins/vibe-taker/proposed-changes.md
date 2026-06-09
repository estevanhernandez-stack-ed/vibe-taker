# Proposed changes — vibe-taker

> Dev-input notes for the next vibe-taker evolve cycle. Hand-seeded between runs.
> **Nothing here is applied automatically.** Each entry is a signal to weigh, not a committed change.

## 2026-05-23 — evolve signal: bring-your-own decision-log MCP

Keep decision-log MCP guidance MCP-agnostic — reference "your decision-log MCP if present (626Labs dashboard auto-detected as `mcp__626labs-cloud__*`)" rather than hardcoding ours. If vibe-taker ever gains a pluggable decision-log surface, support bring-your-own-MCP. Surfaced by the 2026-05-23 sweep.

status: **applied 2026-06-09** — decision-log references genericized in `skills/guide/SKILL.md` and `skills/plant/SKILL.md` per the [family decision-log convention](https://github.com/estevanhernandez-stack-ed/vibe-plugins/blob/main/docs/conventions/decision-log-backend.md) (STANDARD v1): the 626Labs dashboard is now framed as one auto-detected backend (bring-your-own), and the `manage_projects` repo-bind is called out as a separate bridge concern outside the log contract. This pass was language-level; a fully pluggable file/jsonl/disabled backend (the convention's structural layer) remains future evolve work.
