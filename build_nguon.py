"""Sinh nguon-du-lieu.html — bản đồ 4 nhà cung cấp, mọi cửa, mọi trường.

Nguồn số liệu: mau-tai/cac-cua.json (gọi thật từng cửa, xem scratchpad/do_moi_cua.py)
              + meta.vendor_door / meta.source_contract của quant_v2.

Bấm vào một cửa để mở: danh sách trường đầy đủ + mẫu JSON nguyên văn.

Chạy:  python build_nguon.py
"""
import json
import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(r"C:\Users\OS\Lucius\Projects\PRJ Quantitative Investment\.env")

CUA = json.loads((HERE / "mau-tai" / "cac-cua.json").read_text(encoding="utf-8"))

# ── trạng thái từ DB ────────────────────────────────────────────────────────
tt, hd = {}, {}
try:
    with psycopg.connect(os.environ["V2_READER_URL"]) as c, c.cursor() as cur:
        cur.execute("SELECT host, path, dataset, tinh_trang FROM meta.vendor_door")
        for h, p, ds, t in cur.fetchall():
            tt[(h, p)] = (ds, t)
        cur.execute("""SELECT host, path, source, price_unit, price_basis, depth_from, vai_tro
                       FROM meta.source_contract""")
        for h, p, s, u, b, d, v in cur.fetchall():
            hd[(h, p)] = dict(source=s, unit=u, basis=b, depth=str(d) if d else None, vai_tro=v)
        cur.execute("""SELECT source, count(*), min(trade_date), max(trade_date)
                       FROM obs.price_daily GROUP BY 1""")
        kho = {s: (n, str(a), str(b)) for s, n, a, b in cur.fetchall()}
        cur.execute("SELECT source, count(*) FROM obs.corp_action GROUP BY 1")
        kho.update({s: (n, None, None) for s, n in cur.fetchall()})
except Exception as e:                                                # noqa: BLE001
    print("khong doc duoc DB:", e)
    kho = {}

# ── ghi đè thủ công: thứ phép dò không tự biết ──────────────────────────────
# `gap-chart` trả {message, payload, error, code} — vỏ LỖI, không phải dữ liệu.
VO_LOI = {"vci-ohlc-gap-chart"}

NHA = [
    ("SSI", "iboard-api.ssi.com.vn (công khai) · fc-data.ssi.com.vn (FastConnect, cần Bearer)"),
    ("DNSE", "services.entrade.com.vn · api-bo.dnse.com.vn — đều công khai"),
    ("VCI", "trading.vietcap.com.vn · iq.vietcap.com.vn — đều công khai"),
    ("vnstock", "thư viện Python, không phải API. CẤM dùng cho GIÁ — ngoại lệ 03/08 chỉ cho BCTC"),
]

def trang_thai(ma, v):
    if ma in VO_LOI:
        return "hong", "trả vỏ lỗi"
    if not v["ok"]:
        return "hong", "gọi không ra dữ liệu"
    k = tt.get((v["host"], v["path"]))
    if k:
        return {"DANG_DUNG": ("dung", "đang dùng"),
                "CHUA_DUNG": ("chua", "chưa dùng"),
                "KHONG_DUNG": ("khong", "không cần"),
                "HONG": ("hong", "khai HỎNG")}.get(k[1], ("chua", k[1]))
    return "chua", "chưa khai trong vendor_door"

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

khoi = []
for nha, mo_ta in NHA:
    cua = [(k, v) for k, v in CUA.items() if v["vendor"] == nha]
    if not cua:
        continue
    the = []
    for ma, v in cua:
        cls, nhan = trang_thai(ma, v)
        h = hd.get((v["host"], v["path"]), {})
        meta = []
        if h.get("source"):
            n = kho.get(h["source"])
            meta.append(f"kho: <b>{n[0]:,}</b> dòng" if n else "kho: <b>0</b> dòng")
        if h.get("unit"):
            meta.append(f"{h['unit']} · {h['basis']}")
        if h.get("depth"):
            meta.append(f"sâu từ {h['depth']}")
        if h.get("vai_tro"):
            meta.append(f"<b>{h['vai_tro']}</b>")
        chips = "".join(f"<span class=f>{esc(t)}</span>" for t in v["truong"])
        mau = json.dumps(v["mau"], ensure_ascii=False, indent=1) if v["mau"] else "(không có mẫu)"
        goi = f'{v["method"]} {v["host"]}{v["path"]}'
        if v["params"]:
            goi += "\n" + json.dumps(v["params"], ensure_ascii=False)
        the.append(f"""
<details class="cua {cls}">
  <summary>
    <span class="ten">{esc(v['path'])}</span>
    <span class="badge {cls}">{nhan}</span>
    <span class="sot">{v['so_truong']} trường</span>
    <span class="host">{esc(v['host'])}</span>
    {'<span class="meta">' + ' · '.join(meta) + '</span>' if meta else ''}
  </summary>
  <div class="than">
    {'<p class="gc">' + esc(v['ghi_chu']) + '</p>' if v['ghi_chu'] else ''}
    <div class="nhan-nho">GỌI</div><pre class="goi">{esc(goi)}</pre>
    <div class="nhan-nho">TRƯỜNG ({v['so_truong']})</div><div class="fs">{chips or '<span class="f trong">không có</span>'}</div>
    <div class="nhan-nho">MẪU TRẢ VỀ — đo {v['do_luc']}</div><pre class="mau">{esc(mau)}</pre>
  </div>
</details>""")
    song = sum(1 for _, v in cua if v["ok"] and _ not in VO_LOI)
    khoi.append(f"""
<section>
  <h2>{nha} <span class="dem">{len(cua)} cửa · {song} sống</span></h2>
  <p class="mota">{mo_ta}</p>
  {''.join(the)}
</section>""")

