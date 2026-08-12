"""Sinh index.html — nhung THANG noi dung SVG vao DOM.

Vi sao khong dung <img src="*.svg">: the <img> coi SVG la ANH THAY THE — khong co
DOM, nen KHONG boi den chu duoc, KHONG Ctrl+F duoc, va khi phong to bang transform
thi trinh duyet nuong thanh raster o 1x roi keo gian => MO.

Nhung thang vao DOM thi chu la text that: chon duoc, tim duoc, va net o moi muc
phong vi trang phong bang width/height chu khong phai transform: scale().

Mot cho phai xu ly: hai SVG dung TRUNG ten lop (.t .s .n .warn ...) voi gia tri
khac nhau (.t12 la 12px o so do 1, 12.5px o so do 2). Nhung chung vao mot trang
thi CSS de len nhau. Nen o day moi luat duoc gan tien to #d0 / #d1.

Chay:  python build.py
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "2026-08-12"

DIAGRAMS = [
    dict(id="d0", svg="db-va-luong-chay-v2.svg", png="db-va-luong-chay-v2@2x.png",
         tab="① Kiến trúc DB &amp; luồng chạy", name="db-va-luong-chay-v2",
         desc="4 tầng dữ liệu + 8 bước job 17:30, kèm tên file code và logic từng bước"),
    dict(id="d1", svg="van-de-ver1-v1.svg", png="van-de-ver1-v1@2x.png",
         tab="② Vấn đề ver 1", name="van-de-ver1-v1",
         desc="chẩn đoán gốc → 6 nhánh hỏng → khuôn lỗi chung → 4 khuôn còn sống trong ver 2"),
]


def boc(path: Path, sid: str):
    """Tra ve (svg_da_gan_id_va_bo_style, css_da_gan_tien_to, rong, cao)."""
    s = path.read_text(encoding="utf-8")

    m = re.search(r"<style>(.*?)</style>", s, re.S)
    css_tho = m.group(1) if m else ""
    s = s[:m.start()] + s[m.end():] if m else s

    # Bo @import cua SVG — font do TEMPLATE khai mot lan, dung mot cho.
    # PHAI bat den ");" chu KHONG duoc bat den ";" dau tien: dau ";" dau tien nam
    # GIUA url font (wght@400;500;600;700), cat o do se de lai dau nhay khong dong
    # va nuot sach stylesheet phia sau — da lam ca trang mat CSS, chu den tren nen toi.
    css_tho = re.sub(r"@import\s+url\([^)]*\)\s*;", "", css_tho)

    # gan tien to cho tung luat:  ".t { ... }"  ->  "#d0 .t { ... }"
    def gan(mm):
        sels = [f"#{sid} {x.strip()}" for x in mm.group(1).split(",") if x.strip()]
        return ", ".join(sels) + " {" + mm.group(2) + "}"

    css = re.sub(r"([^{}]+)\{([^{}]*)\}", gan, css_tho).strip()

    tag = re.search(r"<svg[^>]*>", s).group(0)
    rong = int(re.search(r'width="(\d+)"', tag).group(1))
    cao = int(re.search(r'height="(\d+)"', tag).group(1))
    # bo width/height cung; JS se dat theo muc phong. Giu viewBox.
    tag_moi = re.sub(r'\s(width|height)="\d+"', "", tag)
    tag_moi = tag_moi.replace("<svg", f'<svg id="{sid}"', 1)
    s = s.replace(tag, tag_moi, 1)

    return s.strip(), css, rong, cao


noi_dung, css_all = [], []
for d in DIAGRAMS:
    svg, css, w, h = boc(HERE / d["svg"], d["id"])
    d["w"], d["h"] = w, h
    noi_dung.append(svg)
    css_all.append(f"/* ── {d['name']} ── */\n{css}")

# Font khai MOT lan, o day, viet dung chuan HTML: dung "&" chu khong phai "&amp;"
# (trong the <style> cua HTML, noi dung la van ban tho — "&amp;" khong duoc giai ma
#  nen se lot nguyen vao URL va lam hong duong dan font).
FONT = ("@import url('https://fonts.googleapis.com/css2?"
        "family=JetBrains+Mono:wght@400;500;600;700&display=swap');")

tabs = "\n      ".join(
    f'<button class="tab" role="tab" aria-selected="{"true" if i == 0 else "false"}" data-v="{i}">{d["tab"]}</button>'
    for i, d in enumerate(DIAGRAMS))

stages = "\n  ".join(
    f'<div class="stage" id="s{i}"{"" if i == 0 else " hidden"}>\n'
    f'    <div class="pad" id="p{i}">\n{noi_dung[i]}\n    </div>\n  </div>'
    for i, d in enumerate(DIAGRAMS))

views = ",\n  ".join(
    '{{ svg:"{svg}", png:"{png}", w:{w}, h:{h}, id:"{id}", '
    'meta:\'<b>{name}</b><span class="dot">·</span>{ver}<span class="dot">·</span>{desc}\' }}'
    .format(ver=VERSION, **d) for d in DIAGRAMS)

html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRJ Quantitative Investment — Sơ đồ tầng dữ liệu</title>
<!-- TRANG NAY SINH TU build.py — dung sua tay, sua roi chay lai se mat. -->
<style>
  {FONT}
  :root{{
    --bg:#0f172a; --edge:#334155; --fg:#e2e8f0; --dim:#94a3b8;
    --cy:#22d3ee; --bl:#60a5fa;
  }}
  *{{box-sizing:border-box}}
  html,body{{height:100%}}
  body{{
    margin:0; background:var(--bg); color:var(--fg); overflow:hidden;
    font:14px/1.55 'JetBrains Mono','SF Mono','Cascadia Code',Consolas,monospace;
  }}
  header{{
    position:fixed; inset:0 0 auto 0; z-index:20; background:rgba(15,23,42,.96);
    border-bottom:1px solid var(--edge); backdrop-filter:blur(8px);
  }}
  .bar{{display:flex; align-items:center; gap:14px; padding:9px 16px; flex-wrap:wrap}}
  .brand{{font-weight:700; font-size:14px; white-space:nowrap}}
  .brand span{{color:var(--dim); font-weight:400; font-size:11px}}
  .tabs{{display:flex; gap:6px}}
  .tab{{
    background:transparent; color:var(--dim); border:1px solid var(--edge);
    padding:5px 12px; border-radius:6px; cursor:pointer; font:inherit; font-size:12px;
    white-space:nowrap; transition:.12s;
  }}
  .tab:hover{{color:var(--fg); border-color:#475569}}
  .tab[aria-selected="true"]{{background:rgba(59,130,246,.22); color:#fff; border-color:var(--bl)}}
  .spacer{{flex:1}}
  .tools{{display:flex; align-items:center; gap:6px}}
  .btn{{
    background:rgba(30,41,59,.7); color:var(--fg); border:1px solid var(--edge);
    height:28px; min-width:30px; padding:0 8px; border-radius:6px; cursor:pointer;
    font:inherit; font-size:12px; display:grid; place-items:center; transition:.12s;
  }}
  .btn:hover{{border-color:var(--cy); color:var(--cy)}}
  .pct{{min-width:52px; text-align:center; font-size:11px; color:var(--dim);
       font-variant-numeric:tabular-nums}}
  .dl{{color:var(--dim); font-size:11px; text-decoration:none; border-bottom:1px dotted #475569}}
  .dl:hover{{color:var(--cy); border-color:var(--cy)}}
  .meta{{padding:0 16px 9px; font-size:11px; color:var(--dim);
        display:flex; gap:8px; flex-wrap:wrap; align-items:baseline}}
  .meta b{{color:var(--fg); font-weight:600}}
  .dot{{color:var(--edge)}}

  .stage{{
    position:absolute; inset:var(--hh,86px) 0 0 0; overflow:auto;
    scrollbar-color:#475569 transparent;
  }}
  .stage[hidden]{{display:none}}
  .pad{{padding:20px; width:max-content}}
  /* Chu la TEXT THAT: chon duoc, Ctrl+F tim duoc, va net o moi muc phong
     vi phong bang width/height chu khong phai transform: scale(). */
  .pad svg{{display:block; height:auto}}

  /* Hai che do, giong cong cu ban tay cua trinh xem PDF.
     KEO la mac dinh — so do kho lon, cuon ngang rat bat tien. */
  .stage.m-keo{{cursor:grab; user-select:none; -webkit-user-select:none}}
  .stage.m-keo.dang-keo{{cursor:grabbing}}
  .stage.m-chon{{cursor:auto; user-select:text; -webkit-user-select:text}}
  .stage.m-chon svg text{{cursor:text}}

  .seg{{display:flex; border:1px solid var(--edge); border-radius:6px; overflow:hidden}}
  .seg .btn{{border:0; border-radius:0; height:26px; font-size:11px; color:var(--dim)}}
  .seg .btn + .btn{{border-left:1px solid var(--edge)}}
  .seg .btn[aria-pressed="true"]{{background:rgba(59,130,246,.25); color:#fff}}

  .hint{{
    position:fixed; right:14px; bottom:12px; z-index:15; font-size:10.5px; color:var(--dim);
    background:rgba(15,23,42,.92); border:1px solid var(--edge); border-radius:6px;
    padding:6px 10px; pointer-events:none;
  }}
  kbd{{background:rgba(51,65,85,.8); border:1px solid #475569; border-radius:3px;
      padding:0 4px; font:inherit; font-size:10px; color:var(--fg)}}
  @media (max-width:760px){{ .meta{{display:none}} .hint{{display:none}} }}

{chr(10).join(css_all)}
</style>
</head>
<body>

<header id="hdr">
  <div class="bar">
    <div class="brand">PRJ Quantitative Investment <span>· sơ đồ tầng dữ liệu</span></div>
    <div class="tabs" role="tablist">
      {tabs}
    </div>
    <div class="spacer"></div>
    <div class="tools">
      <div class="seg">
        <button class="btn" id="mKeo" aria-pressed="true"  title="Kéo thả để di chuyển (H)">✋ kéo</button>
        <button class="btn" id="mChon" aria-pressed="false" title="Bôi đen chữ (V)">⌶ chọn chữ</button>
      </div>
      <button class="btn" id="out" title="Thu nhỏ (−)">−</button>
      <div class="pct" id="pct">100%</div>
      <button class="btn" id="in" title="Phóng to (+)">+</button>
      <button class="btn" id="fit" title="Vừa bề ngang (F)">vừa ngang</button>
      <button class="btn" id="one" title="Kích thước thật (1)">100%</button>
      <a class="dl" id="dlsvg" href="#" download>SVG</a>
      <a class="dl" id="dlpng" href="#" download>PNG</a>
    </div>
  </div>
  <div class="meta" id="meta"></div>
</header>

<main>
  {stages}
</main>

<div class="hint">kéo thả để di chuyển · <kbd>V</kbd> đổi sang chọn chữ (<kbd>H</kbd> quay lại kéo) · <kbd>Ctrl</kbd>+lăn để phóng · <kbd>Ctrl</kbd>+<kbd>F</kbd> tìm chữ</div>

<script>
const VIEWS = [
  {views}
];
const MIN = .15, MAX = 6;
const z = VIEWS.map(() => 1);
let cur = 0, space = false, cheDo = 'keo';   // mac dinh KEO, giong cong cu ban tay cua PDF

const $ = id => document.getElementById(id);
const stage = i => $('s' + i);
const svgEl = i => $(VIEWS[i].id);

function headerH(){{ document.documentElement.style.setProperty('--hh', $('hdr').offsetHeight + 'px'); }}

function apply(i){{
  const v = VIEWS[i];
  svgEl(i).style.width = (v.w * z[i]) + 'px';
  if (i === cur) $('pct').textContent = Math.round(z[i] * 100) + '%';
}}
function setZoom(i, nz, ax, ay){{
  const st = stage(i), old = z[i];
  nz = Math.max(MIN, Math.min(MAX, nz));
  if (nz === old) return;
  // giu diem duoi con tro dung yen
  const cx = (st.scrollLeft + (ax ?? st.clientWidth / 2)) / old;
  const cy = (st.scrollTop  + (ay ?? st.clientHeight / 2)) / old;
  z[i] = nz; apply(i);
  st.scrollLeft = cx * nz - (ax ?? st.clientWidth / 2);
  st.scrollTop  = cy * nz - (ay ?? st.clientHeight / 2);
}}
function fit(i){{
  const st = stage(i);
  if (st.clientWidth < 80) return;
  setZoom(i, (st.clientWidth - 56) / VIEWS[i].w);
}}

VIEWS.forEach((v, i) => {{
  const st = stage(i);
  st.addEventListener('wheel', e => {{
    if (!e.ctrlKey && !e.metaKey) return;          // khong Ctrl thi cuon binh thuong
    e.preventDefault();
    const r = st.getBoundingClientRect();
    setZoom(i, z[i] * (e.deltaY < 0 ? 1.12 : 1 / 1.12), e.clientX - r.left, e.clientY - r.top);
  }}, {{ passive:false }});

  let down = false, px = 0, py = 0;
  st.addEventListener('pointerdown', e => {{
    // Cham tay thi de trinh duyet cuon tu nhien, dung cuop su kien.
    if (e.pointerType !== 'mouse') return;
    // Keo khi: chuot giua · giu Space · hoac chuot trai trong che do KEO.
    if (!(e.button === 1 || space || (e.button === 0 && cheDo === 'keo'))) return;
    down = true; px = e.clientX; py = e.clientY;
    st.classList.add('dang-keo'); st.setPointerCapture(e.pointerId); e.preventDefault();
  }});
  st.addEventListener('pointermove', e => {{
    if (!down) return;
    st.scrollLeft -= e.clientX - px; st.scrollTop -= e.clientY - py;
    px = e.clientX; py = e.clientY;
  }});
  const up = () => {{ down = false; st.classList.remove('dang-keo'); }};
  st.addEventListener('pointerup', up);
  st.addEventListener('pointercancel', up);
}});

// ── che do: KEO (mac dinh) hoac CHON CHU ──────────────────────────────────
function datCheDo(m){{
  cheDo = m;
  VIEWS.forEach((v, i) => {{
    stage(i).classList.toggle('m-keo', m === 'keo');
    stage(i).classList.toggle('m-chon', m === 'chon');
  }});
  $('mKeo').setAttribute('aria-pressed', String(m === 'keo'));
  $('mChon').setAttribute('aria-pressed', String(m === 'chon'));
}}
$('mKeo').onclick  = () => datCheDo('keo');
$('mChon').onclick = () => datCheDo('chon');

function show(i){{
  cur = i;
  VIEWS.forEach((v, k) => stage(k).hidden = (k !== i));
  document.querySelectorAll('.tab').forEach(t => t.setAttribute('aria-selected', String(+t.dataset.v === i)));
  $('meta').innerHTML = VIEWS[i].meta;
  $('dlsvg').href = VIEWS[i].svg;
  $('dlpng').href = VIEWS[i].png;
  headerH(); apply(i);
}}

document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => show(+t.dataset.v)));
$('in').onclick  = () => setZoom(cur, z[cur] * 1.25);
$('out').onclick = () => setZoom(cur, z[cur] / 1.25);
$('fit').onclick = () => fit(cur);
$('one').onclick = () => setZoom(cur, 1);

addEventListener('keydown', e => {{
  // Giu Space: tam thoi keo duoc ke ca dang o che do chon chu.
  if (e.code === 'Space' && !space) {{
    space = true; stage(cur).classList.add('m-keo');
    if (e.target === document.body) e.preventDefault();
    return;
  }}
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === 'h') datCheDo('keo');
  else if (k === 'v') datCheDo('chon');
  else if (k === 'f') fit(cur);
  else if (k === '1') setZoom(cur, 1);
  else if (k === '+' || k === '=') setZoom(cur, z[cur] * 1.25);
  else if (k === '-' || k === '_') setZoom(cur, z[cur] / 1.25);
}});
addEventListener('keyup', e => {{
  if (e.code !== 'Space') return;
  space = false;
  VIEWS.forEach((v, i) => stage(i).classList.remove('dang-keo'));
  datCheDo(cheDo);                       // tra lai che do dang chon
}});
addEventListener('resize', headerH);

headerH(); datCheDo('keo'); show(0); fit(0); VIEWS.forEach((v, i) => {{ if (i) fit(i); }});
</script>
</body>
</html>
"""

(HERE / "index.html").write_text(html, encoding="utf-8")
print(f"index.html — {len(html):,} ky tu · {len(DIAGRAMS)} so do nhung thang vao DOM")
for d in DIAGRAMS:
    print(f"  {d['id']}  {d['name']}  {d['w']}x{d['h']}")
