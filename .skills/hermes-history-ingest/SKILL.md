---
name: hermes-history-ingest
description: >
  Ingest Hermes agent history into the Obsidian wiki. Use this skill when the user wants to mine
  their past Hermes sessions for knowledge, import their ~/.hermes folder, extract insights from
  previous Hermes conversations, or says things like "process my Hermes history", "add my Hermes
  memories to the wiki", "ingest ~/.hermes", or "what have I worked on in Hermes". Also triggers
  when the user mentions Hermes memories, Hermes sessions, ~/.hermes/memories, or Hermes skill logs.
---

# Hermes History Ingest — Conversation & Memory Mining

You are extracting knowledge from the user's Hermes agent history and distilling it into the Obsidian wiki. Hermes stores both free-form memories and structured session transcripts — focus on durable knowledge, not operational telemetry.

This skill can be invoked directly or via the `wiki-history-ingest` router (`/wiki-history-ingest hermes`).

## Before You Start

Follow the shared **Before You Start (config)** steps in `.skills/_shared/history-ingest-common.md`. This skill's history-path variable is `HERMES_HISTORY_PATH` (defaults to `~/.hermes`).

**Shared pipeline** (modes, clustering, distillation routing, writing rules, manifest/bookkeeping, privacy): read `.skills/_shared/history-ingest-common.md` before Step 1; this file only documents what is specific to Hermes.

## Ingest Modes

Append/Full mode semantics are shared — see `.skills/_shared/history-ingest-common.md` (Ingest Modes).

## Hermes Data Layout

Hermes stores all local artifacts under `~/.hermes/` (or `$HERMES_HOME` for non-default profiles).

```
~/.hermes/
├── memories/                          # Persistent agent memories (markdown or JSON)
│   └── *.md / *.json
├── skills/                            # Installed skills (read-only for ingest purposes)
│   └── <skill-name>/SKILL.md
├── sessions/                          # Session transcripts (if session logging is enabled)
│   └── YYYY-MM-DD/
│       └── <session-id>.jsonl
├── config.yaml                        # User config (model, theme, paths)
└── .hub/                              # Skills Hub state (lock.json, audit.log, quarantine/)
```

### Key data sources ranked by value

1. `memories/*.md` / `memories/*.json` — highest signal; curated persistent knowledge the agent accumulated
2. `sessions/**/*.jsonl` — structured turn-by-turn transcripts; rich but noisy
3. `config.yaml` — metadata only (model preferences, paths); rarely worth ingesting

Skip `.hub/` internals (audit/quarantine state) and the `skills/` directory (source material, not user knowledge).

## Step 1: Survey and Compute Delta

Scan `HERMES_HISTORY_PATH` and compare against `.manifest.json`:

- `~/.hermes/memories/`
- `~/.hermes/sessions/**/` (if present)

Classify each file:

- **New** — not in manifest
- **Modified** — in manifest but file is newer than `ingested_at`
- **Unchanged** — already ingested and unchanged

Report a concise delta summary before deep parsing.

## Step 2: Parse Memories First

Memories are the highest-value source. Hermes writes them as either:

- **Markdown** — structured prose with optional frontmatter; ingest directly
- **JSON** — `{"content": "...", "created_at": "...", "tags": [...]}` records

For each memory:

- Extract the core knowledge claim
- Note any tags Hermes attached (they often map to wiki categories)
- Merge into the appropriate wiki page rather than creating one memory = one page

## Step 3: Parse Session JSONL Safely

Each session JSONL line is an event envelope. Common shapes:

```json
{"role": "user", "content": "..."}
{"role": "assistant", "content": "..."}
{"type": "tool_use", "name": "...", "input": {...}}
{"type": "tool_result", "content": "..."}
```

### Extraction rules

- Prioritize assistant responses that state conclusions, patterns, or decisions
- Extract user intent from high-signal turns; skip low-information follow-ups
- Treat `tool_use` / `tool_result` pairs as context, not primary content
- Skip token accounting, internal plumbing, and repeated plan echoes

### Critical privacy filter

Session logs can include injected instructions, tool payloads, and sensitive text. Do not ingest verbatim.

- Remove API keys, tokens, passwords, credentials
- Redact private identifiers unless relevant and user-approved
- Summarize; do not quote raw transcripts verbatim

## Step 4: Cluster by Topic

General clustering guidance is shared — see `.skills/_shared/history-ingest-common.md` (Cluster by Topic). Hermes-specific: use file paths or session `cwd` metadata to infer project scope when available.

## Step 5: Distill into Wiki Pages

Routing, project-page naming, writing rules, and provenance markers are shared — see `.skills/_shared/history-ingest-common.md` (Distill into Wiki Pages). Hermes provenance uses the generic mapping (extracted when directly grounded in explicit memory/session content; inferred when synthesizing patterns across multiple memories; ambiguous when memories conflict).

## Step 6: Update Manifest, Log, and Index

Follow the shared **Update Manifest, Log, and Index** procedure (`.skills/_shared/history-ingest-common.md`). Hermes specifics:

- `source_type`: `hermes_memory` | `hermes_session`
- Top-level summary block:
  ```json
  {
    "hermes": {
      "source_path": "~/.hermes/",
      "last_ingested": "TIMESTAMP",
      "memories_ingested": 42,
      "sessions_ingested": 7,
      "pages_created": 5,
      "pages_updated": 12
    }
  }
  ```
- Log line for `log.md`:
  ```
  - [TIMESTAMP] HERMES_HISTORY_INGEST memories=N sessions=M pages_updated=X pages_created=Y mode=append|full
  ```
- hot.md sample sentence: "Ingested 42 Hermes memories and 7 sessions; dominant themes: reasoning strategies, tool use patterns."

## Privacy

See shared **Privacy** in `.skills/_shared/history-ingest-common.md`. Session-specific redaction rules are in the Step 3 "Critical privacy filter" above.

## Reference

See `references/hermes-data-format.md` for field-level notes and extraction guidance.

## QMD Refresh After Vault Writes

If `$QMD_WIKI_COLLECTION` is set, follow the shared procedure in `.skills/_shared/qmd-refresh.md` after writing vault markdown and record the QMD status line it defines. If unset, record `QMD skipped: QMD_WIKI_COLLECTION unset`.
