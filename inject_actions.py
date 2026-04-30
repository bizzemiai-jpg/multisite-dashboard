"""build_dashboard.py の publish 直前に呼ぶ。actions.json + gsc_data.json を読んで
  index.html に「次にやるべきこと」と「検索順位 TOP」セクションを再注入する（冪等）。"""
import re, json, pathlib

ROOT = pathlib.Path(__file__).parent
html_path = ROOT / "index.html"
actions = json.loads((ROOT / "actions.json").read_text(encoding="utf-8"))
gsc_path = ROOT / "gsc_data.json"
gsc = json.loads(gsc_path.read_text(encoding="utf-8")) if gsc_path.is_file() else {"sites": {}}
asp_path = ROOT / "asp_status.json"
asp = json.loads(asp_path.read_text(encoding="utf-8")) if asp_path.is_file() else {"asps": {}}

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
.gsc-top { margin:12px 0 16px; padding:10px 12px; background:#f0f9ff; border-left:4px solid #0ea5e9; border-radius:6px; }
.gsc-top h3 { margin-top:0; color:#0369a1; border-bottom-color:#bae6fd; }
.gsc-top a.q { color:#0369a1; text-decoration:none; }
.gsc-top a.q:hover { text-decoration:underline; }
.asp { font-size:12px; margin:0; padding:0; list-style:none; }
.asp li { display:grid; grid-template-columns:60px 1fr 70px; gap:8px; padding:6px 8px; border-bottom:1px solid #e2e8f0; align-items:center; }
.asp li:nth-child(odd) { background:#f8fafc; }
.asp .badge { font-size:11px; font-weight:700; padding:2px 6px; border-radius:4px; text-align:center; }
.asp .badge.approved { background:#dcfce7; color:#166534; }
.asp .badge.pending  { background:#fef9c3; color:#854d0e; }
.asp .badge.rejected { background:#fee2e2; color:#991b1b; }
.asp .subj { color:#1e293b; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.asp .d { color:#64748b; font-size:11px; text-align:right; font-variant-numeric:tabular-nums; }
.asp-name { font-weight:700; font-size:12px; color:#475569; margin:8px 0 2px; }
"""

html = html_path.read_text(encoding="utf-8")
html = re.sub(r'<h3>🎯 次にやるべきこと</h3><ul class="actions">.*?</ul>', '', html, flags=re.DOTALL)
html = re.sub(r'<h3>🔍 検索順位[^<]*</h3>.*?(?=<div class="status">|<h3>|<div class="kpis">|$)', '', html, flags=re.DOTALL)
html = re.sub(r'<div class="gsc-top">.*?</div><!--/gsc-top-->', '', html, flags=re.DOTALL)
html = re.sub(r'<h3>🤝 アフィリ申請状況</h3>.*?(?=<div class="status">|<h3>|$)', '', html, flags=re.DOTALL)
if ".actions {" not in html:
    html = html.replace("</style>", EXTRA_CSS + "</style>", 1)

def render_actions(items):
    lis = []
    for icon, text in items:
        cls = ' class="urgent"' if "🔥" in icon else ""
        lis.append(f'<li{cls}><span class="icon">{icon}</span>{text}</li>')
    return f'<h3>🎯 次にやるべきこと</h3><ul class="actions">{"".join(lis)}</ul>'

def render_gsc_top(site_key):
    """100位以内のクエリをカード最上段に表示（順位昇順）"""
    gsc_url = GSC_KEYS.get(site_key)
    period = gsc.get("period", "")
    site_data = gsc.get("sites", {}).get(gsc_url, {})
    all_rows = site_data.get("rows", [])
    rows = sorted([r for r in all_rows if r.get("position", 999) <= 100], key=lambda r: r["position"])
    if not rows:
        return ('<div class="gsc-top"><h3>🔍 検索順位（100位以内）</h3>'
                '<div class="gsc-empty">100位以内の記事なし</div></div><!--/gsc-top-->')
    lis = []
    for r in rows:
        pos = r["position"]
        cls = "good" if pos <= 10 else ("mid" if pos <= 30 else "")
        q = r["query"].replace("<","&lt;").replace(">","&gt;")
        page = r.get("page", "")
        lis.append(
            f'<li><a class="q" href="{page}" target="_blank" title="{q}">{q}</a>'
            f'<span class="imp">{r["impressions"]}</span>'
            f'<span class="pos {cls}">{pos}</span></li>'
        )
    return (f'<div class="gsc-top"><h3>🔍 検索順位（100位以内・{len(rows)}件）</h3>'
            f'<ul class="gsc">{"".join(lis)}</ul>'
            f'<p class="gsc-period">{period} ・ クエリ / 表示 / 順位</p></div><!--/gsc-top-->')

def fmt_date(s):
    # "Sat, 18 Apr 2026 09:32:42" → "4/18"
    import re as _re
    m = _re.search(r"(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", s)
    if not m: return s[:10]
    months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    return f"{months[m.group(2)]}/{int(m.group(1))}"

def render_asp(site_key):
    """サイトに紐づくASPごとの最新ステータスを表示"""
    blocks = []
    has_any = False
    for asp_name, asp_info in asp.get("asps", {}).items():
        if site_key not in asp_info.get("site_keys", []):
            continue
        items = asp_info.get("items", [])[:3]  # 各ASP最新3件
        if not items:
            continue
        has_any = True
        lis = []
        for it in items:
            st = it["status"]
            badge_label = {"approved":"承認","pending":"審査中","rejected":"却下"}.get(st, st)
            subj = it["subject"].replace("<","&lt;").replace(">","&gt;")
            lis.append(
                f'<li><span class="badge {st}">{badge_label}</span>'
                f'<span class="subj" title="{subj}">{subj}</span>'
                f'<span class="d">{fmt_date(it["date"])}</span></li>'
            )
        blocks.append(f'<div class="asp-name">{asp_name}</div><ul class="asp">{"".join(lis)}</ul>')
    if not has_any:
        return ('<h3>🤝 アフィリ申請状況</h3>'
                '<div class="gsc-empty">該当メールなし（Gmail検索: ASPドメインから直近60日）</div>')
    fetched = asp.get("fetched_at", "")[:16].replace("T", " ")
    return (f'<h3>🤝 アフィリ申請状況</h3>{"".join(blocks)}'
            f'<p class="gsc-period">Gmail取得: {fetched}</p>')

for site in actions:
    # 1) GSC100位以内をカード最上段（card-head直後・kpisの直前）に注入
    top_pat = re.compile(
        r'(' + re.escape(site) + r' ↗</a>\s*</div>)\s*(<div class="kpis">)',
        re.DOTALL,
    )
    top_block = render_gsc_top(site)
    html, n_top = top_pat.subn(
        lambda m, b=top_block: m.group(1) + b + m.group(2), html, count=1
    )
    # 2) アクション・ASPはカード末尾（status直前）に注入
    pat = re.compile(r'(' + re.escape(site) + r' ↗</a>.*?)(<div class="status">)', re.DOTALL)
    block = render_actions(actions[site]) + render_asp(site)
    html, n = pat.subn(lambda m, b=block: m.group(1) + b + m.group(2), html, count=1)
    print(f"{site}: top_injected={n_top} bottom_injected={n}")

html_path.write_text(html, encoding="utf-8")
print("[OK] actions + GSC injected into index.html")
