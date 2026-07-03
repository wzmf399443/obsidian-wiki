# Subagent Prompt Templates

Copy the matching template, fill every `{…}` slot, delete inapplicable lines.
Each template already contains the dispatch trio (goal+motivation, acceptance
criteria, report format) required by `.rules/delegation.md` §3. The recommended
tier/agent-type is a default — override deliberately, not habitually.

Shared rules to keep in every prompt:
- "Your final message is the ONLY thing returned to me — put the full report there."
- "Report ≤50 lines. Anything longer goes to a file; return its path."
- "Separate what you OBSERVED from what you INFER."
- "If you cannot finish, report exactly what's done and what remains — do not pad."

---

## T1 — SEARCH / LOCATE  (agent type: `Explore`, tier: inherit)

```
GOAL: Find {what — e.g. every vault page mentioning "MCP server" in body or tags}.
WHY: {motivation — e.g. deciding whether an MCP concept page already exists
     before creating one}.
SCOPE: {dirs/globs — e.g. $VAULT/concepts/ and $VAULT/entities/, *.md only}.
       Vault path: {absolute path from .env}.
ACCEPTANCE:
- Search body text AND frontmatter, not just filenames.
- Say which directories you covered, so absence of results is meaningful.
REPORT (≤50 lines): one line per hit — path:line, 1-sentence context, and
{the decision-relevant attribute, e.g. "whether the page is a stub"}.
Explicitly state "no matches in {scope}" if none. Never paste page bodies.
```

## T2 — IMPLEMENT / WRITE PAGES  (agent type: `general-purpose`, tier: Middle)

```
GOAL: {create/update N wiki pages from source X | make code change Y}.
WHY: {e.g. part of ingesting <source>; these pages serve future wiki-query calls}.
INPUTS: {source paths; existing pages to UPDATE rather than duplicate — list
        them explicitly; relevant conventions: wikilinks, taxonomy at
        $VAULT/_meta/taxonomy.md, max 5 tags}.
CONSTRAINTS: update existing pages in place — never append duplicate sections;
frontmatter must have all 6 fields (title, category, tags, sources, created,
updated); [[wikilinks]] must target pages that exist (check before linking).
Do NOT update index.md/log.md/hot.md/.manifest.json — the coordinator does that
once, after all writers finish {delete this line if agent should do bookkeeping}.
ACCEPTANCE: quality floor R5 in .rules/judgment.md — compression ≤1/3 of source,
standalone first paragraph, ≥2 outgoing links to existing pages.
REPORT (≤50 lines): per page — path, created|updated, 1-line summary, outgoing
links added. List anything you skipped and why.
```

## T3 — REFACTOR / MERGE / NORMALIZE  (agent type: `general-purpose`, tier: Middle; the merge DECISION is Big or user — see judgment.md R1/R3)

```
GOAL: Apply this already-approved recipe: {exact recipe, e.g. "merge page B into
page A: union of body sections, union of tags capped at 5, earliest created,
today's updated, redirect stub at B's path, rewrite inbound [[B]] links to [[A]]"}.
TARGETS: {explicit list of pages/pairs — never "find more candidates yourself"}.
WHY: {e.g. dedup run approved by user on 2026-07-03; decisions already made —
your job is faithful execution, not re-deciding}.
CONSTRAINTS: touch ONLY listed targets. If a target doesn't match the recipe's
assumptions (e.g. page B has a section type the recipe doesn't cover), SKIP it
and flag it — do not improvise.
ACCEPTANCE: after your edits, no [[wikilink]] in the vault points at a deleted/
renamed path; every touched page still has complete frontmatter.
REPORT (≤50 lines): per target — done|skipped(reason); count of link rewrites;
files touched. A fresh verifier will re-check your work — leave nothing implied.
```

## T4 — RESEARCH  (agent type: `general-purpose`, tier: Middle; use `claude-code-guide` for Claude Code/API questions)

```
GOAL: Answer: {specific question(s) — not a topic, a question}.
WHY: {what decision this feeds}.
SOURCES: {web | specific URLs | vault | agent history dirs}. Prefer primary
sources (official docs, changelogs) over blogs/SEO summaries.
ACCEPTANCE:
- Every claim carries its source (URL or file:line).
- Distinguish: confirmed (≥1 primary source) / reported (secondary only) /
  not found. "Not found" is an acceptable answer; a guess is not.
- Note publication dates — flag anything older than {threshold}.
REPORT (≤50 lines): answer first, then per-claim sources, then open questions.
Full notes to {output/ or scratchpad path} if extensive; return the path.
```

## T5 — REVIEW / VERIFY  (agent type: `general-purpose`; tier: Middle for read-back, Big for high-risk judgment. NEVER the agent that produced the work)

```
GOAL: Verify this work against its acceptance criteria. You had no part in
producing it; your job is to find problems, not to confirm success.
THE WORK: {files written / diff / report at path X}.
ORIGINAL ACCEPTANCE CRITERIA: {paste them verbatim from the producing prompt}.
CHECK:
- Read the actual files (not the producer's report) — read-back, don't trust.
- {task-specific: e.g. "resolve 10 random [[wikilinks]] added; do targets exist?"}
- {e.g. "confirm index.md/log.md/hot.md/.manifest.json reflect these writes"}
- Spot-check depth over breadth: 3 items fully beats all items shallowly.
REPORT: verdict pass|warn|fail on the FIRST line. Then per-criterion: met|not
met + evidence (file:line). For fail/warn: the minimal concrete fix. Do NOT fix
anything yourself — report only.
```

---

**Escalation retry note:** when re-dispatching after a failure
(`delegation.md` §5), append a `FAILURE TRAIL:` section — attempt #, what was
tried, verbatim key output, expected-vs-got. An escalated agent without the
trail just repeats attempt #1 at a higher price.
