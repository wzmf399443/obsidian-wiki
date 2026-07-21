# History Ingest — Shared Pipeline

Canonical copy of the parts shared by every per-tool history-ingest skill
(`claude`, `codex`, `copilot`, `hermes`, `openclaw`, `pi`). Each skill file
references this file instead of embedding these blocks, and documents only what
is specific to its own tool (data layout, parsing, source_type values, etc.).

Throughout this file, `$<TOOL>_HISTORY_PATH` is a placeholder for the calling
skill's own history-path variable (e.g. `$CLAUDE_HISTORY_PATH`,
`$CODEX_HISTORY_PATH`). Each skill declares its variable name and default path in
its own **Before You Start** step.

## Before You Start (config)

1. **Resolve config** — follow the Config Resolution Protocol in `llm-wiki/SKILL.md` (inline `@name` override → walk up CWD for `.env` → `~/.obsidian-wiki/config` → prompt setup). This gives `OBSIDIAN_VAULT_PATH` and the skill's own `$<TOOL>_HISTORY_PATH` (see the skill file for its variable name and default path).
2. Read `.manifest.json` at the vault root to check what has already been ingested.
3. Read `index.md` at the vault root to know what the wiki already contains.

## Ingest Modes

### Append Mode (default)

Check `.manifest.json` for each tracked source (file or session). Only process:

- Sources not in the manifest (new material)
- Sources whose freshness timestamp — file modification time, or the source's own `updated_at` where it carries one — is newer than their `ingested_at` in the manifest

This is the default for regular syncs — the user ran a few new sessions and wants to capture just the delta.

### Full Mode

Process everything regardless of manifest. Use after a `wiki-rebuild` or if the user explicitly asks for a full re-ingest.

## Cluster by Topic

Don't create one wiki page per session, conversation, or memory. Instead:

- Group extracted knowledge **by stable topic** across sessions.
- Split a mixed session into separate themes — e.g. one session about "debugging auth + setting up CI" → two topics.
- Merge recurring patterns across dates and projects — e.g. three sessions across different days about "React performance" → one merged topic.
- Infer project scope from the session's working directory / project metadata. Each skill documents which field to use (`cwd`, `repository`, workspace path, `session_info.name`, etc.).

## Distill into Wiki Pages

Route extracted knowledge using existing wiki conventions. Each skill documents how it derives the project name from its own metadata.

### Project-specific vs. global knowledge

| What you found                     | Where it goes               | Example                                             |
| ---------------------------------- | --------------------------- | --------------------------------------------------- |
| Project architecture decisions     | `projects/<name>/concepts/` | `projects/my-project/concepts/main-architecture.md` |
| Project-specific debugging         | `projects/<name>/skills/`   | `projects/my-project/skills/api-rate-limiting.md`   |
| General concept the user learned   | `concepts/` (global)        | `concepts/react-server-components.md`               |
| Recurring problem across projects  | `skills/` (global)          | `skills/debugging-hydration-errors.md`              |
| A tool/service used                | `entities/` (global)        | `entities/vercel-functions.md`                      |
| Patterns across many sessions      | `synthesis/` (global)       | `synthesis/common-debugging-patterns.md`            |

### Writing rules

- **Distill the _knowledge_, not the conversation/chronology.** Don't write "In a session on March 15, the user asked about X." Write the knowledge itself, with the session as a source attribution. Avoid "on date X we discussed..." unless date context is essential.
- For each impacted project, create or update the project overview page at `projects/<name>/<name>.md` — **named after the project, not `_project.md`**. Obsidian's graph view uses the filename as the node label, so `_project.md` makes every project show up as `_project` in the graph. Naming it `<name>.md` gives each project a distinct, readable node name.
- **Write a `summary:` frontmatter field** on every new/updated page — 1–2 sentences, ≤200 chars, answering "what is this page about?" for a reader who hasn't opened it. `wiki-query`'s cheap retrieval path reads this field to avoid opening page bodies.
- **Add confidence and lifecycle fields** to every new page's frontmatter:
  ```yaml
  base_confidence: 0.42
  lifecycle: draft
  lifecycle_changed: <ISO date today>
  ```
  On update, leave `lifecycle` and `lifecycle_changed` unchanged — only a human editor transitions lifecycle state.
- **Mark provenance** per the convention in `llm-wiki` (Provenance Markers section):
  - *No marker* (default) when a claim is directly grounded in explicit source content — extracted claims are unmarked.
  - `^[inferred]` when synthesizing patterns across sources, generalizing across sessions, or filling in implicit reasoning.
  - `^[ambiguous]` when sources conflict or the user changed their mind.
  - Write a `provenance:` frontmatter block on every new/updated page summarizing the rough mix.
  - Some skills add a tool-specific mapping of which source types count as extracted vs inferred (e.g. pre-distilled memories/checkpoints vs synthesized conversation) — see the skill file.

## Update Manifest, Log, and Index

### Update `.manifest.json`

For each processed source file, add/update its entry with:

- `ingested_at`, `size_bytes`, `modified_at`
- `source_type`: the value(s) are tool-specific — see the skill file.
- `project`: the inferred/decoded project name (when applicable).
- `pages_created` and `pages_updated` lists.

Then add/update the top-level project/summary block for this source. Its exact shape is tool-specific — see the skill file.

### Update index.md and log.md

Reflect any new pages in `index.md` and append a log line to `log.md`. The log-line format is tool-specific — see the skill file.

### Update hot.md

**`hot.md`** — Read `$OBSIDIAN_VAULT_PATH/hot.md` (create from the template in `wiki-ingest` if missing). Update **Recent Activity** with a one-line summary of this ingest (see the skill file for a sample sentence). Keep the last 3 operations. Update **Active Threads** if any ongoing project is now better understood. **Update the `updated:` field in the frontmatter** to the current timestamp — this is easy to forget; the body edit and the frontmatter bump must both happen.

## Privacy

- Distill and synthesize — don't copy raw conversation/memory/transcript text verbatim.
- Skip or redact anything that looks like secrets, API keys, passwords, tokens, or credentials.
- If you encounter personal/sensitive content, ask the user before including it; keep references to other people minimal and purpose-bound.
