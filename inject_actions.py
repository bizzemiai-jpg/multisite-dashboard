"""build_dashboard.py の publish 直前に呼ぶ。actions.json + gsc_data.json を読んで
  index.html に「次にやるべきこと」と「検索順位 TOP」セクションを再注入する（冪等）。"""
import re, json, pathlib

ROOT = pathlib.Path(__file__).parent
html_path = ROOT / "index.html"
actions = json.loads((ROOT / "actions.json").read_text(encoding="utf-8"))
gsc_path = ROOT / "gsc_data.json"
gsc = json.loads(gsc_path.read_text(encoding="utf-8")) if gsc_path.is_file() else {"sites": {}}

GSC_KEYS = {
    "biz-english-ai.com": "https://biz-english-ai.com/",
    "ai-gyomu.jp":        "https://ai-gyomu.jp/",
    "side-invest.com":    "https://side-invest.com/",
}

EXTRA_CSS = """
.actions { list-style:none; padding:0; margin:0; font-size:13px; }
.actions li { padding:8px 10px; margin:6px 0; background:#fef9c3; border-left:4px solid #facc15; border-radius:4px; line-height:1.5; }
.actions li.urgent { background:#fee2e2; border-left-color:#ef4444; }
.actions .icon { display:inline-block; margin-right:6px; }
.gsc { font-size:12px; margin:0; padding:0; list-style:none; }
.gsc li { display:grid; grid-template-columns:1fr 50px 50px; gap:8px; padding:6px 8px; border-bottom:1px solid #e2e8f0; align-items:center; }
.gsc li:nth-child(odd) { background:#f8fafc; }
.gsc .q { font-weight:600; color:#1e293b; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.gsc .imp { color:#64748b; text-align:right; font-variant-numeric:tabular-nums; }
.gsc .pos { color:#0f172a; text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }
.gsc .pos.good { color:#16a34a; }
.gsc .pos.mid { color:#ca8a04; }
.gsc-empty { color:#94a3b8; padding:8px; font-size:12px; }
.gsc-period { font-size:11px; color:#94a3b8; margin:4px 0 0; text-align:right; }
"""

html = html_path.read_text(encoding="utf-8")
html = re.sub(r'<h3>🎯 次にやるべきこと</h3><ul class="actions">.*?</ul>', '', html, flags=re.DOTALL)
html = re.sub(r'<h3>🔍 検索順位 TOP5</h3>.*?(?=<div class="status">|<h3>|$)', '', html, flags=re.DOTALL)
if ".actions {" not in html:
    html = html.replace("</style>", EXTRA_CSS + "</style>", 1)

def render_actions(items):
    lis = []
    for icon, text in items:
        cls = ' class="urgent"' if "🔥" in icon else ""
        lis.append(f'<li{cls}><span class="icon">{icon}</span>{text}</li>')
    return f'<h3>🎯 次にやるべきこと</h3><ul class="actions">{"".join(lis)}</ul>'

def render_gsc(site_key):
    gsc_url = GSC_KEYS.get(site_key)
    period = gsc.get("period", "")
    site_data = gsc.get("sites", {}).get(gsc_url, {})
    rows = site_data.get("rows", [])[:5]
    if not rows:
        return ('<h3>🔍 検索順位 TOP5</h3>'
                '<div class="gsc-empty">データ蓄積中（GSC所有権確認後 1〜2日で反映）</div>')
    lis = []
    for r in rows:
        pos = r["position"]
        cls = "good" if pos <= 10 else ("mid" if pos <= 30 else "")
        q = r["query"].replace("<","&lt;").replace(">","&gt;")
        lis.append(
            f'<li><span class="q" title="{q}">{q}</span>'
            f'<span class="imp">{r["impressions"]}</span>'
            f'<span class="pos {cls}">{pos}</span></li>'
        )
    return (f'<h3>🔍 検索順位 TOP5</h3><ul class="gsc">{"".join(lis)}</ul>'
            f'<p class="gsc-period">{period} ・ クエリ / 表示回数 / 順位</p>')

for site in actions:
    pat = re.compile(r'(' + re.escape(site) + r' ↗</a>.*?)(<div class="status">)', re.DOTALL)
    block = render_actions(actions[site]) + render_gsc(site)
    html, n = pat.subn(lambda m, b=block: m.group(1) + b + m.group(2), html, count=1)
    print(f"{site}: injected={n}")

html_path.write_text(html, encoding="utf-8")
print("[OK] actions + GSC injected into index.html")
