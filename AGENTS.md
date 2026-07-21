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
| `.rules/operations.md` | Before an ingest run, before computing an ingest delta by hand, or before touching `.manifest.json` / the `obsidian-wiki` CLI — CLI-invocation and manifest gotchas live here. |
| `.rules/diagnosis.md` | Only for background on why these rules exist. |
| `.rules/letter.md` | If you can't state this vault's #1 safety warning (hint: mixed untagged company data), you haven't read it — read it now. Also before any export/publish. |

**Prime directive:** the main conversation is a commander, not a worker. Bulk
reading and batch writing go to subagents; the main context holds decisions.

## Configuration — pinned facts (verified 2026-07-03, routing rules added 2026-07-04)

- **`.env` exists at this repo's root and is the active config.** Read it once;
  skip the resolution protocol below unless it's missing or an `@name` override
  is in play.
- QMD is NOT configured → skills fall back to Grep/Glob. Staged writes are off.
  Link format is `wikilink`. Max 15 pages per ingest.
- If an operation fails in a way a stale pin would explain (e.g. vault path gone),
  re-verify and update this section (see `.rules/maintenance.md`).

Full Config Resolution Protocol when `.env` is absent or an `@name` override is
present: 0. **Inline vault override (`@name`)** — if the request contains an
`@<name>` token, resolve `~/.obsidian-wiki/config.<name>` directly for that
invocation only (see "Targeting a specific vault" below); 1. walk up from CWD to
`$HOME` looking for a `.env` containing `OBSIDIAN_VAULT_PATH`; 2.
`~/.obsidian-wiki/config`; 3. tell the user to run `wiki-setup`. Full protocol:
`.skills/llm-wiki/SKILL.md`.

### Targeting a specific vault

You can maintain multiple vaults (each a `~/.obsidian-wiki/config.<name>` file
managed by `wiki-switch`) and reach any of them from any directory:

- **`@name` (per-invocation override)** — prefix or mention `@<name>` anywhere
  in a request to route that one command to that vault, e.g. `@work save this`
  or `wiki-query @personal what do I know about X`. It overrides the CWD `.env`
  and the active symlink **for that invocation only** — it does **not** flip
  your default vault. If `config.<name>` doesn't exist, the skill reports it and
  lists available vaults; do **not** silently fall back to the default. The
  `@name` is stripped before the rest of the request is used as content.
- **`/wiki-switch <name>` (persistent default)** — re-points the active symlink
  so all future requests use that vault. This is your default "brain" vault;
  use `@name` to dip into the other one without switching.

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
| "/wiki-history-ingest claude" / "/wiki-history-ingest codex" / "/wiki-history-ingest hermes" / "/wiki-history-ingest pi" | `wiki-history-ingest` |
| "ingest" / "add this to the wiki" / "process these docs" / "process this export" / "ingest this data" / logs, transcripts / "/ingest-url <url>" / "add this URL" / "ingest this link" / "save this page" | `wiki-ingest` |
| "import my Claude history" / "mine my conversations" | `claude-history-ingest` |
| "import my Codex history" / "mine my Codex sessions" | `codex-history-ingest` |
| "import my Hermes history" / "mine my Hermes memories" / "ingest ~/.hermes" | `hermes-history-ingest` |
| "import my OpenClaw history" / "mine my OpenClaw sessions" / "ingest ~/.openclaw" | `openclaw-history-ingest` |
| "import my Copilot history" / "mine my Copilot sessions" / "ingest ~/.copilot" | `copilot-history-ingest` |
| "import my Pi history" / "mine my Pi sessions" / "ingest ~/.pi" | `pi-history-ingest` |
| "what's the status" / "what's been ingested" / "show the delta" | `wiki-status` |
| "wiki insights" / "hubs" / "wiki structure" | `wiki-status` (insights mode) |
| "what do I know about X" / "find info on Y" / any question | `wiki-query` |
| "audit" / "lint" / "find broken links" / "wiki health" | `wiki-lint` |
| "dedup my wiki" / "find duplicate pages" / "merge duplicates" / "identity resolution" / "consolidate my wiki" | `wiki-dedup` |
| "rebuild" / "start over" / "archive" / "restore" | `wiki-rebuild` |
| "link my pages" / "cross-reference" / "connect my wiki" | `cross-linker` |
| "fix my tags" / "normalize tags" / "tag audit" | `tag-taxonomy` |
| "update wiki" / "sync to wiki" / "save this to my wiki" | `wiki-update` |
| `@work update wiki` / `wiki-query @personal ...` / `@research save this` | Any matching wiki skill + Config Resolution Protocol `@name` override |
| "export wiki" / "export graph" / "graphml" / "neo4j" / "export to OKF" / "OKF bundle" / "open knowledge format" | `wiki-export` |
| "import wiki" / "import from export" / "load graph.json" / "import vault" / "import OKF bundle" / "/wiki-import" | `wiki-import` |
| "color my graph" / "color code obsidian" / "color by tag/category/visibility" | `graph-colorize` |
| "save this" / "/wiki-capture" / "capture this" / "file this conversation" / "/wiki-capture --quick" / "quick capture" / "capture this finding" / "save this gotcha" / "drop to raw" | `wiki-capture` |
| "/wiki-research [topic]" / "research X" / "find everything about Y" | `wiki-research` |
| "create a dashboard" / "vault dashboard" / "show all X as a table" / "dynamic view" | `wiki-dashboard` |
| "synthesize my wiki" / "find connections" / "what concepts keep coming up together" / "/wiki-synthesize" | `wiki-synthesize` |
| "create a new skill" | `skill-creator` |
| "/vault-skill-factory" / "make a skill from my wiki" / "turn these pages into a skill" / "package my notes on X as a skill" / "build a domain-expert skill from my vault" | `vault-skill-factory` |
| "/wiki-claude [topic]" / "/wiki-codex [topic]" / "/wiki-hermes [topic]" / "/wiki-openclaw [topic]" / "/wiki-copilot [topic]" / "/wiki-pi [topic]" | `wiki-agent` |
| "/memory-bridge" / "browse codex memory" / "what did codex know about X" / "compare tool memories" / "cross-tool memory" | `memory-bridge` |
| "/daily-update" / "morning sync" / "refresh the wiki index" / "set up the daily cron" / "install terminal notification" | `daily-update` |
| "/impl-validator" / "check this implementation" / "validate what you did" / "is this correct?" | `impl-validator` |
| "/wiki-switch NAME" / "switch to my work wiki" / "switch vault" / "change wiki" / "list my wikis" / "show my vaults" / "create a new vault config" | `wiki-switch` |
| "/wiki-digest" / "what did I learn this week" / "weekly digest" / "knowledge summary" / "what's new in my wiki" / "summarize my recent learning" / "monthly review" | `wiki-digest` |
| "/wiki-stage-commit" / "review staged pages" / "commit staged writes" | `wiki-stage-commit` |
| "/wiki-context-pack" / "context slice for X" | `wiki-context-pack` |
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

## Architecture Reference

For the full pattern (three-layer architecture, page templates, project org), read `.skills/llm-wiki/SKILL.md`.

The vault format is structurally conformant with the [Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) — markdown files with YAML frontmatter, category subfolders, reserved `index.md`/`log.md`. `wiki-export` (OKF mode) and `wiki-import` are the bridge: they translate between our native frontmatter (`title`/`category`/`tags`/`sources`/`created`/`updated` + `summary`) and OKF (`type`/`title`/`description`/`resource`/`tags`/`timestamp`), making vaults exchangeable with any OKF tool. The OKF round-trip is lossless; the `graph.json` round-trip is not.
