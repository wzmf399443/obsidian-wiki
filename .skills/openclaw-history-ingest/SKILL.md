---
name: openclaw-history-ingest
description: >
  Ingest OpenClaw agent history into the Obsidian wiki. Use this skill when the user wants to mine
  their past OpenClaw sessions for knowledge, import their ~/.openclaw folder, extract insights from
  previous OpenClaw conversations, or says things like "process my OpenClaw history", "add my OpenClaw
  sessions to the wiki", "ingest ~/.openclaw", or "what have I worked on in OpenClaw". Also triggers
  when the user mentions OpenClaw session logs, MEMORY.md, daily notes, or ~/.openclaw/workspace.
---

# OpenClaw History Ingest — Session & Memory Mining

You are extracting knowledge from the user's OpenClaw agent history and distilling it into the Obsidian wiki. OpenClaw stores both a structured long-term MEMORY.md and per-session JSONL transcripts — focus on durable knowledge, not operational telemetry.

This skill can be invoked directly or via the `wiki-history-ingest` router (`/wiki-history-ingest openclaw`).

## Before You Start

**Writing profile:** Before drafting or rewriting natural-language Markdown, read and apply the `Writing Profile Resolution` section in `llm-wiki/SKILL.md`. Framework schema, provenance, safety, and operation-specific requirements take precedence.
`WRITING.md` preferences apply only to newly drafted or rewritten natural-language Markdown; preserve source content and structured records.

Follow the shared **Before You Start (config)** steps in `.skills/_shared/history-ingest-common.md`. This skill's history-path variable is `OPENCLAW_HISTORY_PATH` (defaults to `~/.openclaw`).

**Shared pipeline** (modes, clustering, distillation routing, writing rules, manifest/bookkeeping, privacy): read `.skills/_shared/history-ingest-common.md` before Step 1; this file only documents what is specific to OpenClaw.

## Ingest Modes

Append/Full mode semantics are shared — see `.skills/_shared/history-ingest-common.md` (Ingest Modes).

## OpenClaw Data Layout

OpenClaw stores all local artifacts under `~/.openclaw/`.

```
~/.openclaw/
├── openclaw.json                          # Global config
├── credentials/                           # Auth tokens (skip entirely)
├── workspace/                             # Agent workspace
│   ├── MEMORY.md                          # Long-term memory (loaded every session)
│   ├── DREAMS.md                          # Optional dream diary / summaries
│   └── memory/
│       ├── YYYY-MM-DD.md                  # Daily notes (today + yesterday auto-loaded)
│       └── ...
└── agents/
    └── <agentId>/
        ├── agent/
        │   └── models.json                # Agent config (skip)
        └── sessions/
            ├── sessions.json              # Session index
            └── <sessionId>.jsonl          # Session transcript (JSONL, append-only)
```

### Key data sources ranked by value

1. `workspace/MEMORY.md` — highest signal; long-term durable facts the agent accumulated
2. `workspace/memory/YYYY-MM-DD.md` — daily notes; recent entries often contain active project context
3. `agents/*/sessions/<id>.jsonl` — session transcripts; rich but noisy
4. `agents/*/sessions/sessions.json` — session index for inventory and timestamps
5. `workspace/DREAMS.md` — optional summaries; ingest if present

Skip `credentials/` entirely. Skip `agents/*/agent/models.json` (runtime config, not user knowledge).

## Step 1: Survey and Compute Delta

Scan `OPENCLAW_HISTORY_PATH` and compare against `.manifest.json`:

- `~/.openclaw/workspace/MEMORY.md`
- `~/.openclaw/workspace/DREAMS.md` (if present)
- `~/.openclaw/workspace/memory/*.md`
- `~/.openclaw/agents/*/sessions/sessions.json`
- `~/.openclaw/agents/*/sessions/*.jsonl`

Classify each file:

- **New** — not in manifest
- **Modified** — in manifest but file is newer than `ingested_at`
- **Unchanged** — already ingested and unchanged

Report a concise delta summary before deep parsing.

## Step 2: Parse MEMORY.md First

