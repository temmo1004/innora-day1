# INNORA AI 人才培育 — Day 1 上課網頁

線上（學員）：https://temmo1004.github.io/innora-day1/

## 兩種讀法，同一份內容
- **文件模式** — 捲動長頁。學員自己看、可搜尋、可列印。
- **簡報模式** — 一次一張投影片。投影用。右上切換或按 `P`；`←/→`、空白鍵翻頁，`F` 全螢幕，`Esc` 回文件。

## 檔案
- `index.html` — **講師全版**（含講師備忘、時間軸決策紀錄）。本機開，不發布。
- `docs/index.html` — **學員版**，產生物，不要手改。
- `build.py` — 產生學員版：把 `.teach` / `.tnote` / `.slot` 從**原始碼**整段剝掉（不是 CSS 藏），並擋下人名外洩。
- `deck.py` — 注入簡報模式（冪等，可重跑）。

## 改完怎麼發
```bash
python3 deck.py     # 只有改動 index.html 結構時才需要重跑
python3 build.py
git add -A && git commit -m "..." && git push
```

完全離線可用：單一 HTML、零外部資源，場地斷網照樣開。

## 多語版
- `en.body.html` / `vi.body.html` — 英文／越南語學員版的 body（共用 index.html 的 CSS）
- `python3 build_i18n.py` — 產生 `docs/en/` 與 `docs/vi/`，並注入簡報模式
- 英文與越南語是**給越南籍學員 Ninh** 的：她中文還在學、英文無礙，聽課仍是中文
