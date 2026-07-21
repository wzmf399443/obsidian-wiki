# Lessons Log

Hard-won corrections from real sessions. Append-only during a session; distilled
per `.rules/maintenance.md` when >100 lines. Format: see maintenance.md.

<!-- Distilled 2026-07-18 (backup: lessons.md.bak-20260718). All entries through
2026-07-16 were folded or retired:
- already encoded, deleted: 07-03 symlink (AGENTS.md header), 07-03 no-effort-param
  (delegation.md §2), 07-07 skills/ misfile (three SKILL.md files), 07-14 check9c
  (lint script fixed).
- folded into operations.md: 07-14 five-agent-dir symlinks, 07-14 scratchpad
  artifacts, 07-16 classifier-outage Monitor backoff, 07-16 lint check-4 mtime
  low-signal, 07-16 ticket→page mapping grep, 07-16 vault git-untracked rollback.
- folded into delegation.md: 07-03 stale injected CLAUDE.md (§3), quote-original
  report requirement (§4). -->

## 2026-07-20 — synthesize 產出的頁面 provenance block 系統性高報 → check-7 drift
- Situation: 07-20 lint 對 07-18 synthesize 落地的 5 頁（hexa-sync-lifecycle、rwg-category-schema、billing-snapshot-reconstruction、login-unification-patterns、inline-sync-loop-protection）全部報 provenance drift（宣告 inferred 0.70–0.75，marker 重算 0.26–0.35，drift 0.37–0.55）。
- Mistake/surprise: 我第一直覺是「補 `^[inferred]` marker 把重算拉到 0.70，絕不降宣告值」——**讀了頁面後證明錯了**。llm-wiki 明定 provenance block =「有 marker 的 bullet/句子的粗略比例，wiki-lint 由 marker 重算並報 drift」，即 block 本來就該等於 marker 密度、不是語意自評。實讀 hexa 頁：真正的合成推論句**早已全部標好 `^[inferred]`**（27 claim-lines 中 7 個），重算 0.26 偏低純粹因為分母含了 Related 連結清單、還原來源立場的 warning 區塊、Open Questions 等結構行。要湊到 0.70 只能對非推論行亂標 marker（造假）。synthesize skill 寫的 0.70 是語意猜測、非 marker 密度，這才是 drift 真因。
- Rule: synthesis/ 頁 provenance drift 的正解是**把 block 重算對齊實際 marker 密度（通常是降宣告值）**，不是補假 marker。可直接用 check7 的 split_claims 邏輯確定性重寫三個值（腳本：output/lint-2026-07-20/scripts/fix_provenance.py）——同一批 web-hsts drift 也是這樣一起修。只改 frontmatter＋bump updated，body 不動；修後 re-run check7 應歸零。根治：修 synthesize skill 讓它輸出 marker 密度而非語意猜測。
- Applies to: 折入 operations.md「Lint & ingest-dispatch gotchas」或 wiki-synthesize skill（provenance block 輸出邏輯）。

## 2026-07-21 — subagent 書記時戳寫成未來時間 → mtime 對賬 warn
- Situation: ingest subagent 寫 log.md 條目與 hot.md updated 時自行「估」了時戳（03:45Z/03:50Z），實際落盤 03:39/03:40Z——檔內宣稱時間晚於 mtime，verifier mtime 對賬（operations.md）判 warn，多跑一輪修正。
- Mistake/surprise: 派工 prompt 只說「TIMESTAMP」，subagent 便用推算值而非實際時間；未來時戳會讓 mtime 對賬的「mtime ≥ 宣稱時間」不變式失效。
- Rule: 派工 prompt 要求 bookkeeping 時戳一律取自實跑 `date -u +%Y-%m-%dT%H:%M:%SZ`（或沿用 manifest ingested_at 同一值），不得估寫；verifier 檢查項保留「宣稱時戳 ≤ 檔案 mtime」。
- Applies to: templates.md T2（bookkeeping 行）或 operations.md「mtime 對賬 audit」。
