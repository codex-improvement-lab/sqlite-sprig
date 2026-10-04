"""Generate an editable SVG card from the authored demo's actual counts."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / 'docs/index.html').read_text(encoding='utf-8')
diagram = re.search(r'<svg id="branch".*?>(.*?)</svg>', page, re.S).group(1)
diagram = re.sub(r'<text class="diagram-note".*?</text>', '', diagram, flags=re.S)
data = json.loads((ROOT / 'docs/data/demo.json').read_text(encoding='utf-8'))
assert data['sourceRows'] == 24 and data['cases']['103']['totalRows'] == 11
style = '''
text{font-family:Segoe UI,Arial,sans-serif;fill:#19252b}
.traces{stroke:#95a299;stroke-width:1.15;stroke-linecap:round;stroke-linejoin:round}
.column-label{font-size:9px;letter-spacing:1.1px;fill:#788076}
.node rect{fill:#fafbf6;stroke:#c7d0c5;stroke-width:1}
.node-label{font-size:9px;letter-spacing:1px;fill:#6b796c}
.node-count{font-size:12px;text-anchor:end;fill:#52664f}
.node-value{font-size:14px;fill:#354634}
.root rect{fill:url(#paper);stroke:#cd8c69}
.root-label{font-size:9px;letter-spacing:.8px;fill:#7f4b32}
.root-id{font-size:39px;letter-spacing:-1.8px;font-weight:500;fill:#4a3427}
.root-state{font-size:10px;fill:#7f4b32}
.child rect{fill:#f5f7f5;stroke:#becbc8}
.child .node-label{fill:#647a78}
.child-count{font-size:26px;fill:#3d5856}
.child-detail{font-size:11px;fill:#738481}
.diagram-note{font-size:10px;fill:#7a8079}
'''
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="760" viewBox="0 0 1280 760" role="img" aria-label="SQLite Sprig: one record with its context. An authored example retains 11 of 24 rows.">
<style>{style}</style><rect width="1280" height="760" fill="#f2f0ea"/>
<g transform="translate(64 32)" fill="none" stroke="#b84b29" stroke-width="1.6"><path d="M18 36V9M18 24C7 24 5 17 5 10c8 0 13 5 13 14ZM18 16C18 7 24 3 31 3c0 8-5 13-13 13Z"/></g>
<text x="113" y="61" font-size="25">SQLite <tspan font-weight="600">Sprig</tspan></text>
<text x="1216" y="59" font-size="12" text-anchor="end" fill="#6b756d">LOCAL SQLITE · ALPHA 0.1</text>
<path d="M64 96H1216" stroke="#d5d7cf"/>
<text x="64" y="184" font-size="11" letter-spacing="1.5" fill="#626b6a">A BRANCH YOU CAN WORK WITH</text>
<text x="60" y="274" font-size="70" letter-spacing="-3.5">One record.</text>
<text x="60" y="347" font-size="70" letter-spacing="-3.5">With its</text>
<text x="60" y="420" font-size="70" letter-spacing="-3.5" style="fill:#b84b29">context.</text>
<text x="64" y="475" font-size="17" fill="#626b6a">Keep the relationships.</text>
<text x="64" y="503" font-size="17" fill="#626b6a">Keep the ordinary schema.</text>
<text x="64" y="563" font-size="34" letter-spacing="-1">24 <tspan font-size="22" fill="#829080">→</tspan> 11 <tspan font-size="14" letter-spacing="0">rows</tspan></text>
<svg x="455" y="131" width="760" height="570" viewBox="0 0 640 480">{diagram}</svg>
<text x="495" y="626" font-size="10" fill="#7a8079">Required parents stay. Their other branches don't.</text>
<path d="M64 643H1216" stroke="#d5d7cf"/>
<text x="64" y="677" font-family="Consolas,monospace" font-size="14">python sqlite_sprig.py board.sqlite3 --root cards --where "id=103" --out card-103.sqlite3</text>
<text x="64" y="724" font-size="11" fill="#626b6a">Authored example · copies actual data · no masking</text>
<text x="1216" y="724" font-size="11" text-anchor="end" fill="#626b6a">github.com/codex-improvement-lab/sqlite-sprig</text>
</svg>'''
(ROOT / 'docs/demo.svg').write_text('\n'.join(line.rstrip() for line in svg.splitlines()) + '\n', encoding='utf-8')
print('docs/demo.svg')
