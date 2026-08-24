#!/usr/bin/env python3
"""把簡報模式（deck mode）注入 index.html。

同一份內容兩種讀法：
  文件模式 — 捲動長頁，學員自己看、可搜尋、可列印（原本的樣子）
  簡報模式 — 一次一張投影片，投影用；‹ › / 方向鍵 / 空白鍵切換，F 全螢幕

做法：把每個 section 依 h3 / .prompt / .say 自動切成投影片，包進 <div class="slide">。
文件模式下 .slide 是 display:contents，等於不存在，版面完全不變。

冪等：重跑不會疊加（先移除舊的 deck 區塊再注入）。
"""
import re, sys, pathlib

CSS = r"""
/* ===== deck mode ===== */
.slide{display:contents}
.dkbar{display:none}
body.deck{overflow:hidden}
body.deck nav{position:fixed;top:0;left:0;right:0}
body.deck main{max-width:none;padding:0}
body.deck header.hero,body.deck section{margin:0;padding:0;border:0}
body.deck footer{display:none}   /* footer 不在切片裡，簡報模式會裸露在背景 */
body.deck .slide{display:none}
body.deck .slide.on{
  display:flex;flex-direction:column;
  position:fixed;top:60px;bottom:62px;left:0;right:0;
  width:min(1180px,100% - 40px);margin:0 auto;
  background:var(--card);border:1px solid var(--line);border-radius:20px;
  box-shadow:0 18px 40px -18px rgba(0,0,0,.22);
  padding:34px 46px;overflow-y:auto;overscroll-behavior:contain}
/* flex 子元素預設會 shrink，長內容會被壓扁裁掉而不是讓外框捲動 */
body.deck .slide.on>*{flex-shrink:0}
body.deck .slide.on>*:first-child{margin-top:0}
body.deck .slide.on>*:last-child{margin-bottom:0}
/* flex column 會把 inline-block 的膠囊拉滿整行 */
body.deck .slide.on>.steptag{align-self:flex-start}
#dk[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
body.deck .crumb{display:block;font-size:12px;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink3);margin:0 0 18px;flex:none}
.crumb{display:none}
body.deck h2{font-size:clamp(26px,3.6vw,40px)}
body.deck h3{font-size:clamp(20px,2.4vw,27px);margin-top:0}
body.deck .say{font-size:clamp(18px,2.1vw,24px)}
body.deck pre{font-size:clamp(13px,1.25vw,17px)}
body.deck table{font-size:clamp(15px,1.5vw,19px)}
/* 時間軸 12 列，用一般行高在 1080p 會捲掉後幾列＝投影時看不到 */
body.deck #timeline table{font-size:clamp(14px,1.15vw,17px)}
body.deck #timeline th,body.deck #timeline td{padding:6px 12px}
body.deck #timeline h2{margin-bottom:4px}
body.deck #timeline .sub{margin-bottom:12px}
body.deck .oc b{font-size:17px}
body.deck .hero .lede{font-size:clamp(18px,2.4vw,26px)}

body.deck .dkbar{display:flex;position:fixed;bottom:0;left:0;right:0;height:62px;
  align-items:center;gap:14px;padding:0 20px;background:rgba(251,250,248,.96);
  backdrop-filter:blur(8px);border-top:1px solid var(--line);z-index:60}
.dkbar button{font:inherit;font-size:19px;line-height:1;cursor:pointer;
  width:42px;height:42px;border-radius:11px;border:1px solid var(--line);
  background:var(--card);color:var(--ink)}
.dkbar button:hover:not(:disabled){background:var(--accent-soft);
  border-color:var(--accent);color:var(--accent)}
.dkbar button:disabled{opacity:.32;cursor:default}
.dkcount{font-size:14px;font-weight:700;color:var(--ink2);
  min-width:66px;text-align:center;font-variant-numeric:tabular-nums}
.dkwhere{font-size:14px;color:var(--ink3);flex:1;min-width:0;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.dkhint{font-size:12px;color:var(--ink3);white-space:nowrap}
.dkprog{position:fixed;left:0;bottom:62px;height:3px;background:var(--accent);
  z-index:61;transition:width .18s ease;display:none}
body.deck .dkprog{display:block}
@media (max-width:720px){
  body.deck .slide.on{padding:22px 20px;top:56px}
  .dkhint{display:none}
}
@media print{ body.deck{overflow:visible}
  body.deck .slide,body.deck .slide.on{display:contents;position:static}
  .dkbar,.dkprog,.crumb{display:none!important} }
"""