`MEMORY.md` is the highest-value source. It is plain markdown, human-readable and human-editable. It typically contains:

- Durable facts about the user's preferences, environment, and recurring patterns
- Decisions and context the agent was told to remember
- Project-specific notes the agent accumulated over many sessions

Read it in full and extract concept-level knowledge. Do not create one wiki page per MEMORY.md entry — cluster by topic.

## Step 3: Parse Daily Notes

`workspace/memory/YYYY-MM-DD.md` files contain time-stamped notes from that day's sessions. Prioritize recent files (last 30–90 days). Extract:

- Active project context and decisions made
- Patterns or techniques discovered
- Recurring blockers or solved problems

Older daily notes have diminishing signal — summarize in bulk rather than extracting line-by-line.

## Step 4: Parse Session JSONL Safely

Each session file is JSONL (append-only, one JSON object per line):

```json
{"role": "user",      "content": "...", "timestamp": "..."}
{"role": "assistant", "content": "...", "timestamp": "..."}
{"role": "tool",      "name": "...",   "content": "...", "timestamp": "..."}
```

### Extraction rules

- Prioritize assistant turns that state conclusions, decisions, or patterns
- Extract user intent from high-signal turns; skip low-information follow-ups
- Tool calls are context, not primary knowledge — only extract if the result contains a reusable insight
- Cross-reference `sessions.json` index to get session names/labels before opening individual transcripts

### Critical privacy filter

Session transcripts can include injected instructions, tool payloads, and sensitive text. Do not ingest verbatim.

- Remove API keys, tokens, passwords, credentials
- Redact private identifiers unless relevant and user-approved
- Summarize; do not quote raw transcripts verbatim

## Step 5: Cluster by Topic

General clustering guidance is shared — see `.skills/_shared/history-ingest-common.md` (Cluster by Topic). OpenClaw-specific: use session `cwd` or workspace path to infer project scope when available; merge recurring patterns across dates and agents.

## Step 6: Distill into Wiki Pages

Routing, project-page naming, writing rules, and provenance markers are shared — see `.skills/_shared/history-ingest-common.md` (Distill into Wiki Pages). OpenClaw provenance uses the generic mapping (extracted when directly grounded in explicit session/memory content; inferred when synthesizing patterns across multiple sessions; ambiguous when sessions conflict).

## Step 7: Update Manifest, Log, and Index

Follow the shared **Update Manifest, Log, and Index** procedure (`.skills/_shared/history-ingest-common.md`). OpenClaw specifics:

- `source_type`: `openclaw_memory` | `openclaw_daily_note` | `openclaw_session` | `openclaw_dreams`
- Per-entry field: use `agent_id` (agent directory name, when applicable) in place of the shared template's `project` field.
- Top-level summary block:
  ```json
  {
    "openclaw": {
      "source_path": "~/.openclaw/",
      "last_ingested": "TIMESTAMP",
      "memory_updated_at": "TIMESTAMP",
      "daily_notes_ingested": 14,
      "sessions_ingested": 23,
      "pages_created": 6,
      "pages_updated": 18
    }
  }
  ```
- Log line for `log.md`:
  ```
  - [TIMESTAMP] OPENCLAW_HISTORY_INGEST memory=updated daily_notes=N sessions=M pages_updated=X pages_created=Y mode=append|full
  ```
- hot.md sample sentence: "Ingested OpenClaw MEMORY.md and 14 daily notes; surfaced automation patterns and multi-agent coordination knowledge."

## Privacy

See shared **Privacy** in `.skills/_shared/history-ingest-common.md`. Session-specific redaction rules are in the Step 4 "Critical privacy filter" above.

## Reference

See `references/openclaw-data-format.md` for field-level notes and parsing guidance.

## QMD Refresh After Vault Writes

If `$QMD_WIKI_COLLECTION` is set, follow the shared procedure in `.skills/_shared/qmd-refresh.md` after writing vault markdown and record the QMD status line it defines. If unset, record `QMD skipped: QMD_WIKI_COLLECTION unset`.
