"""build_dashboard.py の publish 直前に呼ぶ。actions.json を読んで index.html に「次にやるべきこと」セクションを再注入する（冪等）。"""
import re, json, pathlib, sys

ROOT = pathlib.Path(__file__).parent
html_path = ROOT / "index.html"
actions = json.loads((ROOT / "actions.json").read_text(encoding="utf-8"))

EXTRA_CSS = """
.actions { list-style:none; padding:0; margin:0; font-size:13px; }
.actions li { padding:8px 10px; margin:6px 0; background:#fef9c3; border-left:4px solid #facc15; border-radius:4px; line-height:1.5; }
.actions li.urgent { background:#fee2e2; border-left-color:#ef4444; }
.actions .icon { display:inline-block; margin-right:6px; }
"""

html = html_path.read_text(encoding="utf-8")
# remove old injected blocks (idempotent)
html = re.sub(r'<h3>🎯 次にやるべきこと</h3><ul class="actions">.*?</ul>', '', html, flags=re.DOTALL)
if ".actions {" not in html:
    html = html.replace("</style>", EXTRA_CSS + "</style>", 1)

def render(items):
    lis = []
    for icon, text in items:
        cls = ' class="urgent"' if "🔥" in icon else ""
        lis.append(f'<li{cls}><span class="icon">{icon}</span>{text}</li>')
    return f'<h3>🎯 次にやるべきこと</h3><ul class="actions">{"".join(lis)}</ul>'

for site, items in actions.items():
    pat = re.compile(r'(' + re.escape(site) + r' ↗</a>.*?)(<div class="status">)', re.DOTALL)
    block = render(items)
    html, n = pat.subn(lambda m, b=block: m.group(1) + b + m.group(2), html, count=1)
    print(f"{site}: injected={n}")

html_path.write_text(html, encoding="utf-8")
print("[OK] actions injected into index.html")
