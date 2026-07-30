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

## 2026-07-24 — 使用者中斷 ingest subagent → 頁面已寫、書記未做的半完成狀態
- Situation: 第一次派工（sonnet）被使用者中斷改派 fable；中斷時該 agent 其實已寫完 7 頁（統一 `updated: 02:52:59Z`），但 manifest/log/hot/index 全未動。重派的 fable agent 自行識別出此狀態，逐 claim 驗證覆蓋而非重合併，避免了 duplicate section。
- Mistake/surprise: 中斷 ≠ 未執行——subagent 被 kill 前的寫入已落盤。若重派 prompt 假設「從零開始」，agent 很可能對已含內容的頁面再 append 一次（duplicate-section 失效模式）。偵測訊號：目標頁 `updated` 時戳統一且新於 log.md 最後條目、manifest hash 落後於磁碟。
- Rule: 重派任何被中斷的寫入型任務前（或在重派 prompt 中）明寫：「前一次 run 可能已部分寫入——先檢查目標頁是否已含 delta 內容；已含則驗證覆蓋並只補書記，不得重合併」。驗證端（T5）對應加 duplicate-section 檢查項。
- Applies to: templates.md T2/T5、operations.md「Lint & ingest-dispatch gotchas」。

## 2026-07-23 — ingest subagent 自發使用非標準 ^[extracted] marker，蔓延至 55 頁
- Situation: 07-22/23 ingest 驗收發現本次批次又新增多處 `^[extracted]`；全 vault 掃描共 55 頁 205 處（07-15 首見時僅 37 頁，放任兩週擴散）。
- Mistake/surprise: 規範只有 `^[inferred]`/`^[ambiguous]`（extracted=無標記），但派工 prompt 只寫「推論句標 marker」，多個 fable subagent 自行對稱地補了 `^[extracted]`；lint check-7 以 marker 密度重算 provenance 時會誤計，造成假 drift（07-20 教訓的反向版本）。
- Rule: ①派工 prompt 的 provenance 段落須明寫「不得使用 ^[extracted]」（wiki-ingest SKILL.md:425 已補）；②發現非標準 marker 不要單頁修，先全 vault grep 統計再批次清（scripts 模式：scratchpad strip_extracted.py——剝 marker＋check-7 同口徑重算 provenance＋備份，2026-07-23 實跑 55 頁 0 殘留 0 YAML 損壞）；③清完 re-grep 歸零＋YAML parse 全過才算完。
- Applies to: operations.md「Lint & ingest-dispatch gotchas」；templates.md T2 CONSTRAINTS 行。

## 2026-07-29 — trust-record/check 掃全 vault rglob，混合 vault 永遠 error
- Situation: 建 trust ledger 時 `trust-record --all` 對混合 vault 掃出 683 頁（含 <private-dir>/ 480、<private-dir>/ 19、根層個人檔），504 頁無 trust frontmatter → 第一頁即 "missing frontmatter" 硬錯；過去六輪 12e 只報 ledger_missing，把這個範圍 bug 完全遮住。
- Mistake/surprise: 工具的「全 vault」≠ lint/複核實務的「框架 179 頁」；enforcement 設計隱含假設純框架 vault。
- Rule: trust.py 已加 `TRUST_CONTENT_DIRS`（concepts/entities/skills/references/synthesis/journal/projects/misc）限縮 iter_trust_pages，對齊 wiki-lint 掃描範圍（tests 43/43 過）。日後任何「全 vault」語意的工具上到混合 vault 前，先確認掃描範圍是否含個人 dirs。
- Applies to: operations.md「obsidian-wiki CLI gotchas」。

## 2026-07-29 — base_confidence 歷史值系統性高估：按來源檔數/品質計價、未算 lineage
- Situation: 全 vault 信任複核 179 頁 → lower 127（Δ均值 −0.17）、keep 43、raise 3、repair-first 6。單一 epic 樹在公式（min(L/3,1)×0.5＋avg_q×0.5）上限 0.59，但宣告值大量落在 0.85–0.95——過往 ingest 把同 epic 多子票檔算成多來源。
- Mistake/surprise: 「sources 清單長」≠「獨立佐證多」；lineage 崩塌規則下同 epic 樹＝1。owner 拍板 2026-07-29：彙整型頁不因多主題廣度加分（嚴格同主張佐證）。
- Rule: ingest/synthesize 派工 prompt 的 confidence 段明寫「同 epic 樹＝單一 lineage、單樹上限 0.59」；分數變更走 trust ledger 流程（review→approve→trust-record），不得由 lint/ingest 自動改。待修佇列：4 頁來源 07-06 reorg 遺失（rwg-order-routing/rwg-data-correction-tools/rwg-addons-launch-plan/partner-api-sevenrooms-compat），重拉後 `trust-record --page` 更新。
- Applies to: templates.md T2 CONSTRAINTS、wiki-ingest SKILL.md confidence 段。
