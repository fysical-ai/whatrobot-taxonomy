"""Generate docs/ — a single static explorer page fed by dist/, hostable on GitHub Pages.

Prose content is CC BY 4.0; this generator is MIT.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import DIST, ROOT, version
from .loader import Taxonomy

DOCS = ROOT / "docs"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>whatrobot taxonomy __VERSION__</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e3e3e3;--acc:#0b5fff;--chip:#f3f4f6}
@media(prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee;--muted:#999;--line:#2a2a2a;--acc:#6ea0ff;--chip:#1e1e1e}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:16px;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px;margin:0}header small{color:var(--muted)}
main{display:grid;grid-template-columns:320px 1fr;min-height:calc(100vh - 60px)}
@media(max-width:800px){main{grid-template-columns:1fr}}
nav{border-right:1px solid var(--line);padding:16px;overflow:auto}
nav ul{list-style:none;margin:0;padding-left:14px}nav>ul{padding:0}
nav a{color:var(--fg);text-decoration:none;display:block;padding:2px 4px;border-radius:4px}
nav a:hover,nav a.on{background:var(--chip);color:var(--acc)}
section{padding:16px 24px;max-width:900px}
.crumbs{color:var(--muted);font-size:13px}.id{font-family:ui-monospace,monospace;color:var(--muted);font-size:13px}
.chip{display:inline-block;background:var(--chip);border-radius:12px;padding:1px 10px;margin:2px;font-size:13px}
table{border-collapse:collapse;width:100%;margin:12px 0}td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}
select{font:inherit;padding:4px}
</style></head><body>
<header><h1>whatrobot taxonomy</h1><small>__VERSION__ · data CC BY 4.0 · <a href="https://github.com/fysical-ai/whatrobot-taxonomy">GitHub</a> · <a href="design.html">Design notes</a></small>
<label>Locale <select id="loc">__LOCALES__</select></label></header>
<main><nav id="tree"></nav><section id="detail"><p>Select a category.</p></section></main>
<script>
const DATA=__DATA__;let locale='en';
function cats(){return DATA[locale].categories.verticals.flatMap(v=>v.categories)}
function attrs(){return Object.fromEntries(DATA[locale].attributes.attributes.map(a=>[a.friendly_id,a]))}
function tree(){const c=cats(),by=Object.fromEntries(c.map(x=>[x.id,x]));const roots=c.filter(x=>!x.parent_id);
 const li=x=>`<li><a href="#${x.id.split('/').pop()}" data-id="${x.id}">${x.name}</a>${x.children.length?'<ul>'+x.children.map(ch=>li(by[ch.id])).join('')+'</ul>':''}</li>`;
 document.getElementById('tree').innerHTML='<ul>'+roots.map(li).join('')+'</ul>';}
function show(id){const c=cats().find(x=>x.id===id);if(!c)return;const A=attrs();
 document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.dataset.id===id));
 const rows=c.attributes.map(a=>{const d=A[a.friendly_id]||{};const vals=(d.values||[]).map(v=>`<span class="chip">${v.name}</span>`).join('');
   return `<tr><td><code>${a.friendly_id}</code><br><small>${d.name||''}</small></td><td>${d.type||''}${d.multi?'[]':''}${d.unit?' ('+d.unit+')':''}</td><td>${d.question||''}${vals?'<br>'+vals:''}</td></tr>`}).join('');
 document.getElementById('detail').innerHTML=`<div class="crumbs">${c.full_name}</div><h2>${c.name} <span class="id">${c.id.split('/').pop()} · ${c.friendly_id}</span></h2>
 <p>${c.description}</p><p><b>Inclusion rule.</b> ${c.inclusion_rule}</p>
 ${c.aliases.length?'<p><b>Aliases.</b> '+c.aliases.map(a=>`<span class="chip">${a}</span>`).join('')+'</p>':''}
 ${c.examples.length?'<p><b>Examples.</b> '+c.examples.map(a=>`<code>${a}</code>`).join(', ')+'</p>':''}
 <h3>Attributes (${c.attributes.length}, incl. inherited)</h3><table><tr><th>Attribute</th><th>Type</th><th>Question / values</th></tr>${rows}</table>`;}
document.getElementById('loc').onchange=e=>{locale=e.target.value;tree();route()};
function route(){const h=location.hash.slice(1);if(h)show('gid://whatrobot/TaxonomyCategory/'+h)}
window.onhashchange=route;tree();route();
</script></body></html>
"""


def build_docs(tx: Taxonomy) -> Path:
    locales = ["en", *tx.locales]
    data = {}
    for loc in locales:
        data[loc] = {
            "categories": json.loads((DIST / loc / "categories.json").read_text(encoding="utf-8")),
            "attributes": json.loads((DIST / loc / "attributes.json").read_text(encoding="utf-8")),
        }
    DOCS.mkdir(exist_ok=True)
    html = (
        PAGE.replace("__VERSION__", version())
        .replace("__LOCALES__", "".join(f'<option value="{l}">{l}</option>' for l in locales))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False))
    )
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    # copy dist alongside for direct download from Pages
    if (DOCS / "dist").exists():
        shutil.rmtree(DOCS / "dist")
    shutil.copytree(DIST, DOCS / "dist")
    return DOCS / "index.html"
