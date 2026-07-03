# Obsidian Wiki — Agent Context

A **skill-based framework** for building and maintaining an Obsidian knowledge base.
No scripts or dependencies — everything is markdown instructions you execute directly.

> **Single source:** `CLAUDE.md` and `GEMINI.md` are symlinks to this file
> (`AGENTS.md`). Edit `AGENTS.md` only — never replace the symlinks with copies.

## Session Protocol — read before doing work

Operating rules live in `.rules/`. Don't read them all upfront — load on trigger.
If a referenced file is missing, ignore that reference and continue.

| Read this | When |
|---|---|
| `.rules/delegation.md` | BEFORE any task that reads >3 files, scans dirs/history, does web research, or edits >3 pages. Non-negotiable for ingest/lint/dedup/cross-link runs. |
| `.rules/judgment.md` | Before declaring a task done; before any destructive op (merge, delete, rebuild); when stuck or retrying; when the ask is ambiguous. |
| `.rules/templates.md` | When writing a subagent prompt (copy the matching template). |
| `.rules/maintenance.md` | Before editing anything in `.rules/` or this file. |
| `.rules/lessons.md` | At session start if working on wiki maintenance — recent mistakes live here. |
| `.rules/diagnosis.md` | Only for background on why these rules exist. |
| `.rules/letter.md` | If you can't state this vault's #1 safety warning (hint: mixed untagged company data), you haven't read it — read it now. Also before any export/publish. |

**Prime directive:** the main conversation is a commander, not a worker. Bulk
reading and batch writing go to subagents; the main context holds decisions.

## Configuration — pinned facts (verified 2026-07-03)

- **`.env` exists at this repo's root and is the active config.** Read it once;
  skip the walk-up/global-config search described below unless it's missing.
- QMD is NOT configured → skills fall back to Grep/Glob. Staged writes are off.
  Link format is `wikilink`. Max 15 pages per ingest.
- If an operation fails in a way a stale pin would explain (e.g. vault path gone),
  re-verify and update this section (see `.rules/maintenance.md`).

Fallback resolution order when `.env` is absent: (1) walk up from CWD to `$HOME`
looking for a `.env` containing `OBSIDIAN_VAULT_PATH`; (2) `~/.obsidian-wiki/config`;
(3) tell the user to run `wiki-setup`. Full protocol: `.skills/llm-wiki/SKILL.md`.

**After reading config, read the vault's owner-conventions file** — it overrides
framework defaults for the whole session. Check `$OBSIDIAN_VAULT_PATH/AGENTS.md`
first; if absent, `$OBSIDIAN_VAULT_PATH/CLAUDE.md` (this vault uses that filename —
it holds real conventions, e.g. respond in Traditional Chinese).

## Vault Structure

```
$OBSIDIAN_VAULT_PATH/
├── index.md          # Master index — every page listed, always current
├── log.md            # Chronological activity log
├── hot.md            # ~500-word snapshot of recent activity — read at session start
├── .manifest.json    # Every ingested source: path, timestamps, pages produced
├── _meta/            # taxonomy.md (tag vocabulary) + *.base dashboards
├── _insights.md      # Graph analysis output
├── _raw/             # Staging — rough notes promoted on next ingest
├── concepts/ entities/ skills/ references/ synthesis/ journal/
└── projects/<name>.md  # One page per project synced via wiki-update
```

Required frontmatter on every page: `title`, `category`, `tags`, `sources`,
`created`, `updated`. Pages connect via `[[wikilinks]]` (or Markdown links when
`OBSIDIAN_LINK_FORMAT=markdown`).

## Skill Routing

Skills live in `.skills/<name>/SKILL.md`. Match intent to skill:

