#!/usr/bin/env python3
"""把 index.html（含講師備忘）產出學員版 docs/index.html。

講師區 <div class="teach">…</div>、<span class="tnote">…</span> 與講師模式按鈕
會整段從輸出的原始碼移除——不是用 CSS 藏，學員 view-source 也看不到。
"""
import re, pathlib, sys

SRC = pathlib.Path(__file__).parent / "index.html"
OUT = pathlib.Path(__file__).parent / "docs" / "index.html"

def strip_block(html, cls):
    """移除 <tag class="cls">…</tag>，正確處理巢狀同名標籤。"""
    out, i = [], 0
    pat = re.compile(r'<(\w+)([^>]*\bclass="[^"]*\b%s\b[^"]*"[^>]*)>' % re.escape(cls))
    while True:
        m = pat.search(html, i)
        if not m:
            out.append(html[i:])
            return "".join(out)
        out.append(html[i:m.start()])
        tag, depth, j = m.group(1), 1, m.end()
        step = re.compile(r'</?%s\b' % re.escape(tag))
        while depth:
            n = step.search(html, j)
            if not n:                      # 標籤沒收好 → 不要靜默吃掉剩下的檔案
                raise SystemExit(f"build: <{tag} class={cls}> 沒有對應的結束標籤")
            depth += -1 if n.group(0).startswith("</") else 1
            j = html.index(">", n.end()) + 1
        i = j

def main():
    html = SRC.read_text(encoding="utf-8")
    # slot = 講師還沒填的待辦坑位，學員版不該看到（填好後把 .slot 換成真連結）
    for cls in ("teach", "tnote", "slot"):
        html = strip_block(html, cls)
    html = re.sub(r'\s*<button class="tbtn".*?</button>', "", html, flags=re.S)
    html = re.sub(r'// 講師模式\n\(function\(\)\{.*?\n\}\)\(\);\n', "", html, flags=re.S)

    for leak in ("講師", "白羊", "Joe", "待拍板"):
        if leak in html:
            raise SystemExit(f"build: 學員版還留著「{leak}」，檢查 index.html")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"OK  {len(SRC.read_text(encoding='utf-8')):,} → {len(html):,} bytes  →  {OUT}")

if __name__ == "__main__":
    main()
