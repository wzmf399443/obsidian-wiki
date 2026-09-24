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
        {owned pages (by `sources:` basename) vs mention-only pages — not
        yours: suggest changes under CROSS-BATCH}.
CONSTRAINTS: update existing pages in place — never append duplicate sections;
frontmatter must have all 6 fields (title, category, tags, sources, created,
updated); [[wikilinks]] must target pages that exist (check before linking).
Do NOT update index.md/log.md/hot.md/.manifest.json — the coordinator does that
once, after all writers finish {delete this line if agent should do bookkeeping}.
- Scope: never read/grep/glob <private-dir>/ or <private-dir>/, no `*`/`**` glob at the vault
  root; search only scope.txt files with /usr/bin/grep (bare grep is a wrapper).
- Target `updated` is today + related content already there = a parallel batch
  wrote it: add only your own delta; on a stale-edit error, re-read and merge.
- Provenance: only `^[inferred]`/`^[ambiguous]` — never `^[extracted]` in any
  form; colon and plain forms count equally. Sources giving one field/condition
  different meanings (front/back end, plan/implementation, ticket/acceptance) →
  both sides + `^[ambiguous]` naming each; never harmonise into one rule — you
  have no adjudication right.
- Correcting/overturning claim X: grep the page for X's keywords and handle every
  hit (rewrite or keep). A one-line caveat that overturns or qualifies a claim is
  never DEFERRED and doesn't count toward the 1/3 compression cap.
- Confidence (owner ruling 2026-07-29): one epic tree = one lineage, single-tree
  cap 0.59, no credit for breadth; an existing page's base_confidence changes
  only when a new source corroborates the same claim — otherwise it goes through
  the trust ledger (review → approve → trust-record), never auto-changed by
  ingest or lint.
- Frontmatter: edit line by line (list key: insert after its last `  - ` line);
  no DOTALL/greedy regex, no whole-block rebuild; key list after = before; any
  script asserts the body byte-identical (split on "\n---", never a `\s*\n`
  anchor); quote values containing ": " or "#" or starting with [ { & *. Before
  finishing, assert by script: summary ≤200 chars (Python len()) and every page
  you wrote passes yaml.safe_load.
- Timestamps from a real `date -u +%Y-%m-%dT%H:%M:%SZ` run (or the manifest's
  ingested_at value), never estimated. Never write credentials, tokens, IPs,
  phone numbers, BID/PID, production order IDs or Slack/CloudWatch links —
  afterwards grep your pages for the concrete strings from the source.
ACCEPTANCE: quality floor R5 in .rules/judgment.md — compression ≤1/3 of source,
standalone first paragraph, ≥2 outgoing links to existing pages.
REPORT (≤50 lines): per page — path, created|updated, 1-line summary, outgoing
links added. List anything you skipped and why. Quote every original sentence
you changed. Sections: CROSS-BATCH (edits for pages you don't own, each with its
source + snapshot date) · DEFERRED · COORDINATOR TEXT CORRECTED (prompt wording
the source contradicted).
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
and flag it — do not improvise. If ANY target of a finding mismatches, re-evaluate
all targets of that finding before touching any, and explain it in the report.
- Fill-a-gap / add-pending fixes: re-read the counterpart page's current text
  first; if it has a definite value, cite that value instead of marking pending.
- Correcting claim X: grep the page for X's keywords and handle every hit.
- Frontmatter edits follow T2's frontmatter rule (line by line; key list and body
  unchanged vs before).
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
- Re-derive key claims from the SOURCE, not from the page's internal consistency.
- Claimed timestamps (log/hot entries, `updated`) ≤ the file's mtime.
- Corrected claims: grep in-page and cross-page for the old wording; cross-page
  fixes: read both sides' current text; status words: `grep -n <ticket>` the
  whole file. After an interrupted/resumed run: no duplicate sections.
- Promoted `_raw/` drafts with file:line citations: check ≥3 citations against
  the source repo + every core claim (minimal fix: line numbers + bump
  `updated`; claim/provenance untouched).
- Identifier scan: credentials, tokens, IPs, phone numbers, BID/PID, production
  order IDs, Slack/CloudWatch links. Scope: never read/grep/glob <private-dir>/ or
  <private-dir>/; no `*`/`**` glob at the vault root.
- Carry/blind-spot items: quote the value with ±2 lines of context (an as-of note
  there = healthy); an item carried ≥2 rounds that nobody has read in full is
  downgraded to 「待實讀確認」 in the 3rd round, not carried again.
- Sharded detection (e.g. lint check-5): a finding outside or across your shard —
  claim it yourself and mark CROSS-CLUSTER; never hand it over or skip it. Before
  calling a finding "new", compare it by ID with the previous run's open items
  {attach them}; a same-batch `updated` proves a rewrite, not newness.
- Batch page edits (ingest, lint-fix, consolidate): each touched page's frontmatter
  key set vs the pre-run backup (sources/updated/provenance exempt), relationships
  targets never shrink, body byte-identical for frontmatter-only edits; a batch run
  with no pre-run page backup fails this check (09-04, 09-18).
- New pages: each has ≥1 incoming content link (index.md doesn't count).
REPORT: verdict pass|warn|fail on the FIRST line. Then per-criterion: met|not
met + evidence (file:line). For fail/warn: the minimal concrete fix. Do NOT fix
anything yourself — report only.
```

T5 coordinator notes: after sharded detection, confirm every CROSS-CLUSTER or
"handed over" item actually landed; old-debt (carry) reconciliation finishes
before any "new" count is reported; a prompt that says "the vault was just
changed" attaches the previous run's open-item list.

## T6 — MULTI-BATCH INGEST COORDINATION (coordinator checklist; producers get T2, verifiers T5)
Moved to `.rules/templates-ingest-coordination.md` (2026-09-24): the coordinator run sheet for every coordinator-run ingest; lint-fix/consolidate per its Scope line.

---

**Escalation retry note:** when re-dispatching after a failure
(`delegation.md` §5), append a `FAILURE TRAIL:` section — attempt #, what was
tried, verbatim key output, expected-vs-got. An escalated agent without the
trail just repeats attempt #1 at a higher price.
