---
name: codex-history-ingest
description: >
  Ingest Codex CLI conversation history into the Obsidian wiki. Use this skill when the user wants to mine
  their past Codex sessions for knowledge, import their ~/.codex folder, extract insights from previous coding
  sessions, or says things like "process my Codex history", "add my Codex conversations to the wiki", or
  "what have I discussed in Codex before". Also triggers when the user mentions .codex sessions, rollout files,
  session_index.jsonl, or Codex transcript logs.
---

# Codex History Ingest — Conversation Mining

You are extracting knowledge from the user's past Codex sessions and distilling it into the Obsidian wiki. Session logs are rich but noisy: focus on durable knowledge, not operational telemetry.

This skill can be invoked directly or via the `wiki-history-ingest` router (`/wiki-history-ingest codex`).

## Before You Start

Follow the shared **Before You Start (config)** steps in `.skills/_shared/history-ingest-common.md`. This skill's history-path variable is `CODEX_HISTORY_PATH` (defaults to `~/.codex`).

**Shared pipeline** (modes, clustering, distillation routing, writing rules, manifest/bookkeeping, privacy): read `.skills/_shared/history-ingest-common.md` before Step 1; this file only documents what is specific to Codex.

## Ingest Modes

Append/Full mode semantics are shared — see `.skills/_shared/history-ingest-common.md` (Ingest Modes).

## Codex Data Layout

Codex stores local artifacts under `~/.codex/`.

```
~/.codex/
├── sessions/                          # Session rollout logs by date
│   └── YYYY/MM/DD/
│       └── rollout-<timestamp>-<id>.jsonl
├── archived_sessions/                 # Archived rollout logs
├── session_index.jsonl                # Lightweight index of thread id/name/updated_at
├── history.jsonl                      # Local transcript history (if persistence enabled)
├── config.toml                        # User config (contains history settings)
└── state_*.sqlite / logs_*.sqlite     # Runtime DBs (usually skip)
```

### Key data sources ranked by value

1. `session_index.jsonl` — best inventory source for IDs, titles, and freshness
2. `sessions/**/rollout-*.jsonl` — rich structured transcript events
3. `history.jsonl` — useful fallback/timeline aid if enabled

Avoid ingesting SQLite internals unless the user explicitly asks.

## Step 1: Survey and Compute Delta

Scan `CODEX_HISTORY_PATH` and compare against `.manifest.json`:

- `~/.codex/session_index.jsonl`
- `~/.codex/sessions/**/rollout-*.jsonl`
- `~/.codex/archived_sessions/**` (optional; only if user asks for archived history)
- `~/.codex/history.jsonl` (optional fallback)

Classify each file:

- **New** — not in manifest
- **Modified** — in manifest but file is newer than `ingested_at`
- **Unchanged** — already ingested and unchanged

Report a concise delta summary before deep parsing.

## Step 2: Parse Session Index First

`session_index.jsonl` typically has entries like:

```json
{"id":"...","thread_name":"...","updated_at":"..."}
```

Use it to:

- Build a canonical session inventory
- Prioritize recent/high-signal sessions
- Map rollout IDs to human-readable thread names

## Step 3: Parse Rollout JSONL Safely

Each `rollout-*.jsonl` line is an event envelope with:

```json
{
  "timestamp": "...",
  "type": "session_meta|turn_context|event_msg|response_item",
  "payload": { ... }
}
```

### Extraction rules

- Prioritize user intent and assistant-visible outputs
- Favor `response_item` records with user/assistant message content
- Use `event_msg` selectively for meaningful milestones; ignore pure telemetry
- Treat `session_meta` as metadata (cwd, model, ids), not user knowledge

### Skip/noise filters

- Token accounting events
- Tool plumbing with no semantic content
- Raw command output unless it contains reusable decisions/patterns
- Repeated plan snapshots unless they add novel decisions

### Critical privacy filter

Rollout logs can include injected instructions, tool payloads, and sensitive text. Do not ingest verbatim system/developer prompts or secrets.

- Remove API keys, tokens, passwords, credentials
- Redact private identifiers unless relevant and approved
- Summarize instead of quoting raw transcripts

## Step 4: Cluster by Topic

General clustering guidance is shared — see `.skills/_shared/history-ingest-common.md` (Cluster by Topic). Codex-specific: use `cwd` from session metadata to infer project scope.

## Step 5: Distill into Wiki Pages

Routing, project-page naming, writing rules, and provenance markers are shared — see `.skills/_shared/history-ingest-common.md` (Distill into Wiki Pages). Codex specifics:

- Derive the project name from the session's `cwd`.
- Provenance uses the generic extracted/inferred/ambiguous mapping from the shared file (extracted when directly grounded in explicit session content; inferred when synthesizing patterns across events/sessions; ambiguous when sessions conflict).

## Step 6: Update Manifest, Log, and Index

Follow the shared **Update Manifest, Log, and Index** procedure (`.skills/_shared/history-ingest-common.md`). Codex specifics:

- `source_type`: `codex_rollout` | `codex_index` | `codex_history`
- Top-level project/session summary block:
  ```json
  {
    "project-name": {
      "source_path": "~/.codex/sessions/...",
      "last_ingested": "TIMESTAMP",
      "sessions_ingested": 12,
      "sessions_total": 40,
      "index_updated_at": "TIMESTAMP"
    }
  }
  ```
- Log line for `log.md`:
  ```
  - [TIMESTAMP] CODEX_HISTORY_INGEST sessions=N pages_updated=X pages_created=Y mode=append|full
  ```
- hot.md sample sentence: "Ingested 12 Codex sessions; surfaced recurring patterns in CLI tooling and shell scripting."

## Privacy

See shared **Privacy** in `.skills/_shared/history-ingest-common.md`. Rollout-specific redaction rules are in the Step 3 "Critical privacy filter" above.

## Reference

See `references/codex-data-format.md` for field-level parsing notes and extraction guidance.

## QMD Refresh After Vault Writes

If `$QMD_WIKI_COLLECTION` is set, follow the shared procedure in `.skills/_shared/qmd-refresh.md` after writing vault markdown and record the QMD status line it defines. If unset, record `QMD skipped: QMD_WIKI_COLLECTION unset`.
