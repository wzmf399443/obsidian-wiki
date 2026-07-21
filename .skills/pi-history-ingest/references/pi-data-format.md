# Pi Data Format — Detailed Reference

This reference expands the field-level parsing notes for Pi coding agent session
ingestion. It restates and details what `SKILL.md` already establishes about the
`~/.pi/agent/sessions/` layout — it does not introduce new fields beyond what the
skill's schema table describes.

## Root Layout

Pi stores sessions under `~/.pi/agent/sessions/` (or the path set by the
`PI_CODING_AGENT_SESSION_DIR` environment variable, surfaced to the skill as
`PI_HISTORY_PATH`):

```
~/.pi/agent/sessions/
├── --<cwd-path>--/                    # Working directory with / replaced by -
│   └── <timestamp>_<uuid>.jsonl       # Session JSONL file
└── ...
```

- The **parent directory name** encodes the working directory the session was
  created in. Decode it the same way as Claude Code's project directories:
  strip the leading `--`, replace `-` with `/`, being cautious that dashes can
  also appear inside real path segments — prefer the `cwd` field from the
  session's `session` header entry as the canonical source when in doubt.
- The **filename** is `<ISO-timestamp>_<uuid>.jsonl`. The timestamp gives a
  cheap sort/triage signal before opening the file; the UUID is the session
  identity.

## Session JSONL Shape

Each `.jsonl` file is a **tree**, not a flat transcript:

- **Line 1** is always a `session` header entry.
- Every subsequent line is a tree node with an `id` and a `parentId`, so a
  session can branch (e.g. via `/tree`) and later entries may not be linear
  descendants of the immediately preceding line.

This means naive top-to-bottom reading can pull in abandoned branches as if
they were the final conversation. Always reconstruct the active path (see
"Reconstructing the Active Branch" below) before treating content as the
session's real outcome.

### Entry Type Reference

| `type` | Purpose | Ingest? |
|---|---|---|
| `session` | Header with `cwd`, `version`, `id`, `timestamp` | Metadata only |
| `message` | Conversation turn (`user`, `assistant`, `toolResult`, `bashExecution`, etc.) | **Primary source** |
| `session_info` | Display name set via `/name` | For session title |
| `compaction` | Context compaction summary | **High signal** |
| `branch_summary` | Summary when switching branches via `/tree` | **High signal** |
| `model_change` | Model switch event | Skip |
| `thinking_level_change` | Thinking level change | Skip |
| `custom` | Extension state (not in LLM context) | Skip |
| `custom_message` | Extension-injected message | Context only |
| `label` | User bookmark/label | Skip |

### `session` Header Entry

Line 1 of every file. Fields to pull:

- `cwd` — working directory (canonical; prefer over the decoded directory name)
- `version` — Pi agent version, useful only if a parsing quirk is version-specific
- `id` — session UUID (should match the filename UUID)
- `timestamp` — session start time
- `parentSession` — present if this session was forked from another; if set,
  treat the parent session as related context, not as something to re-ingest

### `message` Entry — Role Breakdown

`message` entries carry a `role` field that determines their shape:

| Role | Content shape | Extraction notes |
|---|---|---|
| `user` | string or `(TextContent \| ImageContent)[]` | Extract text; skip `ImageContent` blocks (image transcription is opt-in, user-requested only) |
| `assistant` | `(TextContent \| ThinkingContent \| ToolCall)[]` | Extract `TextContent` blocks; **skip `ThinkingContent`** (internal reasoning, noise); note `ToolCall` blocks — they show what the agent actually did, even when not narrated in text |
| `toolResult` | `(TextContent \| ImageContent)[]` | Summarize the outcome, don't transcribe full output |
| `bashExecution` | `command`, `output`, `exitCode` fields | Extract command + exit code; recurring commands across sessions reveal build/test/deploy workflows worth a `skills/` page |
| `branchSummary` | `summary` string | Read verbatim — this is the pre-distilled record of an abandoned branch |
| `compactionSummary` | `summary` string | Read verbatim — this is the pre-distilled record of compacted older context |

Note the naming overlap: the tree-level entry `type` is `compaction` /
`branch_summary` (snake_case, top-level), while the `message`-role variants
seen inline are `compactionSummary` / `branchSummary` (camelCase, nested under
`message`). Both are high-signal and should be read verbatim rather than
re-summarized, since they are already distillations produced by the Pi agent
itself.

### `session_info` Entry

