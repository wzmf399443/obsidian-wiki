# Lessons Log

Hard-won corrections from real sessions. Append-only during a session; distilled
per `.rules/maintenance.md` when >100 lines. Format: see maintenance.md.

<!-- Distilled 2026-09-23 (backup: lessons.md.bak-20260923; ~/.claude/backups/2026-09-23-lessons-distill/).
Second round: the 2026-07-18 round (backup lessons.md.bak-20260718, now in that dir's old-bak/) had folded or
retired everything through 07-16. This round folded or retired all 55 entries 07-20 … 09-23; four meta-lessons
stay below. Full 55-row map (local, gitignored): output/lessons-distill-2026-09-23/mapping.md.
- Retired, already encoded (each also left a one-clause pointer): 07-23 ^[extracted] (wiki-ingest SKILL.md:459; T2),
  07-29 trust rglob (trust.py TRUST_CONTENT_DIRS; ops scope), 07-31 colon markers (check7 fixed 08-03,
  wiki-lint SKILL.md:125; T2), 08-05 <company> read (vault CLAUDE.md ## Scope; ops scope).
- operations.md — §Mixed-vault scope (new): 07-29, 08-05, 08-12 check.py, 08-17 (its ugrep note replaced by the
  09-23 fact), 09-23 bare grep, 09-23 root glob. §Shell / grep / git gotchas (new): 08-31 zsh, 09-01 grep -E,
  09-01 git untracked, 09-04 ${=VAR}, 09-15 newermt, 09-16/17 positive control. §Delta: 09-01, 09-02 comment
  edits, 09-04 skip rule, 09-23 hash proof. Mapping: 09-21 sources:, 09-23 basename. §CLI: 09-02 uv run (stale
  fact fixed), 07-30 .env, 08-06 --json/xargs, 08-14 graph-query, 07-29 queued re-pulls. §Lint: 07-20, 07-23
  cleanup, 08-27 verifiers, 08-27 YAML hard error, 09-23 image links. §Repo structure: 08-31 scripts/ + hard errors.
- templates.md — T2: 07-21, 07-23, 07-29 + 09-23 confidence, 07-31, 08-12 today-delta/len(), 08-19, 08-27 quoting,
  08-31 both sides, 09-04 key list, 09-17 list insert, 09-18 body bytes, 09-21 mention-only, 09-23 DEFER,
  09-23 identifiers, scope line. T3: 08-12 LINT_FIX, 08-19, 09-04. T5: 07-21, 07-24, 08-12, 08-13, 08-14, 08-19,
  08-27 CROSS-CLUSTER, 08-31, 09-17 check-5, 09-18 carry, 09-23 identifiers + glob. T6 (new, coordinator run
  sheet; since 2026-09-24 in templates-ingest-coordination.md): 07-24, 08-12, 08-14, 08-27 ×3, 08-31, 09-04, 09-16/17, 09-17 ×2, 09-18, 09-21 ×2, 09-23 ×3.
- delegation.md — §3 second-hand facts: 09-16/17, 09-17, 09-21. §4: 08-27 never hand over, 09-16/17 report on
  disk. §5 interruptions note (no ladder change): 07-24, 08-27, 09-04, 09-16/17.
- Open candidate kept here (not a rule): wiki-capture quick mode should grep-check file:line before writing, or
  cite the function name instead of a line number (08-13). -->

## 2026-08-27 — 驗證器誤報率高時會淹沒真問題（meta）
- Situation / Mistake: 96 頁收尾自寫驗證器首跑報 97 問題，逐條查證只有 2 個是真的（91 個是驗證器自己的 YAML regex bug）；若照單改頁面，修的是不存在的問題，真問題反被淹沒。
- Rule: 驗證器的結論要先過「它自己的誤報率」這關——首跑數字異常就先拿 1–2 條實測驗證器本身，修好再看結論（機械細則：operations.md §Lint「Closing verifier scripts」）。
- Applies to: 所有 closing/lint 驗證器（`scripts/verify_mechanical.py` 與 run-dir 腳本）。

## 2026-09-17 — 同批 `updated` 只證明頁面被重寫，不證明矛盾是新的（meta）
- Situation / Mistake: check-5 finding 因兩頁 `updated` 同為本批時戳被標成「本輪新生」，其實 09-15 N-2 早已記過一半；把時間欄位當語意證據（與 `-newermt` 時區誤判同族），prompt 裡「vault 是熱的」又先給了錨。
- Rule: 時戳（mtime／`updated`）只證明「被寫過」，不證明內容的新舊或對錯；新舊一律對上一輪 open items 做編號比對（templates.md T5）。
- Applies to: templates.md T5 sharded-detection 行與 coordinator notes；wiki-lint 回報順序（carry closure 先於 check-5 定稿）。

## 2026-09-18 — 自帶 as-of 標註的舊日期是健康的，不是過期（meta）
- Situation / Mistake: `hot.md` Active Threads「停在 07-17」連續多輪被列為盲區，但下一行就寫明基準日＋「不可當現況引用」；只取值、不讀上下文的檢查項會把誤判機械複製到無限期，照「盲區」處方改日期反而製造假資訊。
- Rule: 「欄位值老舊」≠「內容過期」——判讀前先讀該值前後的上下文（T5 ±2 行），自帶 as-of 標註的區塊判 healthy；`hot.md` Active Threads 應從 wiki-lint 盲區清單移除。
- Applies to: templates.md T5 carry/盲區檢查項；wiki-lint 盲區清單。

## 2026-09-18 — 「重建＋驗證」≠「逐行改」：一組 assert 只證明它檢查過的事（meta）
- Situation / Mistake: 明知 09-17 教訓仍用整塊重建 frontmatter＋一串 YAML assert 升 45 頁 lifecycle，回報 0 errors，實際 41 頁 body 空行被吃；是 subagent 的 diff vs backup 抓到協調者，不是我的驗證。
- Rule: 規則寫「逐行」就逐行，包再多驗證也還是重建；assert 要瞄準實際會壞的地方（body byte 級不變）；派給 subagent 的硬性 diff 驗收同樣套在協調者自己身上。
- Applies to: templates.md T2 frontmatter 行、templates-ingest-coordination.md T6 首行（協調者自我約束）；所有 frontmatter 批改腳本。