| Intent | Skill |
|---|---|
| "set up my wiki" / "initialize" | `wiki-setup` |
| "/wiki-history-ingest <agent>" (claude/codex/hermes/openclaw/copilot/pi) | `wiki-history-ingest` (router) |
| "import my <agent> history" / "mine my sessions" / mentions `~/.claude`, `~/.codex`, `~/.hermes`, `~/.openclaw`, `~/.copilot`, `~/.pi` | `<agent>-history-ingest` |
| "/wiki-claude [topic]" etc. — topic-targeted pull from one agent's history | `wiki-agent` |
| "/ingest-url <url>" / "save this page" | `ingest-url` |
| "ingest" / "add this to the wiki" / "process these docs" / `_raw/` promotion | `wiki-ingest` |
| "process this export" / logs, transcripts, chat dumps | `data-ingest` |
| "ingest the obsidian-wiki project" | `obsidian-wiki-ingest` |
| "what's the status" / "show the delta" / "wiki insights" / "hubs" | `wiki-status` |
| "what do I know about X" / any knowledge question | `wiki-query` |
| "audit" / "lint" / "broken links" (`--consolidate` = act mode) | `wiki-lint` |
| "dedup" / "merge duplicates" / "consolidate my wiki" | `wiki-dedup` |
| "rebuild" / "start over" / "archive" / "restore" | `wiki-rebuild` |
| "link my pages" / "cross-reference" / "orphans" | `cross-linker` |
| "fix my tags" / "tag audit" | `tag-taxonomy` |
| "update wiki" / "sync to wiki" (from any project) | `wiki-update` |
| "export wiki" / "graphml" / "neo4j" | `wiki-export` |
| "color my graph" | `graph-colorize` |
| "save this" / "/wiki-capture" / "file this conversation" | `wiki-capture` |
| "/wiki-research [topic]" / autonomous web research → wiki | `wiki-research` |
| "create a dashboard" / "show all X as a table" | `wiki-dashboard` |
| "synthesize" / "find connections" / "/wiki-synthesize" | `wiki-synthesize` |
| "/wiki-context-pack" / "context slice for X" | `wiki-context-pack` |
| "/wiki-stage-commit" / "review staged pages" | `wiki-stage-commit` |
| "/wiki-digest" / "what did I learn this week" | `wiki-digest` |
| "/wiki-switch NAME" / "list my wikis" | `wiki-switch` |
| "/memory-bridge" / "compare tool memories" | `memory-bridge` |
| "/daily-update" / "morning sync" / cron setup | `daily-update` |
| "/impl-validator" / "validate what you did" | `impl-validator` |
| "create a new skill" | `skill-creator` |
| wiki pattern theory / architecture questions | `llm-wiki` |

## Cross-Project Usage

From any directory: `wiki-update` distills the current project into
`$VAULT/projects/<name>.md` (delta-only on repeat runs via `last_commit_synced`
in `.manifest.json`); `wiki-query` answers from the wiki (index/frontmatter pass
first, page bodies only if needed, `[[wikilink]]` citations in the answer).

## Visibility Tags (optional)

Pages may carry `visibility/public` (default when untagged), `visibility/internal`,
or `visibility/pii`. Filtered mode is opt-in — phrases like "public only" /
"as a user would see it" exclude internal+pii from query/export results. These are
system tags: they don't count toward the 5-tag limit. Details in `wiki-query` /
`wiki-export` skills.

> **Warning for THIS vault:** pages are mostly untagged, and untagged counts as
> public — so filtered mode does not make export/sharing safe here. Any
> export/publish/share is on the always-ask list (`.rules/judgment.md` R3).

## Core Principles

- **Compile, don't retrieve.** Update existing pages — don't append or duplicate.
- **Track everything.** After any write: `.manifest.json` (ingests), `index.md`,
  `log.md`, `hot.md`. A write without bookkeeping is not done (`.rules/judgment.md`).
- **Delegate bulk work.** Scans, history mining, batch edits → subagents
  (`.rules/delegation.md`). Main context holds decisions, not data.
- **Verify, don't self-certify.** Multi-page writes get a fresh-context read-back
  (`impl-validator`). The producer never signs off on its own output.
- **Connect with `[[wikilinks]]`.** Every page links to related pages.
- **Keep context warm.** `hot.md` is the session-to-session handoff — read it at
  start, update it after writes.

Full architecture pattern: `.skills/llm-wiki/SKILL.md`.
