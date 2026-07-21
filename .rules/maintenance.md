# Maintenance Protocol for `.rules/` and AGENTS.md

How future sessions (any model) keep these files alive without degrading them.
The failure mode to prevent: rules bloat until nobody reads them, or get
"simplified" until the protections are gone.

## What you may change WITHOUT asking the user

- **Append a lesson** to `.rules/lessons.md` (format below). This is the default
  destination for anything learned the hard way.
- **Fix objectively broken references**: a path that 404s, a tool/skill name that
  no longer exists, a pinned fact you have re-verified against reality (update
  the "verified YYYY-MM-DD" date when you do).
- **Add an example** to an existing rubric in `judgment.md` when a real case
  showed the rubric was ambiguous — add, don't replace.
- **Add a template variant** to `templates.md` for a recurring task type.

Backup rule for any edit beyond a pure append: copy the file to
`<name>.md.bak-YYYYMMDD` first (keep only the most recent backup per file;
delete older ones).

## What REQUIRES explicit user approval first

- Changing thresholds or ladders in `delegation.md` (the >3-files rule,
  escalation caps, tier assignments).
- Deleting or weakening any rule, especially verification steps. If a rule seems
  wrong, propose the change with the evidence — don't quietly bypass it. A rule
  that got skipped "because it slowed things down" is exactly the degradation
  this file exists to prevent.
- Rewriting `AGENTS.md` structure or the Session Protocol table.
- Anything in `judgment.md` R3's always-ask list.
- Editing `letter.md` (it's a historical document; append a dated postscript
  instead if something must be added).

## Lesson format (append to `.rules/lessons.md`)

```
## YYYY-MM-DD — {one-line title}
- Situation: {what was being done}
- Mistake/surprise: {what went wrong or what was unexpected — 1-2 lines}
- Rule: {the corrected behavior, imperative, checkable}
- Applies to: {which .rules file/section this should eventually fold into}
```

Write the lesson in the SAME session the mistake happened — next session won't
remember it. One lesson per entry; no essays.

## Compaction thresholds

- `lessons.md` > ~100 lines → distill: fold stable lessons into the target
  `.rules/` file they name (that counts as "adding an example" — allowed), delete
  entries that were one-off, keep the file under 50 lines after distilling.
  Operational CLI / manifest / delta-detection lessons distill into
  `operations.md`; delegation/model-tier lessons into `delegation.md`; the rest
  into whatever their "Applies to" line names.
- `AGENTS.md` > ~150 lines or any `.rules/` file > ~200 lines → propose a trim to
  the user; don't grow past that silently.
- Duplicated guidance in two files → keep it in the more specific file, replace
  the other copy with a one-line pointer.

## Upstream sync protection

This repo is a fork (`wzmf399443/obsidian-wiki`, upstream `Ar9av/obsidian-wiki`).
`.rules/` is fork-local and unknown to upstream — a merge will not touch it, but
`AGENTS.md` WILL conflict with upstream changes. On conflict: keep the local
Session Protocol + pinned-facts sections, take upstream's framework-content
updates (vault structure, skill routing rows), and re-verify that `CLAUDE.md` and
`GEMINI.md` are still symlinks to `AGENTS.md` afterwards. Back up `AGENTS.md`
before any upstream merge.

## Staleness review

If `lessons.md`'s newest entry is >3 months old and sessions are running fine,
that's success, not neglect. But when a pinned fact's verification date is >6
months old and you're about to rely on it for something destructive, re-verify
it first (one cheap check beats one wrong rebuild).