JS = r"""
/* ===== deck mode ===== */
(function(){
  var main=document.querySelector('main');
  if(!main) return;

  /* --- 1. 自動切片：每個 section 依 h3 / .prompt / .say 斷開 --- */
  function isBreak(el){
    if(el.nodeType!==1) return false;
    if(el.tagName==='H3') return true;
    return el.classList.contains('prompt')||el.classList.contains('say');
  }
  /* 標題類節點不算「實質內容」——只有標題的片不該獨立成一張空投影片 */
  function heavy(n){
    if(n.nodeType!==1) return n.textContent.trim().length>0;
    if(n.tagName==='H2'||n.tagName==='H3') return false;
    return !(n.classList.contains('steptag')||n.classList.contains('sub'));
  }
  function chunk(host,label){
    var kids=[].slice.call(host.childNodes), groups=[], cur=null, hasBody=false;
    kids.forEach(function(n){
      if(n.nodeType===3 && !n.textContent.trim()) return;      // 純空白略過
      if(!cur || (hasBody && isBreak(n))){ cur=[]; groups.push(cur); hasBody=false; }
      cur.push(n);
      if(heavy(n)) hasBody=true;
    });
    groups.forEach(function(g){
      var d=document.createElement('div');
      d.className='slide';
      var c=document.createElement('b'); c.className='crumb'; c.textContent=label;
      d.appendChild(c);
      host.insertBefore(d,g[0]);
      g.forEach(function(n){ d.appendChild(n); });
    });
  }
  var hero=main.querySelector('header.hero');
  if(hero) chunk(hero,'Day 1');
  [].forEach.call(main.querySelectorAll('section'),function(s){
    var h=s.querySelector('h2');
    chunk(s,h?h.textContent.trim():'');
  });

  var slides=[].slice.call(main.querySelectorAll('.slide'));
  if(!slides.length) return;

  /* --- 0. 依頁面語言取字 --- */
  var L = (document.documentElement.lang || 'zh').slice(0,2);
  var T = {
    zh:{deck:'簡報模式',doc:'文件模式',prev:'上一張（←）',next:'下一張（→ 或空白鍵）',
        exit:'回到文件模式（Esc）',hint:'← → 切換　F 全螢幕　Esc 回文件'},
    en:{deck:'Slides',doc:'Document',prev:'Previous (←)',next:'Next (→ or Space)',
        exit:'Back to document (Esc)',hint:'← → move　F fullscreen　Esc exit'},
    vi:{deck:'Trình chiếu',doc:'Tài liệu',prev:'Trang trước (←)',next:'Trang sau (→ hoặc Space)',
        exit:'Về chế độ tài liệu (Esc)',hint:'← → chuyển　F toàn màn hình　Esc thoát'}
  }[L] || null;
  if(!T) T = {deck:'Slides',doc:'Document',prev:'Previous',next:'Next',exit:'Exit',hint:''};

  /* --- 2. 控制列 --- */
  var prog=document.createElement('div'); prog.className='dkprog'; prog.style.width='0';
  var bar=document.createElement('div'); bar.className='dkbar';
  bar.innerHTML='<button data-d="-1" title="'+T.prev+'">&lsaquo;</button>'+
    '<button data-d="1" title="'+T.next+'">&rsaquo;</button>'+
    '<span class="dkcount"></span><span class="dkwhere"></span>'+
    '<span class="dkhint">'+T.hint+'</span>'+
    '<button data-x="1" title="'+T.exit+'">&times;</button>';
  document.body.appendChild(prog); document.body.appendChild(bar);
  var cnt=bar.querySelector('.dkcount'), where=bar.querySelector('.dkwhere');
  var pv=bar.querySelector('[data-d="-1"]'), nx=bar.querySelector('[data-d="1"]');

  var i=0, on=false;
  function show(n){
    i=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(s,k){ s.classList.toggle('on',k===i); });
    cnt.textContent=(i+1)+' / '+slides.length;
    var c=slides[i].querySelector('.crumb');
    where.textContent=c?c.textContent:'';
    prog.style.width=((i+1)/slides.length*100)+'%';
    pv.disabled=(i===0); nx.disabled=(i===slides.length-1);
    slides[i].scrollTop=0;
  }
  function setDeck(v){
    on=v; document.body.classList.toggle('deck',on);
    dbtn.setAttribute('aria-pressed',on?'true':'false');
    dbtn.textContent=on?T.doc:T.deck;
    try{ localStorage.setItem('deck',on?'1':'0'); }catch(e){}
    if(on){ show(i); } else {
      slides.forEach(function(s){ s.classList.remove('on'); });
      if(slides[i]) slides[i].scrollIntoView({block:'start'});
    }
  }

  /* --- 3. 模式切換鈕（掛在 nav 的按鈕列） --- */
  var dbtn=document.createElement('button');
  dbtn.className='tbtn'; dbtn.id='dk'; dbtn.setAttribute('aria-pressed','false');
  dbtn.textContent=T.deck;
  var tt=document.getElementById('tt');
  if(tt&&tt.parentNode) tt.parentNode.insertBefore(dbtn,tt);
  else document.querySelector('.navin').appendChild(dbtn);

  dbtn.addEventListener('click',function(){ setDeck(!on); });
  bar.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    if(b.dataset.x) return setDeck(false);
    show(i+(+b.dataset.d));
  });

  document.addEventListener('keydown',function(e){
    var t=e.target.tagName;
    if(t==='INPUT'||t==='TEXTAREA'||e.target.isContentEditable) return;
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    if((e.key==='p'||e.key==='P')&&!on){ e.preventDefault(); return setDeck(true); }
    if(!on) return;
    switch(e.key){
      case 'ArrowRight': case 'PageDown': case ' ': e.preventDefault(); show(i+1); break;
      case 'ArrowLeft': case 'PageUp': e.preventDefault(); show(i-1); break;
      case 'Home': e.preventDefault(); show(0); break;
      case 'End': e.preventDefault(); show(slides.length-1); break;
      case 'Escape': e.preventDefault(); setDeck(false); break;
      case 'f': case 'F': e.preventDefault();
        if(document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();
        break;
    }
  });

  /* nav 連結在簡報模式下 = 跳到那一節的第一張 */
  [].forEach.call(document.querySelectorAll('.navlinks a'),function(a){
    a.addEventListener('click',function(e){
      if(!on) return;
      var tgt=document.querySelector(a.getAttribute('href')); if(!tgt) return;
      e.preventDefault();
      var first=tgt.classList.contains('slide')?tgt:tgt.querySelector('.slide');
      var k=slides.indexOf(first);
      if(k>=0) show(k);
    });
  });

  try{ if(localStorage.getItem('deck')==='1') setDeck(true); }catch(e){}
})();
"""

