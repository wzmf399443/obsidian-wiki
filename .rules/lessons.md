# Lessons Log

Hard-won corrections from real sessions. Append-only during a session; distilled
per `.rules/maintenance.md` when >100 lines. Format: see maintenance.md.

## 2026-07-03 — CLAUDE.md and GEMINI.md are symlinks

- Situation: rewriting the repo's agent context files (this institution's setup).
- Mistake/surprise: tried to write `CLAUDE.md` directly; the harness refused —
  `CLAUDE.md` and `GEMINI.md` are symlinks to `AGENTS.md`.
- Rule: edit `AGENTS.md` only; never replace the symlinks with real files.
- Applies to: AGENTS.md header note (already added).

## 2026-07-03 — Agent tool has no effort parameter

- Situation: writing the model dispatch protocol; verified against actual tool
  schemas instead of memory.
- Mistake/surprise: easy to assume subagents take a reasoning-effort option —
  they don't; `effort` exists only inside Workflow scripts' `agent()` calls.
- Rule: for the Agent tool, choose tier via `model` (haiku/sonnet/opus) only;
  omit `model` to inherit the session model.
- Applies to: delegation.md §2 (already encoded).

## 2026-07-03 — Injected CLAUDE.md context can be stale vs disk

- Situation: a review subagent noticed the CLAUDE.md content auto-injected into
  its system context matched an old backup, not the freshly rewritten file.
- Mistake/surprise: the harness caches agent-context files; right after an edit,
  a subagent (or a concurrently started session) may operate on the previous
  version of the rules.
- Rule: after editing AGENTS.md, tell subagents in the prompt to READ the file
  from disk rather than trust their injected copy; expect one stale session.
- Applies to: delegation.md §3 (prompt contents), maintenance.md.
