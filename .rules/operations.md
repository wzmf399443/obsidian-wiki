# Operational Gotchas — CLI, manifest & repo structure

Hard-won operational knowledge for running this tooling against a real vault:
how to invoke the CLI, how to detect the ingest delta when the tracking
manifest can't be trusted, plus repo-structure / lint / ingest-dispatch
gotchas distilled from `.rules/lessons.md`. Read this before an ingest run,
before computing a delta by hand, or before touching `.manifest.json`.

> Scope: this is about operating the obsidian-wiki *tooling*, not knowledge that
> belongs in a vault. It lives here (the tool repo's `.rules/`), not in a vault
> `skills/` page — see the `skills/` guardrail in `.skills/llm-wiki/SKILL.md`.

## Mixed-vault scope (<private-dir>/ <private-dir>/)

`<private-dir>/` and `<private-dir>/` are the owner's private notes: never read, edit, cite or scan them (vault `CLAUDE.md` `## Scope`). The whitelist is `TRUST_CONTENT_DIRS` in `obsidian_wiki/trust.py` (concepts entities skills references synthesis journal projects misc) plus root special files. This scope bug has recurred in six carriers (tool, agent, lint script, exclude flag, bare grep, root glob), each time silently.

- **Whitelist + post-check, in any environment (08-17)**: build `scope.txt` with `find <vault> \( -path '*/<company>' -o -path '*/<private-dir>' \) -prune -o -name '*.md' -print` (rebuild it after new pages are created) and search it with `/usr/bin/grep -n PAT $(< scope.txt)`; `--exclude-dir=<company> --exclude-dir=<private-dir>` is never the only defense — whatever the method, a result counts only after `grep -c` of the output for <company>/<private-dir> paths returns 0.
- **Bare `grep` is a wrapper (09-23)**: in the claude-work shell `grep` is a shell function that runs the Claude binary as ugrep (`type grep`), so use `/usr/bin/grep`, and dispatch prompts say "bare grep is a wrapper — don't rely on it".
- **No root glob (09-23)**: never `*`/`**` at the vault root (`ls */x.md` expands into <private-dir>/ and <private-dir>/); find files only via `scope.txt` or the listed content dirs (`concepts entities skills references synthesis journal projects`, plus `misc` if it exists). Every producer, verifier and lint prompt carries this sentence (to-do: add it to the vault `CLAUDE.md` `## Scope`).
- **Exclude first, never scan-then-filter (08-05)**: if you need something inside <private-dir>/ or <private-dir>/, ask the owner to paste it; if unsure whether a dir is in scope, ask first (to-do: bake the whitelist into the skills' example grep commands).
- **Scope-check every new carrier (07-29, 08-12)**: before a tool with "whole-vault" semantics or a new vault-scanning script runs on this vault, grep its include/exclude list against the whitelist (include ⊆ content dirs + special files, or exclude ⊇ <company>, <private-dir>); when a lint suite is reused, "all scripts agree on scope" is a runner acceptance item.

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

**Rebuild the tracking baseline:**
- scan every unchanged `.md` under the sources dir (exclude `.git/`, `attachments/`, a root-level `INDEX.md`) and write each file's current `sha256` as `content_hash`; backfill `ingested_at` uniformly to the last known ingest time (read from `log.md`); mark each rebuilt entry `"backfilled": true` with a `backfill_note` explaining why; add top-level `rebuilt_at` / `rebuild_reason`;
- exclude that day's changed (delta) files — add their real entries only after the actual ingest completes;
- sanity check: rebuilt count + same-day delta should equal an independent scan of in-scope files (cross-checked by a separate scan agent).

### 變體：部分條目遺失 → delta 報大量假 NEW（2026-07-16）

回滾事故後 manifest 可能只缺「某幾次 ingest 的條目」而非整份遺失：manual_delta
會把那些已入庫的 source 全報成 NEW。看到成批 NEW 時先別 ingest，查三個訊號：
① `log.md` 有無涵蓋這些檔案的 INGEST 條目（含頁面清單）；② 對應 vault 頁面
是否齊備；③ 各檔 `fetched_at` 是否早於該次 ingest 時間、內容是否與 git HEAD
一致（即入庫後未再變）。三者皆成立 → **backfill 條目（標 `backfilled` +
`backfill_note`，pages 批次層級歸屬），不重新 ingest**；補完跑 manual_delta
複核歸零。

History: operations-history.md §`.manifest.json` loss & rebuild

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

**Is a `modified` source a real delta? (09-01, 09-02, 09-04, 09-23)** Judge by the source header `jira_updated_max`, not by git or by comment-heading timestamps:
- `jira_updated_max` later than the last `ingested_at` ⇒ substantive-change candidate — never classify it fetched_at-only because no new `### name — time` heading appeared (editing a Jira comment keeps its created timestamp; that is how QA backfills like PENDING→PASS and revised decisions arrive).
- Cheapest proof first: revert the exporter header fields (`fetched_at`, `jira_updated_max`) to the previous values and re-hash — equal to the manifest `content_hash` ⇒ content unchanged: SKIP, with that proof in `skip_note` — status spot-check still required (cheap insurance: it catches a status word the previous run missed). Otherwise diff against the previous version (`sources_snapshot/`, keep one per run; to-do: jira-ingest committing after each fetch would allow `git diff`), or compare section by section against the page's claims (QA result tables, PENDING/待確認 markers, Design Decisions).
- For a hash-changed source (header-reverted re-hash ≠ `content_hash`), SKIP only if its owning page's `created`/last substantive `updated` ≥ the source's `jira_updated_max` AND a spot-check that includes the status word matches; any status difference is a substantive delta (→ compare section by section), and every dispatch prompt's spot-check has a "status matches" item.

## obsidian-wiki CLI gotchas

### The CLI is not global — call `.venv/bin/obsidian-wiki` directly (verified 2026-09-24)

The package is installed only in the project venv at
`/Users/<user>/<workspace>/obsidian-wiki/.venv` (uv-managed), not globally. Calling
`obsidian-wiki graph-query ...` bare returns `command not found`, and since
2026-09-02 `uv run obsidian-wiki` fails at dependency resolution (`No solution
found`: the project declares `requires-python>=3.9`, but the `server` extra's
`mcp>=2.0` needs Python >=3.10). Call the venv binary by absolute path, and
hardcode that path in dispatch prompts:

```bash
/Users/<user>/<workspace>/obsidian-wiki/.venv/bin/obsidian-wiki graph-query <vault_path> "<question>" --pretty
```

A `uv run` failure is environmental: don't retry it, don't conclude "CLI not
installed", and never run `uv sync` to repair it (re-resolving could alter the
working venv). Root-fix candidate (upstream PR): `requires-python>=3.10`, or keep
`mcp` in a non-default optional extra.

It prints a warning — `... is installed but setup has never been run. Run:
obsidian-wiki setup --vault ...` — which is harmless for `graph-query`
(`candidates`/`should_read`/`index_only` still return normally). To silence it
and make the command global, run `.venv/bin/obsidian-wiki setup --vault <vault_path>`
once, or `pip install obsidian-wiki` globally.

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
- **`--json` stdout isn't clean (08-06)**: the setup warning is printed on stdout before the JSON, so parse from the first `{` (`raw[raw.index('{'):]`) for every `--json`; pass many `--page` args via xargs (`sed 's/^/--page /' pages.txt | xargs /Users/<user>/<workspace>/obsidian-wiki/.venv/bin/obsidian-wiki trust-record <vault> … --json > out.txt 2>&1`), never via a shell-variable expansion.
- **graph-query 0 hits on Chinese terms ≠ no page (08-14)**: never conclude "no existing page" from it; before creating a page, re-check with a scoped vault grep (§Mixed-vault scope) by keyword AND ticket ID.
- **Subprocess CLI tests pin `cwd`, not only `HOME` (07-30)**: config resolution walks up from cwd to a `.env`, so the repo-root `.env` leaks the real vault into tests; `run_cli()` in `tests/test_context_pack_cli.py` defaults cwd to the fake HOME since ea1633a (#174) — for any test that doesn't pin cwd, run pytest from a directory without `.env`.
- Queued 2026-07-29 (status not re-checked): 4 pages lost their sources in the 07-06 reorg (rwg-order-routing, rwg-data-correction-tools, rwg-addons-launch-plan, partner-api-sevenrooms-compat) — re-pull them, then `trust-record --page` each.

## `.manifest.json` structure & jq recipes (verified 2026-07-08)

Top level is `{version, last_updated, sources, projects, stats}`. `sources` is an **object** (NOT an array) keyed by source path — `~` form since 2026-07-16 (§sources 路徑慣例).
**Virtual keys** — keys not starting with `/` or `~` (`conversation:*`, `inline:*`; 13 as of 2026-09-23) — are not file paths: scripts that assume every key is a path must special-case them, and never delete them as "missing". `source_removed: true` entries are excluded from missing counts.

jq pitfalls: top-level `to_entries | .[-1]` returns the last *top-level* key (`stats`/`last_updated`…), not the last source; `.sources[-1]` errors (can't index object with number). An `inline:<slug>:<date>` key's date is its capture date, not evidence the manifest is stale.

History: operations-history.md §`.manifest.json` structure & jq recipes (verified 2026-07-08)

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

Vault 在兩台機器間同步、home dir 不同（`/Users/<user>` 與 `/Users/<user-b>`），絕對路徑是否「失聯」取決於機器；兩台的來源目錄統一為 **`~/<workspace>/wiki-source`**：

- **寫入慣例（強制）**：wiki 頁 `sources:` 與 `.manifest.json` key 一律寫
  `~/<workspace>/wiki-source/...`（其他本機路徑同理用 `~` 前綴，如
  `~/<workspace>/AI/cursor/<company>-go/...`）。不得寫 `/Users/<user>/...` 絕對路徑，
  也不得照抄舊頁面/舊 manifest 的絕對路徑慣例。
- **消費端**：任何讀這些路徑的 script 必須 `os.path.expanduser()`；
  `manual_delta.py` 已改（含 virtual-key 判斷：非 `/` 且非 `~` 開頭才算 virtual）。
- **相容與例外**：<user> 機的舊路徑 `~/<workspace>/wiki_source` 保留為指向 `wiki-source` 的相容 symlink（外部工具沿舊路徑仍可用）；`.env`（含 `OBSIDIAN_SOURCES_DIR`）gitignored、每機一份；`log.md` 內的舊絕對路徑不改寫（歷史紀錄）。
- **待查（work 機）**：07-15 lint 在 work 機報 14 條 remap MISS，但 07-16 在
  <user> 機逐條檢查 0 miss — 推測 work 機的 wiki-source 少了部分檔案
  （兩機 sources 同步 drift）^[inferred]。下次在 work 機 session 時複核。

History: operations-history.md §sources 路徑慣例：機器無關的 `~` 形式（owner 決策 2026-07-16）

## wiki-source standing rules (from the 2026-07 reorg): attachments/, removed exports, 18430 duplicate

- **`attachments/` excluded**: the ~855 `attachments/` images are policy-excluded from ingest and must also be excluded from delta scans, or they all read as NEW.
- **Removed exports: annotate, never delete the key**: a deleted source export keeps its manifest key, annotated `source_removed: true` + `removed_note` (keeps ingest provenance; delta scripts skip these, so the MISSING pile doesn't need re-interpreting each run). A duplicate old key (same ticket re-tracked under a new path) is a different case — the 07-08 cleanup deleted those.
- **Per-run duplicate check**: `<project-key>-18430.md` exists at the wiki-source root AND in `<project-key>-17584 RwG Add-Ons Payment & Revamp/` (both still present and both tracked — manifest key + git — verified 2026-09-24). Which copy is fresher flips between syncs — don't assume; compare mtime/hash each run and ingest the changed one.

History: operations-history.md §wiki_source 2026-07 reorg drift — resolved 2026-07-08

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

### Reusable scripts live in `scripts/`; hard errors don't stay report-only (2026-08-31)

Move any script declared "always reuse" into `scripts/` on the spot (`output/<run>/scripts/` and scratchpads evaporate). A report-only lint that finds a hard error (e.g. a YAML parse failure that drops a page from the statistics) fixes it on the spot or files it as an explicit to-do — "logged" is not "handled" — and the next ingest/lint first re-checks the hard errors the previous log.md named (one grep).

## Shell / grep / git gotchas (all fail silently)

- **Zero needs a positive control in the same dimension (08-31, 09-01, 09-15, 09-16/17)**: before trusting 0 hits / 0 stale / 0 writes / an empty diff, run a control that must hit in that same dimension — a deliberately wrong current status for a status sweep, a known old wording for an overturned-claim grep, a known `path:line:` entry for a list compare (must give ≥1), a version known to differ for a git pathspec ("the command runs" is not a control); write the self-check and its control command into the script or dispatch prompt rather than leaving them to the executor, and never add `2>/dev/null` to these checks (it hides the only clue).
- **zsh does no word splitting on unquoted `$VAR` (08-31, 09-04)**: a multi-path string in a variable becomes one nonexistent path, so write the paths on the command line or expand with `${D[@]}` / `${=D}` — for every script argument too (e.g. `verify_mechanical.py --new`).
- **BRE vs ERE braces (09-01)**: widen spacing with `.\{0,N\}` in plain grep (BRE) but `.{0,N}` in `grep -E` (ERE), where `\{` is a literal brace; if unsure, use plain grep.
- **git diff is blind to untracked files (09-01)**: run `git ls-files --error-unmatch <path>` before reading an empty `git diff` as "unchanged"; for source changes prefer the header `jira_updated_max` (§Delta detection).
- **`find -newermt` parses its string as local time (09-15)**: a UTC string moves the cutoff 8 h early on this machine, so record `date -u > start_time.txt` at the start and use `find -newer start_time.txt`; if `-newermt` is unavoidable, convert to local time and state the tz in the report (earlier `-newermt` self-proofs fed UTC strings — treat them as 8 h weaker).

## Lint & ingest-dispatch gotchas

Multi-batch ingest coordinator checklist → `.rules/templates-ingest-coordination.md` (T6).

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

**歸屬判準（09-21、09-23）**：grep 命中只是候選——owned 頁一律由 `sources:` 區塊決定（逐行解析該 key 到下一個頂層 key，不用 DOTALL），且 entry 的 basename 必須 `== <ticket>.md`（子票路徑的資料夾名含 epic 票號，子字串比對會把頁算給 epic；只在資料夾名出現者另列 `via_folder`）。命中但不在 `sources:` 的頁列為 mention-only，派工 prompt 另立一段「這些你不擁有，要改走 CROSS-BATCH」；共頁（同一頁被多票列為來源）的票歸同一個 agent——這是決定批次切法的主要依據。

### Vault 頁面 git untracked——沒有頁面級回滾（2026-07-16）

<vault> 雖在 git repo 內，但日常變更全 untracked，`git checkout` 無法回到
session 前狀態；vault 靠跨機同步而非 git。①派工 REPORT 要求 subagent 引述
被改動句原文，事後才有回滾依據（見 delegation.md §4）；②「重來」的可行語義
是逐頁重審重寫，不是字面 revert；③高風險批次改動前比照 manifest 慣例先
`cp` 頁面級備份。^[inferred]

### Closing verifiers, provenance & YAML (2026-07-20 … 09-23)

- **Provenance block = marker density (07-20, 07-23)**: fix check-7 drift by recomputing the block from the markers with check-7's `split_claims` logic (usually lowering the declared value; e.g. `output/lint-2026-07-20/scripts/fix_provenance.py`), never by adding markers — frontmatter + bump `updated` only, body untouched, then re-run check-7 → 0. Non-standard markers (e.g. `^[extracted]`): vault-wide grep count first, then one batch clean (strip + recompute, backup first), done only when a re-grep returns 0 and every page's YAML parses. (To-do: wiki-synthesize still writes a semantic guess instead of marker density.)
- **Closing verifier scripts (08-27)**: reuse `scripts/verify_mechanical.py`; parse indented YAML blocks line by line (its `fm_block()`), never with a regex repeat group + `\s*`; strip fenced blocks and inline code spans before wikilink scans (bash `[[ ]]`, `$(...)`); length limits (summary ≤200) hold only via a script `len()` assert; if the first run reports abnormally many issues, test the verifier on 1–2 of them before touching pages. (To-do: it lacks the key-set-vs-backup and body-unchanged checks — run-dir scripts do those.)
- **YAML parse failure is a hard error (08-27)**: a page whose frontmatter fails `yaml.safe_load` silently drops out of every YAML-based check (while `trust.py`'s line parser still passes it as clean), so report it first as its own category (not a check-3 "missing field"), and give every "N pages hit" with its check's denominator — a denominator below the page count means pages were silently excluded. (To-do: lint check-3 and `trust.py` lack this smoke check; verify_mechanical C0 has it.)
- **Image links resolve from the source's folder (09-23)**: resolve `![](attachments/…)` against `dirname(<source file>)` first, then the wiki-source root, and only then mark it NOT FOUND and report it.
