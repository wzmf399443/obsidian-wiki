# Ingest coordination — T6 coordinator run sheet
For the coordinator of every coordinator-run ingest (single-batch too); lint-fix/consolidate runs use the parts its Scope line names. Moved verbatim from `templates.md` on 2026-09-24 — producer (T2) and verifier (T5) templates stay there.

## T6 — MULTI-BATCH INGEST COORDINATION (coordinator checklist; producers get T2, verifiers T5)

Scope: every coordinator-run ingest, single-batch too. Lint-fix/consolidate runs
also use PRE-DISPATCH's backup, the "Frontmatter vs backup" and "Propagation"
checks, the status-edit rule and the first (self-binding) line (09-04
"ingest/lint-fix", 08-14 "any status sync", 09-17 "any coordinator write").

```
You obey every page rule you give producers (T2) — no "just one field" exemption —
and re-run scripts/verify_mechanical.py after EACH page write of your own.
PRE-DISPATCH
- rsync the content dirs to ~/.claude/backups/<date>-ingest/ (the only rollback
  basis); every backup/cmp path in SHARED_RULES points at THIS run's backup.
- Copied scaffold: grep -rn '<prev date>\|[0-9]\+ sources\|[0-9]\+ modified' scripts/
  → fix every hit; log/hot prose lives in data files, code only anchors + appends.
- scope.txt via find -prune (operations.md §Mixed-vault scope), rebuilt after
  producers create pages; copy the sources to sources_snapshot/.
- Ownership by `sources:` basename (operations.md mapping); tickets sharing a page
  → one batch; batches pairwise-disjoint; ≤4 agents at once.
- Re-ingest: check each "new content" claim (requester brief, CROSS-BATCH) against
  output/ingest-<prev>/reports/*.md and tell the requester of mismatches; prompts
  say "not first-time content — diff first, then merge".
- Every prompt: report to reports/<BATCH>.md AND as the final message; CROSS-BATCH
  items cite source + snapshot date; facts you add cite their source.
GLOBAL CHECKS (after all batches, before bookkeeping; every 0 has a positive control)
- Touched set: cmp every content page vs the backup; reconcile with the reports.
- Status sweep: status words within ±80 chars of each ticket ID, not the whole line;
  hits are candidates only; hot.md/index.md/epic pages: grep -n "<ticket>" and read
  every hit; report false-negative risk next to the false positives.
- Propagation: grep the whole whitelist for every overturned/qualified claim (keywords
  with widened spacing + related tickets), incl. every DEFERRED / CROSS-BATCH item
  and lines you wrote yourself; decide every hit; hit list into log.md.
- Orphans: every new page ≥1 incoming content link (index.md doesn't count); fix via
  reciprocal links from the new page's own outgoing targets.
- Frontmatter vs backup: every key still present (sources/updated/provenance exempt),
  relationships targets never shrink; frontmatter-only edits leave the body
  byte-identical; each base_confidence change explained or reverted.
- CROSS-BATCH suggestions: re-verify status/date/quantity against scan.json / source
  frontmatter before applying; never reuse the suggester's wording.
VERIFICATION: fresh V1 (T5) re-derives from source and re-checks propagation and
new-page incoming ≥1; F1 fixer is neither producer nor verifier; fresh V2 checks F1's
own new wording. Index/hot text only after the verdict, never from a page's summary.
BOOKKEEPING (exactly once): manifest (every source; SKIPs with hash + skip_note)
→ index.md + log.md (APPEND only) → hot.md → manual_delta.py shows all unchanged.
Any status edit (hot, index, content pages): grep -n the ticket in the whole file
first and decide every hit.
INTERRUPTION (delegation.md §5): report file present = done; otherwise cmp owned pages
vs the backup yourself — never pass an mtime guess on as fact. Resume by SendMessage
with that verified state ("X written; Y still equals the backup" / "nothing written
yet") + "my read of the disk may be wrong: re-read each page before writing; never
re-merge". Model monthly cap → no resume: fresh agent at an available tier + the
disk-state list ("use the main model" follows the main model after it switches).
Orphan writes: attribute by ticket-ID grep ∩ batch ticket lists, never by timestamps.
Afterwards V1 also checks for duplicate sections.
```
