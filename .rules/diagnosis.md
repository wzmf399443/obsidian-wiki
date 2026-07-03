# Harness Diagnosis — Top 3 Failure Modes (and Fixes)

> Written 2026-07-03 by a one-time Fable 5 session, based on direct inspection of this
> repo (36 skills, ~9,500 lines), the vault (575 pages), and the session harness.
> Other files in `.rules/` implement the fixes; this file explains WHY they exist.
> If a fix here contradicts a rule elsewhere in `.rules/`, this file loses — rules
> files are the maintained source of truth.

## #1 — The main conversation does bulk reading itself (biggest token leak)

**What happens:** Skills like `wiki-lint`, `cross-linker`, `claude-history-ingest`,
and `wiki-dedup` instruct the agent to scan every vault page or read whole session
transcripts. Executed in the main conversation, one lint pass over 575 pages fills
the context window, triggers compaction, and the session loses its instructions
(CLAUDE.md content, the skill's own steps) exactly when it still has work left.
Late-session errors in long wiki operations are usually THIS, not model weakness.

**Detection signal:** you are about to Read/Grep more than 3 files, or you cannot
predict how many files a scan will touch before starting it.

**Fix (implemented in `delegation.md`):** the main conversation is a commander.
Bulk reading, scanning, history mining, web research, and batch page edits are
delegated to subagents that return conclusions only (≤50 lines + file paths).
Fan out per-directory or per-source. The main context holds decisions, not data.

## #2 — Environment facts are re-derived every session (slow-start leak)

**What happens:** Each session re-runs the config resolution walk, re-reads
`llm-wiki/SKILL.md` (526 lines) to learn conventions, re-checks whether QMD is
configured, re-discovers the vault layout. The persistent memory directory was
empty and the `$VAULT/AGENTS.md` hook was unused. Thousands of tokens per session
spent rediscovering facts that change at most a few times a year.

**Detection signal:** you are running `find`/`cat` to answer a question whose
answer is already pinned in CLAUDE.md's "Pinned Environment Facts" section.

**Fix (implemented in `CLAUDE.md`):** stable facts are pinned in CLAUDE.md with a
verification date. Trust them by default; re-verify only if an operation fails in
a way the pinned fact would explain (e.g. vault path 404s). When a pinned fact
proves stale, fix it in CLAUDE.md immediately (see `maintenance.md`).

## #3 — Writes have no acceptance contract (silent-drift leak)

**What happens:** Every write skill must update four bookkeeping files
(`.manifest.json`, `index.md`, `log.md`, `hot.md`). This is enforced only by
convention — nothing verifies it happened. A skipped index update doesn't fail
loudly; it makes every future `wiki-query` slightly wrong, and the drift
compounds until someone runs a rebuild. Likewise, agents report their own work
as "done" without any read-back, so a truncated write or an unresolved
`[[wikilink]]` ships silently.

**Detection signal:** you are about to say "done" and the only evidence is that
you remember issuing the Write calls.

**Fix (implemented in `judgment.md` §Done and `delegation.md` §Verify):**
"done" has a checklist definition (page + all four bookkeeping files + links
resolve). Any write operation touching >3 pages gets a fresh-context verification
agent (the `impl-validator` skill already exists for this — use it) that reads
the files back and returns pass/warn/fail. The producer never verifies itself.

## Honest limits — what these fixes do NOT solve

Decomposition, verification, and multi-sample judging raise *execution* quality
to near-Fable level for well-specified tasks. They do NOT compensate for:

- **Ambiguous asks** ("clean up my wiki" with no criteria) — don't guess at scale;
  ask the user 1–3 sharp questions first, or propose a small concrete sample
  ("here are 3 example fixes — apply this pattern to all 40?") and get approval.
- **Taste/judgment calls** (is this synthesis insightful or trite? should these
  two pages really merge?) — escalation ladder: try `opus`, then multi-sample
  judging (3 attempts + 1 judge), and if still uncertain, present options to the
  user with your lean. Saying "this needs your call" is a valid output.
- **Unknown unknowns** — a checklist can't catch a category of error nobody
  anticipated. When something feels off but no rule names it, write it down in
  `.rules/lessons.md` and surface it to the user rather than suppressing it.