MARK_CSS = ("/* ===== deck mode ===== */", "/* ===== /deck mode ===== */")
MARK_JS  = ("/* ===== deck mode ===== */", "/* ===== /deck mode ===== */")


def drop(text, a, b):
    """移掉上一次注入的區塊，讓重跑不會疊加。"""
    while True:
        s = text.find(a)
        if s < 0:
            return text
        e = text.find(b, s)
        if e < 0:
            raise SystemExit("deck: 找到起始標記但沒有結束標記，檔案可能被手改壞了")
        # 連同注入時補的換行一起吃掉，否則每跑一次就多長幾個空行（不冪等）
        text = text[:s].rstrip("\n \t") + "\n" + text[e + len(b):].lstrip("\n \t")


def main():
    p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                     else pathlib.Path(__file__).parent / "index.html")
    h = p.read_text(encoding="utf-8")
    h = drop(h, *MARK_CSS)
    h = drop(h, *MARK_JS)

    if "</style>" not in h or "</script>" not in h:
        raise SystemExit("deck: 找不到 </style> 或 </script>，結構不對")

    h = h.replace("</style>", CSS.strip() + "\n" + MARK_CSS[1] + "\n</style>", 1)
    # 注入到最後一個 </script> 之前
    k = h.rfind("</script>")
    h = h[:k] + "\n" + JS.strip() + "\n" + MARK_JS[1] + "\n" + h[k:]

    p.write_text(h, encoding="utf-8")
    print(f"OK  deck mode 已注入 {p}  ({len(h):,} chars)")


if __name__ == "__main__":
    main()
