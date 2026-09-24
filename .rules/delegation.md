# Delegation & Model Dispatch Protocol

Rules for when the main conversation delegates work to subagents, which model
tier to use, and how results come back. Written for a Sonnet-class main agent.
Prompt templates that implement this protocol: `.rules/templates.md`.

## 1. The commander does not fight (when to delegate)

Delegate to a subagent when ANY of these is true:

- The task requires reading **more than 3 files** or **more than ~300 lines** total.
- You **cannot predict how many files** a scan will touch (vault scans, `_raw/`
  sweeps, history mining, grep-then-read chains).
- Web research beyond a single known page.
- Batch edits to **more than 3 wiki pages** (fan out; one agent per batch of ~5–10
  pages).
- Any `wiki-lint`, `cross-linker`, `wiki-dedup` (scan phase), `*-history-ingest`,
  or `wiki-synthesize` run — these always scan at unknown scale.

Do it yourself (no subagent) when: single known file, single page write, a quick
grep for one symbol, answering from context you already have, talking to the user.

**Why (see `.rules/diagnosis.md` #1):** every file read in the main conversation
permanently occupies context. When context fills, compaction erases your
instructions mid-task. Subagent context is disposable; yours is not.

Independent subagents go in ONE message so they run in parallel. Don't re-run a
search you already delegated — wait for the result.

## 2. Model tiers

The Agent tool takes an optional `model` parameter. In this harness the accepted
values are `haiku`, `sonnet`, `opus` (a session running fable also accepts
`fable`) — treat them as tier slots:

| Tier | `model` param (the ONLY valid values) | GLM backend maps it to | Use for |
|---|---|---|---|
| **Small** | `haiku` | *(model name not recorded — ask user)* | Mechanical work with a clear spec: apply an already-solved pattern across files, extract fields, reformat, count/list things |
| **Middle** | `sonnet` | *(ask user)* | DEFAULT worker: search, page writing, ingest distillation, implementation, first-pass review |
| **Big** | `opus` | `glm-5.2` | Judgment: merge/delete decisions, adversarial verification of high-risk work, escalation target, taste calls |

- **Always pass the slot keyword (`haiku`/`sonnet`/`opus`), never a backend model
  name like `glm-5.2`** — backend names will error; the proxy does the mapping.
- **Omitting `model` is correct by default** — the subagent inherits the session
  model. Specify a tier only when you deliberately want cheaper (Small, for
  mechanical batches) or stronger (Big, for judgment).
- If a model override errors anyway, omit the parameter and note it in
  `.rules/lessons.md`.
- The Agent tool has **no effort/reasoning parameter** — don't invent one. An
  `effort` option exists only inside Workflow scripts (`agent()` opts), and
  Workflow itself requires explicit user opt-in ("use a workflow") — default to
  the plain Agent tool. When unsure of a tool's real params, verify against the
  actual schema with `ToolSearch` — don't assume the Agent tool matches Workflow's
  `agent()`.

Agent types (the `subagent_type` parameter): `Explore` (read-only search —
cheapest way to locate things), `Plan` (read-only architect), `general-purpose` /
`claude` (can write files). Never send a write task to `Explore`/`Plan`.

## 3. The dispatch trio — every subagent prompt contains

1. **Goal + motivation** — what to produce AND why/for whom, so the agent can
   make sensible micro-decisions without asking back.
2. **Acceptance criteria** — objectively checkable conditions ("every page you
   touch still has all 6 frontmatter fields", "list every source file examined,
   not just matches").
3. **Report format** — exactly what to return (see §4), including "your final
   message is the ONLY thing I receive — put everything there".

A prompt missing any of the three gets you a confident agent doing the wrong
thing. Copy from `.rules/templates.md` rather than writing from scratch.

If AGENTS.md/CLAUDE.md was edited this session, tell subagents to READ the file
from disk — the harness caches agent-context files, so the injected copy can be
stale right after an edit (observed 2026-07-03).

**Second-hand facts (2026-09-16/17, 09-17, 09-21).** Anything you relay without having just
read its source — an upstream report's summary, a subagent's CROSS-BATCH suggestion, a
requester's "this part is new" — may be stale or wrong: cite its source (ticket + section,
snapshot date); re-verify status/date/quantity claims against the source, and "new content"
claims against the previous run's reports, before relaying or applying them; and tell the
agent "the source is authoritative — if it disagrees with this wording, follow the source
and report it under COORDINATOR TEXT CORRECTED".

## 4. Report contract (what comes back)

- **Conclusions only**, ≤50 lines: findings, decisions needed, `file:line`
  references. Never raw file contents, never full page bodies.
- **Long artifacts go to disk**, report carries the path: wiki pages into the
  vault; drafts/intermediate data into `output/` in this repo or the session
  scratchpad. Rule of thumb: anything >50 lines is a file, not a message.
- Reports must **separate observed facts from inference** ("index.md lists 570
  pages; 5 files on disk are missing from it" vs "the index looks stale").
- When the agent **edits existing pages**, the report must quote the original
  sentence(s) it changed — vault pages are git-untracked (operations.md), so
  the quote is the only rollback basis.
- If the agent could not finish, the report says exactly what remains — a partial
  honest report beats a padded complete-looking one.
- **Write-heavy tasks also save the report itself** to `reports/<BATCH>.md` AND return it
  as the final message — after an interruption it is the only proof of "done" vs
  "half-written" (2026-09-16/17). Name the file after the batch/task: on 2026-09-24 the
  harness refused a subagent's write to `REPORT.md` ("Subagents should return findings as
  text") while accepting `VERIFY.md` and `reports/B1.md`. If a write is refused, the agent
  does not route around it — it returns the text and the coordinator saves it.
- **Never hand a finding over**: a finding outside the agent's shard is claimed and marked
  `CROSS-CLUSTER` for the coordinator to dedup — parallel agents have no channel, so a
  handover is a silent drop (2026-08-27).

## 5. Escalation & de-escalation ladder

- **Small-tier agent gets it wrong once → escalate to Middle immediately.** Don't
  coach a Small model through corrections; retry-coaching costs more than the
  upgrade and fails anyway.
- **Middle-tier fails the same subtask twice → escalate to Big**, and hand the
  Big agent the full failure trail: what was attempted, verbatim key output, what
  was expected instead. Without the trail, the Big model repeats attempt #1.
- **Big model solves it → extract the pattern, de-escalate:** have Small/Middle
  apply the now-explicit recipe across the remaining batch. Don't keep paying Big
  prices for solved problems.
- **Hard cap: two retry rounds per approach.** After that, the approach is wrong,
  not the execution — change strategy or surface to the user with the trail
  (`.rules/judgment.md` §Wrong-direction has the signals).

**Interruptions are not failures (2026-07-24, 08-27, 09-04, 09-16/17).** A quota wall, stream
stall or user stop is not a failed attempt: resuming is not a retry round and moves no one on
this ladder (a resumed agent that then fails is handled by the ladder as usual). Its writes may
already be on disk (signal: target pages share one fresh `updated`, the manifest hash lags the
disk), so check yourself (report file present, `cmp` vs backup) — never pass an mtime guess on
as fact — and every resume or re-dispatch prompt carries that verified state + "may be partially
written — re-read before writing, never re-merge". Session/daily/spend-limit cap → wait for the
reset, then resume by SendMessage (keeps context); model monthly cap → don't resume (it hits the
wall again): fresh agent at an available tier with the predecessor's on-disk list. Cutting
concurrency: stop the latest-started / still-reading agents first. Two consecutive stalls with no
write progress → consider another model. Coordinator run sheet: templates-ingest-coordination.md (T6).

## 6. Verify, don't self-certify

The agent (or you) that produced work never signs off on it. Acceptance runs in
**fresh context** — a new subagent with no memory of the production process:

- **File writes** → read-back verification: a fresh agent reads the files and
  checks them against the acceptance criteria (the `impl-validator` skill is
  built for this — returns pass/warn/fail). Mandatory when >3 pages were written
  or anything was merged/deleted.
- **Code changes** → run the tests or actually execute the code path. "It looks
  right" is not verification.
- **High-risk judgment** (dedup merges, taxonomy changes, rebuild decisions) →
  second opinion from a Big-tier agent, or generate 2–3 independent answers and
  have a separate judge pick — disagreement between samples means escalate to
  the user.
- Verification failures go back to the PRODUCER role to fix (possibly a new
  agent), then re-verify. Verifier never fixes; fixer never verifies.
