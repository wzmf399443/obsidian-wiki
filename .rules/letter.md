# 給未來 session 的信

> 2026-07-03，由一次性的 Fable 5 session 寫下。這是歷史文件——除了在文末加註日期附言，
> 不要改寫它（見 maintenance.md）。你（未來的 session）多半是 Sonnet 或 GLM 中階模型，
> 這封信假設你沒看過這個環境。

## 使用者沒問、但你必須知道的三件事

### 1. 這個 vault 是使用者的工作命脈，不是玩具

看 `$VAULT/hot.md` 和 `log.md` 就知道：這裡沉澱的是 <company> QA 工作的即時知識——
<project-key> 票據狀態、integration 規格（inline/SevenRooms/Bistrochat/RwG）、QA 驗收結論。
使用者靠它跨 session、跨工具接續工作。這代表：

- **寫錯比不寫更糟。** 一筆錯誤的票據狀態（例如把 PR Reviewing 寫成 Done）會在
  未來的 wiki-query 裡以權威口吻誤導使用者。ingest 時分不清的資訊，標 `ambiguous`
  或不入庫，勝過猜一個。vault 裡已有這個慣例（log 裡多處 "flagged ambiguous"），沿用它。
- **vault 混有公司資料且幾乎沒打 visibility 標籤。** `<private-dir>/` 是巢狀的公司筆記、
  `<private-dir>/` 是舊筆記、`attached/` 是附件——都不是框架管理的目錄，lint/ingest 一律排除
  （既有慣例，log 可證）。任何 export、publish、或把內容送出本機的操作，先當作
  全庫含敏感資料處理，問過使用者再動。

### 2. 主對話的 context 是最稀缺的資源，比 token 費用更稀缺

這套制度（`.rules/` 全部）的核心邏輯只有一句：**主對話讀進來的每個字都永久佔用
指揮位置的記憶體；塞滿了，harness 會壓縮你的上下文，你會在任務做到一半時忘記
自己的規則。** 所以大量讀取派 subagent、報告只收結論、開場靠三層快取暖機——
`hot.md`（vault 近況）→ persistent memory（環境事實）→ AGENTS.md pinned facts
（設定值）。先讀 hot.md 再動工，是這個環境最划算的一次 tool call。

### 3. 制度已經在退化了，而且有實例

規格說 `hot.md` 是「約 500 字的快照」——實際上它已經膨脹到遠超過（單一條目就上千字，
Active Threads 累積了半年的票據明細）。這就是無人執行邊界時的自然結局，也是你要
對抗的重力。下次更新 hot.md 時：舊條目摺疊成一行、已 Done 的 thread 移出（知識本體
在 wiki 頁裡，hot.md 只是指標）、把它修回 ~500 字。log.md 同理，只 append 不整理
也會無限長大。

## 這套制度最可能的退化方式（按可能性排序）與預防

1. **規則被靜默跳過**——趕時間的 session 覺得「這次不用驗證了」。預防：完成定義
   （judgment.md R2）把 bookkeeping 和 read-back 綁進「done」，跳過就等於沒做完；
   如果你正想跳過某條規則，那個念頭本身就該寫進 lessons.md 讓使用者看到。
2. **檔案膨脹到沒人讀**——lessons 只加不併、AGENTS.md 越長越雜（hot.md 已示範）。
   預防：maintenance.md 的行數門檻是硬規定，超了就整併或向使用者提議修剪。
3. **pinned facts 過期後仍被信任**——.env 改了、vault 搬了、QMD 裝了，但 AGENTS.md
   還寫著舊事實。預防：每個 pin 帶查核日期；破壞性操作前重新驗證超過 6 個月的 pin。
4. **upstream merge 蓋掉客製**——AGENTS.md 會跟上游衝突。預防：merge 前備份，
   衝突時保留 Session Protocol 與 pinned facts 段落（maintenance.md 有細則）。
5. **升級樓梯變成裝飾**——所有事都用預設模型硬做，或反過來什麼都丟 Big。預防：
   delegation.md §5 的門檻是數字（錯一次/錯兩次/兩輪上限），照數字走，不憑感覺。

## 誠實條款（這套制度做不到的事）

拆解、驗證、多樣本評審能把「執行品質」補到接近強模型；但**模糊需求和品味判斷
補不了**。遇到「這個 synthesis 有沒有洞見」「這兩頁該不該合併」這類問題，照
judgment.md R6 的樓梯走：升級 Big → 多答案評審 → 分歧就攤開給使用者選。
「這題需要你決定」是專業的輸出，不是失敗。查不到的事標註「未查證」，永遠不要編。

## 交接欄

- 2026-07-03（Fable 5，建制 session）：A–G 全部交付完成（diagnosis、AGENTS.md 重寫、
  delegation、judgment、templates、maintenance+lessons、本信）。已知未竟事項：
  (1) GLM 模型棧的 Middle/Small 型號名未取得——delegation.md §2 留有待填欄位，
  下次使用者在場時問一句補上；(2) hot.md 的瘦身只寫了規則沒有執行——下次
  wiki 維護 session 順手做。
