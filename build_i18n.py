#!/usr/bin/env python3
"""組出多語版學員頁：共用 index.html 的 CSS，body 各語一份。
輸出 docs/<lang>/index.html，並注入簡報模式。"""
import re, pathlib, shutil, subprocess, sys
BASE = pathlib.Path(__file__).parent
LANGS = {"en": ("en.body.html", "Day 1 · Build yourself with AI — INNORA", "en"),
         "vi": ("vi.body.html", "Ngày 1 · Dùng AI tạo nên chính bạn — INNORA", "vi")}

css = re.search(r'<style>(.*?)</style>', (BASE/"index.html").read_text(encoding="utf-8"), re.S).group(1)
css = re.split(r'/\* ===== deck mode ===== \*/', css)[0]

COPY_JS = r"""<script>
// 複製提示詞：取純文字，把註解欄（← 改成…）整段拿掉
(function(){
  function clean(el){
    var c=el.cloneNode(true);
    c.querySelectorAll('.cm').forEach(function(n){ n.remove(); });
    return c.textContent.split('\n').map(function(l){ return l.replace(/\s+$/,''); }).join('\n').trim();
  }
  function fallback(txt){
    var ta=document.createElement('textarea');
    ta.value=txt; ta.setAttribute('readonly','');
    ta.style.cssText='position:fixed;top:-9999px;left:-9999px';
    document.body.appendChild(ta); ta.select();
    var ok=false;
    try{ ok=document.execCommand('copy'); }catch(e){}
    document.body.removeChild(ta);
    return ok;
  }
  document.querySelectorAll('.copy').forEach(function(btn){
    btn.addEventListener('click',function(){
      var src=document.getElementById(btn.dataset.t);
      if(!src) return;
      var txt=clean(src);
      function done(ok){
        btn.textContent = ok ? '已複製 ✓' : '請手動選取';
        btn.classList.toggle('done',ok);
        setTimeout(function(){ btn.textContent='複製'; btn.classList.remove('done'); },1800);
      }
      if(navigator.clipboard && window.isSecureContext){
        navigator.clipboard.writeText(txt).then(function(){done(true);},function(){done(fallback(txt));});
      } else {
        done(fallback(txt));
      }
    });
  });
})();
</script>"""

made = []
for lang, (bodyfile, title, htmllang) in LANGS.items():
    src = BASE/bodyfile
    if not src.exists():
        print(f"  · {lang}: 沒有 {bodyfile}，略過"); continue
    body = src.read_text(encoding="utf-8")
    out = BASE/"docs"/lang; out.mkdir(parents=True, exist_ok=True)
    page = (f'<!doctype html>\n<html lang="{htmllang}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{title}</title>\n<style>{css}</style>\n</head>\n<body>\n{body}\n'
            + COPY_JS + '\n</body></html>')
    (out/"index.html").write_text(page, encoding="utf-8")
    subprocess.run([sys.executable, str(BASE/"deck.py"), str(out/"index.html")], check=True,
                   capture_output=True)
    made.append(lang)

# 示範圖給各語頁用相對路徑 ../cover-demo.jpg
demo = BASE/"docs"/"cover-demo.jpg"
if not demo.exists():
    m = re.search(r'src="data:image/jpeg;base64,([^"]+)"', (BASE/"index.html").read_text(encoding="utf-8"))
    if m:
        import base64
        demo.write_bytes(base64.b64decode(m.group(1)))
        print("  · 匯出 cover-demo.jpg 供多語頁引用")
print("✅ 多語頁:", "、".join(made) or "無")
