# Judgment Rubrics — decisions weaker models get wrong

Externalized judgment calls, each with a concrete pass/fail example. When a
situation matches a rubric, follow it even if your instinct says otherwise —
these encode failure patterns that feel fine from the inside.

## R1 — When to escalate to a stronger model

Escalate (per `.rules/delegation.md` §5) when the task is **judgment-shaped**,
not effort-shaped: ambiguous criteria, competing goods, taste, or "is this
actually the same thing?" questions.

- ✅ **Escalate:** deciding whether `concepts/rag.md` and `concepts/retrieval-
  augmented-generation.md` should merge — requires reading both and judging
  identity vs overlap. Wrong merges destroy information.
- ❌ **Don't escalate:** applying an approved merge recipe to 12 more confirmed
  duplicate pairs — that's mechanical; use a Small/Middle agent. Escalating
  everything is how the budget dies and the user turns the system off.

## R2 — When a task is actually DONE

"Done" is a checklist, not a feeling. For any wiki write operation, done means
ALL of: (1) target pages written with complete frontmatter (`title`, `category`,
`tags`, `sources`, `created`, `updated`); (2) bookkeeping updated — `index.md`,
`log.md`, `hot.md`, plus `.manifest.json` for ingests; (3) new `[[wikilinks]]`
point at pages that exist; (4) for >3 pages or any merge/delete: fresh-context
read-back passed (`impl-validator`).

- ✅ **Done:** ingested 4 docs → 6 pages written, manifest has 4 new source
  entries, index gained 6 rows, log + hot.md updated, validator returned pass.
- ❌ **Not done:** "I wrote the 6 pages" with bookkeeping "to follow" — that's
  the silent-drift leak (`.rules/diagnosis.md` #3). If you ran out of room to
  finish bookkeeping, the task is NOT done; say so explicitly and finish it.

Same principle for code: done = executed/tested, not compiled-in-your-head.

## R3 — When to stop and ask the user

Ask BEFORE acting when the action is destructive or the intent is genuinely
underdetermined. Never ask permission for reversible actions that follow
directly from the request.

Always-ask list: merging or deleting wiki pages (`wiki-dedup` act phase),
`wiki-rebuild`, overwriting `_meta/taxonomy.md` wholesale, `git push`, any
operation on vault dirs that look personal rather than framework-managed
(`<private-dir>/`, `<private-dir>/`, `attached/`), and **any export/publish/share of vault
content** — including `wiki-export` and "public only" filtered queries. This
vault's pages are mostly untagged, and untagged means `visibility/public` to the
filter, so filtered mode does NOT make output safe: it would ship company (<company>)
content as public. Treat the whole vault as sensitive until the user says otherwise.

- ✅ **Ask:** "dedup my wiki" found 14 candidate pairs → present the list with
  per-pair confidence and your lean, get approval, THEN merge. (Propose-approve-
  apply: for big ambiguous asks, doing 3 examples and asking "this pattern ×40?"
  costs one round-trip and prevents 40 wrong writes.)
- ❌ **Don't ask:** "add this article to the wiki" → just pick the category and
  tags yourself; that's the skill's job. Asking "which category?" for every
  routine call trains the user to ignore your questions.

If the user is unavailable and the action is on the always-ask list: do the
non-destructive part (report, staged copies in `output/`), leave the destructive
part queued with a clear note. Never default to "proceed" on destructive ops.

## R4 — Wrong-direction signals (change strategy, don't retry)

Retrying is only right when the failure was random. These signals mean the
APPROACH is wrong, and retry #3 will fail like #1 and #2:

- Same error class twice despite different attempts.
- Each "fix" requires touching something progressively less related to the task.
- Your workaround disables or weakens a safety/verification step (a hack that
  deletes the check instead of passing it).
- Output keeps growing but acceptance criteria are no closer ("busy but not
  converging").
- You're about to blame the environment/tool without having reproduced the
  claim in isolation.

Response: stop, write down the trail (attempts, outputs, expectation), then
either switch strategy or escalate with the trail (`delegation.md` §5).

- ✅ **Correct:** grep-based link check misses links inside code blocks twice →
  stop patching the regex; switch to parsing per-line with code-fence state.
- ❌ **Wrong:** third retry of the same regex with one more special case, then a
  fourth. Two rounds per approach is the hard cap.

## R5 — Quality floor for wiki content (how to check without taste)

A weaker model can't always judge "is this page good?" but can check proxies
that correlate with good:

1. **Compression test:** page ≤ ~1/3 the length of its source material. A page
   that restates the source failed to distill.
2. **Standalone test:** the first paragraph makes sense to someone who hasn't
   seen the source conversation/document.
3. **Connection test:** ≥2 outgoing `[[wikilinks]]` to EXISTING pages, and the
   linked pages are genuinely related (spot-check one).
4. **Update-over-append test:** if a page on this topic already existed, the diff
   shows integrated edits, not a new section bolted onto the end.
5. **Frontmatter + tags:** all 6 fields; tags from `_meta/taxonomy.md`, max 5
   (visibility/ tags exempt).

Spot-check protocol for batch writes: verify 3 random pages fully rather than
all pages shallowly. If any of the 3 fails, assume the batch is bad — fix the
generator and re-verify, don't hand-patch the one page you looked at.

## R6 — Honest limits (what to do when the rubrics run out)

Some calls need judgment this file can't encode: whether a synthesis insight is
real or trite, whether the user would find a page's tone right, whether two
subtly different concepts deserve one page. The ladder:

1. Escalate to a Big-tier agent with the specific question (not the whole task).
2. Still uncertain → generate 2–3 independent answers, have a separate judge
   agent compare; if they agree, proceed; if they split, that's information.
3. Still split → present the options to the user with your lean and the
   disagreement. **"This needs your call" is a valid, professional output.**

What is NOT acceptable: silently picking one option and reporting it with
confidence, or hedging so much the user can't tell a decision was needed.
When you learn something from the outcome, append it to `.rules/lessons.md`
(format in `.rules/maintenance.md`).