tong = len(CUA)
song = sum(1 for k, v in CUA.items() if v["ok"] and k not in VO_LOI)

html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nguồn dữ liệu — PRJ Quantitative Investment</title>
<!-- SINH TU build_nguon.py — dung sua tay -->
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
  :root{{--bg:#0f172a;--pn:#111c33;--edge:#334155;--fg:#e2e8f0;--dim:#94a3b8;
        --cy:#22d3ee;--em:#34d399;--am:#fbbf24;--ro:#fb7185;--vi:#a78bfa}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--fg);
       font:13px/1.6 'JetBrains Mono','SF Mono',Consolas,monospace;padding:28px 20px 60px}}
  .wrap{{max-width:1180px;margin:0 auto}}
  h1{{font-size:20px;margin:0 0 6px}}
  .sub{{color:var(--dim);font-size:12px;margin:0 0 4px}}
  .tong{{color:var(--dim);font-size:12px;margin:0 0 26px}}
  .tong b{{color:var(--em)}}
  h2{{font-size:15px;margin:34px 0 4px;padding-bottom:7px;border-bottom:1px solid var(--edge)}}
  .dem{{color:var(--dim);font-weight:400;font-size:11px;margin-left:8px}}
  .mota{{color:var(--dim);font-size:11px;margin:0 0 12px}}
  details.cua{{background:var(--pn);border:1px solid var(--edge);border-left-width:3px;
              border-radius:7px;margin-bottom:7px}}
  details.dung{{border-left-color:var(--em)}}
  details.chua{{border-left-color:var(--am)}}
  details.hong{{border-left-color:var(--ro)}}
  details.khong{{border-left-color:#64748b}}
  summary{{cursor:pointer;padding:10px 13px;list-style:none;display:flex;
          align-items:center;gap:10px;flex-wrap:wrap}}
  summary::-webkit-details-marker{{display:none}}
  summary::before{{content:'▸';color:var(--dim);font-size:11px;transition:.15s}}
  details[open] summary::before{{transform:rotate(90deg)}}
  details[open] summary{{border-bottom:1px solid var(--edge)}}
  .ten{{font-weight:600;color:#fff}}
  .badge{{font-size:10px;padding:1px 7px;border-radius:99px;border:1px solid}}
  .badge.dung{{color:var(--em);border-color:var(--em)}}
  .badge.chua{{color:var(--am);border-color:var(--am)}}
  .badge.hong{{color:var(--ro);border-color:var(--ro)}}
  .badge.khong{{color:#94a3b8;border-color:#64748b}}
  .sot{{font-size:11px;color:var(--cy)}}
  .host,.meta{{font-size:10.5px;color:var(--dim)}}
  .meta{{margin-left:auto}}
  .than{{padding:12px 13px 15px}}
  .gc{{color:var(--am);font-size:11.5px;margin:0 0 12px}}
  .nhan-nho{{font-size:10px;color:var(--dim);letter-spacing:.09em;margin:13px 0 5px}}
  .nhan-nho:first-of-type{{margin-top:0}}
  pre{{background:#0b1220;border:1px solid var(--edge);border-radius:6px;
      padding:10px 12px;overflow-x:auto;font-size:11px;margin:0;color:#cbd5e1}}
  pre.goi{{color:var(--cy)}}
  .fs{{display:flex;flex-wrap:wrap;gap:5px}}
  .f{{background:rgba(167,139,250,.13);border:1px solid rgba(167,139,250,.4);
     color:#ddd6fe;border-radius:4px;padding:2px 7px;font-size:10.5px}}
  .f.trong{{background:none;border-color:var(--edge);color:var(--dim)}}
  footer{{margin-top:40px;color:var(--dim);font-size:10.5px;border-top:1px solid var(--edge);padding-top:14px}}
  @media(max-width:700px){{.meta{{margin-left:0;width:100%}}}}
</style>
</head>
<body><div class="wrap">
<h1>Nguồn dữ liệu — 4 nhà cung cấp</h1>
<p class="sub">PRJ Quantitative Investment · kiểm kê theo HOST, không theo endpoint</p>
<p class="tong"><b>{tong}</b> cửa · <b>{song}</b> gọi ra dữ liệu · đo thật ngày {date.today()} —
mỗi cửa dưới đây đều được gọi một lần để lấy tên trường và mẫu trả về. Bấm để mở.</p>
{''.join(khoi)}
<footer>
Trường và mẫu lấy từ lời gọi THẬT, không chép từ tài liệu. Trạng thái lấy từ
<code>meta.vendor_door</code> và <code>meta.source_contract</code> của quant_v2.<br>
Sinh bởi <code>build_nguon.py</code> · dữ liệu thô ở <code>mau-tai/cac-cua.json</code>
</footer>
</div></body></html>"""

(HERE / "nguon-du-lieu.html").write_text(html, encoding="utf-8")
print(f"nguon-du-lieu.html — {len(html):,} ký tự · {tong} cửa · {song} sống")
for nha, _ in NHA:
    n = sum(1 for v in CUA.values() if v["vendor"] == nha)
    print(f"  {nha:9s} {n} cửa")