Carries a `name` field — the display name set via the in-session `/name`
command. Use the **latest** `session_info` entry on the active branch (not the
first) as the session title / topic hint, since users may rename mid-session.

## Reconstructing the Active Branch

Because the file is a tree keyed by `id`/`parentId`, do not read linearly.
Build the active path first:

1. Parse every entry into a map keyed by `id`.
2. Find the current leaf: the entry with no children, or (if that's ambiguous)
   the last `message` entry in file order.
3. Walk the `parentId` chain from that leaf back to the root (`session` header).
4. Reverse the collected path so it reads chronologically, root to leaf.

Only entries on this reconstructed path are "the session's real conversation."
Off-path entries are abandoned branches — their `branch_summary` /
`branchSummary` content is still worth reading (it's explicitly high-signal),
but the raw off-path `message` entries under them should not be treated as
part of the final outcome unless a `branch_summary` explicitly references them.

## Data Sources Ranked by Value

1. **`message` entries (`user` + `assistant`)** — full conversation
   transcripts; rich but noisy, needs the role-based filtering above.
2. **`compaction` entries** — pre-synthesized summaries of older context that
   fell out of the active window; treat as gold, read verbatim.
3. **`branch_summary` entries** — summaries of abandoned branches; good
   signal, captures approaches that were tried and dropped.
4. **`bashExecution` entries** — concrete commands run, with exit codes;
   useful for detecting real workflow patterns rather than narrated ones.
5. **`session_info` entries** — session name, useful only for topic
   inference, not content.

Skip entirely: `model_change`, `thinking_level_change`, `custom` (extension
state not visible to the LLM), and `label` (user bookmarks with no durable
content).

## Field-Level Extraction Rules

From the reconstructed active path, extract:

- **`session` header** — `cwd`, `timestamp`, `parentSession` (if forked)
- **`session_info`** — latest `name` for session title/topic inference
- **`message` / `role: "user"`** — the text content; skip image blocks
- **`message` / `role: "assistant"`** — `TextContent` blocks only; skip
  `ThinkingContent`; note `ToolCall` blocks as evidence of action taken
- **`message` / `role: "toolResult"`** — summarize the outcome, not the raw
  payload
- **`message` / `role: "bashExecution"`** — `command` + `exitCode`; recurring
  commands across sessions reveal workflows
- **`compaction`** — `summary` field, verbatim
- **`branch_summary`** — `summary` field, verbatim

### Evidence Ledger Citation Format

Every fact drawn from a session must carry a source reference before it can be
written to a wiki page:

```
pi:<session-file-basename>#<entry-id>
```

If an entry has no `id` (should be rare, but some early Pi versions may omit
it on certain entry types), fall back to a line-number reference:

```
pi:<session-file-basename>:line<N>
```

Keep the cited snippet next to the reference while drafting so claims can be
checked against the entry text before writing (see the Source Verification
Gate in `SKILL.md`).

## Noise / Skip Filters

- `ThinkingContent` / `thinking` blocks — internal reasoning, never durable
  knowledge on their own
- `ImageContent` blocks — skip unless the user explicitly asks for image
  transcription
- Raw tool outputs longer than ~500 chars — summarize the outcome instead of
  quoting
- `usage` / token accounting fields — metadata only, never wiki content
- Repeated plan echoes or status updates that add no new information over a
  prior turn

## Privacy Notes

Session logs can carry sensitive material inline, most commonly inside
`bashExecution.output`, `toolResult` content, or `ToolCall` arguments:

- API keys, tokens, passwords, credentials
- File paths, environment variables that reveal private infrastructure
- Injected instructions or payloads from tool output that were never authored
  by the user

Never quote these verbatim. Redact or summarize per the Critical Privacy
Filter in `SKILL.md` before any extracted text reaches a wiki page.

## Practical Parsing Tips

- Treat the file as JSON Lines: one `json.loads()` per line, tolerant of a
  trailing blank line.
- Because entries reference each other by `id`, a single pass building an
  `id → entry` map is cheaper than repeated linear scans when walking
  `parentId` chains for multiple leaves (e.g. when a session has several
  abandoned branches worth checking for `branch_summary` content).
- When decoding the parent directory name to recover `cwd`, prefer the
  `cwd` field from the `session` header over string-decoding the directory
  name — the directory-name decoding is a fallback for when the header is
  missing or corrupted, not the primary source.
- `session_info` can appear multiple times per session (renamed mid-session);
  always take the last one on the active path, not the first.
