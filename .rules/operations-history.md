# Operations history — resolved incidents and executed procedures

Moved verbatim from `operations.md` on 2026-09-24. A record, not operating guidance:
the standing rules live in `operations.md`, under the same section headers as below.

## `.manifest.json` loss & rebuild

Standing rule: operations.md §`.manifest.json` loss & rebuild

**Rebuild procedure** (done 2026-07-03, 132-file baseline):
- Scan every unchanged `.md` under the sources dir (exclude `.git/`,
  `attachments/`, and a root-level `INDEX.md`).
- For each, write the current `sha256` as `content_hash`.
- Backfill `ingested_at` uniformly to the last known ingest time (read from
  `log.md`), and mark each rebuilt entry `"backfilled": true` with a
  `backfill_note` explaining why. Add top-level `rebuilt_at` / `rebuild_reason`.
- Deliberately exclude that day's changed (delta) files — add their real entries
  only after the actual ingest completes.
- Sanity check: rebuilt count + same-day delta should equal an independent scan
  of in-scope files (132 + 6 = 138, cross-checked by a separate scan agent).

### 變體：部分條目遺失 → delta 報大量假 NEW（2026-07-16）

Instance, moved from the end of the variant (its rule text stays in operations.md):
實例：2026-07-16 USEN/Hexa 兩樹 20 檔（07-15 入庫、條目未落盤）。

## `.manifest.json` structure & jq recipes (verified 2026-07-08)

Standing rule: operations.md §`.manifest.json` structure & jq recipes (verified 2026-07-08) — condensed and updated there; the text below is the 2026-07-08 state.

Top level is `{version, last_updated, sources, projects, stats}`. `sources` is
an **object** keyed by absolute source path — NOT an array (a 2026-07-07 session
note claimed array with `.key` fields; jq-verified object on 2026-07-08).
Three **virtual keys** are not file paths: `conversation:<slug>` ×2 and
`inline:<slug>:<date>` ×1. Scripts that assume every key is a path must
special-case keys not starting with `/` — and never delete them as "missing".

jq pitfalls and working recipes:

- Top-level `to_entries | .[-1]` returns the last *top-level* key
  (`stats`/`last_updated`…), not the last source. `.sources[-1]` errors
  (can't index object with number). Also: the last sources entry is currently
  the `inline:...:2026-06-23` virtual key — its embedded date is the capture
  date, not evidence the manifest is stale.

```bash
jq -r '.sources | length' .manifest.json
jq -r '.sources | to_entries | .[-3:][] | "\(.key) | \(.value.ingested_at // "?")"' .manifest.json
jq -r '[.sources | to_entries[] | select(.value.ingested_at >= "2026-07-01")] | length' .manifest.json
jq -r '.sources | to_entries[] | select(.key | contains("<project-key>-18430"))' .manifest.json
```

## sources 路徑慣例：機器無關的 `~` 形式（owner 決策 2026-07-16）

Standing rule: operations.md §sources 路徑慣例：機器無關的 `~` 形式（owner 決策 2026-07-16）

Vault 在兩台機器間同步，home dir 不同（`/Users/<user>` 與 `/Users/<user-b>`），
兩台的來源目錄統一為 **`~/<workspace>/wiki-source`**。07-15 PM lint（work 機）曾發現
71 頁 sources「失聯」並提出單向 remap；07-16 於 <user> 機驗證失聯與否取決於
機器 → owner 拍板改用 `~` 形式，2026-07-16 已全面執行：

- **已執行的 remap（backup：`~/.claude/backups/2026-07-16-sources-remap/`）**：
  vault 76 檔 311 處＋manifest 231 key 全改 `~` 形式（log.md 除外——歷史紀錄
  不改寫）；<user> 機 `~/<workspace>/wiki_source` 已 rename 為 `wiki-source`＋留同名
  相容 symlink（外部工具沿舊路徑仍可用）；`.env` 的 `OBSIDIAN_SOURCES_DIR`
  已指向新路徑（`.env` gitignored、每機一份）。

## wiki_source 2026-07 reorg drift — resolved 2026-07-08

Standing rule: operations.md §wiki-source standing rules (from the 2026-07 reorg)

Background: flat `<project-key>-*_slug.md` exports were moved/consolidated into epic
folders (e.g. `<project-key>-17584 RwG Add-Ons Payment & Revamp/`), leaving ~72 stale
manifest keys; ~855 `attachments/` images are policy-excluded from ingest and
must be excluded from delta scans or they all read as NEW.

2026-07-08 cleanup (backup: `<vault>/.manifest.json.bak-20260708`):

- **25 duplicate old keys deleted** — same ticket re-tracked under a new path.
- **44 deleted sub-ticket exports annotated `source_removed: true`** (with
  `removed_note`) instead of deleted — keeps ingest provenance, and delta
  scripts skip them so the MISSING pile doesn't need re-interpreting each run.
- **3 virtual keys kept** untouched.
- Manifest went 225 → 200 entries; `stats` counters left as historical.

Duplicate `<project-key>-18430.md` exists at wiki_source root AND inside the RwG
folder, both tracked. Which copy is fresher flips between syncs (07-07: folder
newer; 07-08: root newer — root is where uncommitted Jira syncs land ^[inferred]).
Don't assume; compare mtime/hash per run and ingest the changed one.
