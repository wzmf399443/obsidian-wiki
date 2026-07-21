# Operational Gotchas — CLI, manifest & repo structure

Hard-won operational knowledge for running this tooling against a real vault:
how to invoke the CLI, how to detect the ingest delta when the tracking
manifest can't be trusted, plus repo-structure / lint / ingest-dispatch
gotchas distilled from `.rules/lessons.md`. Read this before an ingest run,
before computing a delta by hand, or before touching `.manifest.json`.

> Scope: this is about operating the obsidian-wiki *tooling*, not knowledge that
> belongs in a vault. It lives here (the tool repo's `.rules/`), not in a vault
> `skills/` page — see the `skills/` guardrail in `.skills/llm-wiki/SKILL.md`.

## `.manifest.json` loss & rebuild

**Symptom.** The vault's `.manifest.json` is missing entirely, yet `log.md` has
many INGEST entries claiming "manifest N files hash-updated" — a contradiction.
Cause is usually a machine/path migration that didn't carry the manifest along
(e.g. sources moved from `/Users/<user>/<workspace>/wiki_source/...` to a new path;
old pages' `sources:` fields still point at the old location).

**Don't treat "manifest missing" as "Full Mode / re-ingest everything."** For a
vault that is already complete and only lost its tracking file, a full re-ingest
re-distills every page and causes massive duplicate churn. The right move is to
rebuild the tracking baseline, then ingest only the true delta.

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

回滾事故後 manifest 可能只缺「某幾次 ingest 的條目」而非整份遺失：manual_delta
會把那些已入庫的 source 全報成 NEW。看到成批 NEW 時先別 ingest，查三個訊號：
① `log.md` 有無涵蓋這些檔案的 INGEST 條目（含頁面清單）；② 對應 vault 頁面
是否齊備；③ 各檔 `fetched_at` 是否早於該次 ingest 時間、內容是否與 git HEAD
一致（即入庫後未再變）。三者皆成立 → **backfill 條目（標 `backfilled` +
`backfill_note`，pages 批次層級歸屬），不重新 ingest**；補完跑 manual_delta
複核歸零。實例：2026-07-16 USEN/Hexa 兩樹 20 檔（07-15 入庫、條目未落盤）。

## Delta detection without a manifest

When the manifest is gone or untrustworthy, two independent signals reconstruct
the delta — no full re-read needed:

1. **`log.md` mtime = last ingest end time.** Every ingest writes `log.md` last,
   so `find <sources> -name '*.md' -newer <vault>/log.md` lists sources changed
   since the last ingest.
2. **Source-repo git diff.** If the sources dir is a git repo,
   `git diff <last-commit-before-ingest> HEAD` gives exact content-level changes;
   feed that to the ingest subagent so it distills only new content instead of
   re-reading whole sources and diffing against wiki pages.

**Precondition.** `hot.md`/`log.md` must hold a trustworthy last-ingest time, and
source mtimes must not have been clobbered by a checkout/copy (cross-check that
mtimes line up with the source repo's commit times).

## obsidian-wiki CLI gotchas

### The CLI is not global — invoke via `uv run`

The package is installed only in the project venv at
`/Users/<user>/<workspace>/obsidian-wiki/.venv` (uv-managed), not globally. Calling
`obsidian-wiki graph-query ...` bare returns `command not found`. From the
project dir, use:

```bash
uv run obsidian-wiki graph-query <vault_path> "<question>" --pretty
```

It prints a warning — `... is installed but setup has never been run. Run:
obsidian-wiki setup --vault ...` — which is harmless for `graph-query`
(`candidates`/`should_read`/`index_only` still return normally). To silence it
and make the command global, run `obsidian-wiki setup --vault <vault_path>` once,
or `pip install obsidian-wiki` globally.

### `cache-check` / `batch-plan` falsely report everything modified

Observed 2026-07-06: `uv run obsidian-wiki batch-plan <vault> <sources>` reported
`to_ingest: 1007, skipped_unchanged: 0`, and `cache-check` flagged even
long-untouched files as `modified`. Direct check: the manifest `content_hash`
matched the on-disk sha256 exactly — the comparison logic is broken, not the
manifest. Possibly related to setup never having run. ^[inferred]

**Impact.** Trusting `batch-plan` would re-ingest ~131 unchanged sources (a large
subagent fan-out) — the same wrong prescription as the manifest-loss case above.

**Fallback: manual sha256 compare (verified).** Walk each source file
(`python os.walk`, exclude `.git`/`.claude`/`.serena`, keep only `.md`/`.txt`,
drop root-level `INDEX.md`), compute `sha256:<hex>`, compare against
`.manifest.json`'s `content_hash`, and bucket into new/modified/unchanged.
The 2026-07-06 run gave unchanged 131, modified 6, new 0 — cross-verified against
file mtimes.

### Operating rules

- Before an ingest, spot-check one file's hash by hand. If `cache-check`
  disagrees with the manual check, switch the whole run to a manual delta and
  don't trust the CLI output.
- **The manual delta is now a script: `scripts/manual_delta.py`** (promoted
  2026-07-08 after the third hand-rolled run). It knows the real manifest
  layout, virtual keys, and `source_removed` annotations — use it instead of
  rewriting the walk.
- To-do: fix the CLI comparison logic, or run `obsidian-wiki setup` to rule out
  the never-set-up variable and retest. ^[inferred]

## `.manifest.json` structure & jq recipes (verified 2026-07-08)

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

### mtime 對賬 audit（5 秒查 bookkeeping 落盤）

`ls -la $VAULT/log.md $VAULT/hot.md $VAULT/index.md $VAULT/.manifest.json` —
expectations: `log.md` mtime ≥ its last entry's timestamp; `index.md` mtime ≥
last LINT_FIX/INGEST end; `.manifest.json` mtime ≥ last INGEST/REBUILD end;
`hot.md` only moves on deliberate updates (a lag of hours can be normal).
Signal: log claims a write but the target file's mtime predates the entry →
the write never landed.

## git diff delta：先驗證 HEAD==manifest，否則 diff 是 superset（2026-07-09）

「用 source repo 的 `git diff HEAD -- <file>` 當精準 ingest delta」有一個前提：
上次 ingest 時的檔案內容必須等於現在的 HEAD blob。若上次 ingest 吃的是
**未 commit 的 working tree 狀態**（常態——Jira sync 直接落地未即 commit），
之後才 commit/merge，則 diff-vs-HEAD 會包含已入庫內容，是 **superset** 而非
精準 delta，直接餵給 subagent 會重複合併舊知識。

**每檔一行檢查**（2026-07-09 實測：同一批 4 檔中 2 exact、2 superset）：

```bash
git show "HEAD:$f" | shasum -a 256   # 對比 manifest 該 key 的 content_hash
```

- 相等 → `git diff HEAD -- $f` 就是精準新內容，直接餵。
- 不等 → diff 是 superset；派工 prompt 必須明講「部分內容已入庫，先對照
  現有 wiki 頁去重，只合併真正新的 claims」，並點名已入庫的部分。

**Fallback：manifest hash 在 git 歷史找不到任何 blob（2026-07-13 實測）。**
逐 commit `git show <c>:$f | shasum` 全不吻合時（上次 ingest 吃的 working-tree
狀態從未被 commit），改用**另一份 tracked、hash 與 manifest 吻合且已完整入庫的
副本**（18430 的 root copy）當 diff 基準——雙副本檔案（見下節 reorg drift）天然
提供這個備援。所得 diff 仍照 superset 協議處理；主對話可先自己看 diff：若實質
delta 極小（本例 83 行中僅 2 點新知識），直接把事實寫進派工 prompt，
subagent 連 source 都不必重讀。

## sources 路徑慣例：機器無關的 `~` 形式（owner 決策 2026-07-16）

Vault 在兩台機器間同步，home dir 不同（`/Users/<user>` 與 `/Users/<user-b>`），
兩台的來源目錄統一為 **`~/<workspace>/wiki-source`**。07-15 PM lint（work 機）曾發現
71 頁 sources「失聯」並提出單向 remap；07-16 於 <user> 機驗證失聯與否取決於
機器 → owner 拍板改用 `~` 形式，2026-07-16 已全面執行：

- **寫入慣例（強制）**：wiki 頁 `sources:` 與 `.manifest.json` key 一律寫
  `~/<workspace>/wiki-source/...`（其他本機路徑同理用 `~` 前綴，如
  `~/<workspace>/AI/cursor/<company>-go/...`）。不得寫 `/Users/<user>/...` 絕對路徑，
  也不得照抄舊頁面/舊 manifest 的絕對路徑慣例。
- **消費端**：任何讀這些路徑的 script 必須 `os.path.expanduser()`；
  `manual_delta.py` 已改（含 virtual-key 判斷：非 `/` 且非 `~` 開頭才算 virtual）。
- **已執行的 remap（backup：`~/.claude/backups/2026-07-16-sources-remap/`）**：
  vault 76 檔 311 處＋manifest 231 key 全改 `~` 形式（log.md 除外——歷史紀錄
  不改寫）；<user> 機 `~/<workspace>/wiki_source` 已 rename 為 `wiki-source`＋留同名
  相容 symlink（外部工具沿舊路徑仍可用）；`.env` 的 `OBSIDIAN_SOURCES_DIR`
  已指向新路徑（`.env` gitignored、每機一份）。
- **待查（work 機）**：07-15 lint 在 work 機報 14 條 remap MISS，但 07-16 在
  <user> 機逐條檢查 0 miss — 推測 work 機的 wiki-source 少了部分檔案
  （兩機 sources 同步 drift）^[inferred]。下次在 work 機 session 時複核。

## wiki_source 2026-07 reorg drift — resolved 2026-07-08

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

## Repo structure & session artifacts

### New skills need symlinks in all five agent dirs (2026-07-14)

This repo's `.skills/` is symlinked identically into `.agents/`, `.claude/`,
`.cursor/`, `.kiro/`, `.windsurf/` — adding a skill only under `.claude/` leaves
the other four agent harnesses blind to it. When adding/renaming a skill,
add/update the symlink in all five dirs; verify with
`ls -la .agents .claude .cursor .kiro .windsurf | grep <skill>`.

### Old sessions' scratchpads keep scan artifacts (2026-07-14)

After a /clear, before re-running an expensive scan, check sibling session
scratchpads for its artifacts:
`/private/tmp/claude-501/<project-slug>/<session-id>/scratchpad/` (e.g.
`wiki_lint_structural_findings.json`). Corollary: always write lint reports to
`output/` — scratchpads are tmp and won't survive reboot.

### Safety classifier outage: Monitor works as a wait timer (2026-07-16)

When the harness safety classifier goes down, every Bash AND Agent dispatch
errors "temporarily unavailable" while read-only tools keep working. Do
read-only prep first, then wait via Monitor timers with escalating backoff
(90s → 5min → 10min), probing with a trivial `echo` Bash call before
re-dispatching the full subagent fan-out.

## Lint & ingest-dispatch gotchas

### Lint check 4 (stale vs sources) is low-signal on this vault (2026-07-16)

Jira re-sync re-downloads source files, bumping mtime even when content is
already ingested — mtime-based staleness systematically over-reports (07-16:
64 pages flagged vs a same-day all-clean manifest hash delta). Staleness
verdicts come from the manifest hash delta (`scripts/manual_delta.py`), not
file mtimes; report check-4 mtime findings only with that caveat, and never
trigger re-ingest from them alone.

### Ingest 派工前必須逐票 grep 驗證 ticket→page mapping（2026-07-16）

派工 prompt 寫死 ticket→page mapping 前，逐票
`grep -l "<ticket>" $VAULT/{concepts,references}/*.md` 驗證；票數≠頁數必有
共頁或缺頁（實例：18313/18368 兩票共一頁，按位置配對整體錯位）。Prompt 保留
「目標頁不符描述就 SKIP 並回報」逃生口——07-16 事故靠它揪錯。

### Vault 頁面 git untracked——沒有頁面級回滾（2026-07-16）

<vault> 雖在 git repo 內，但日常變更全 untracked，`git checkout` 無法回到
session 前狀態；vault 靠跨機同步而非 git。①派工 REPORT 要求 subagent 引述
被改動句原文，事後才有回滾依據（見 delegation.md §4）；②「重來」的可行語義
是逐頁重審重寫，不是字面 revert；③高風險批次改動前比照 manifest 慣例先
`cp` 頁面級備份。^[inferred]
