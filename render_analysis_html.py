"""Render the recurring BGF structure JSON report as an interactive HTML page."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def render_report(report: dict[str, object]) -> str:
    """Return a self-contained interactive HTML document."""

    payload = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
    # A script element is raw text in HTML; prevent data from closing it.
    payload = payload.replace("</", "<\\/")
    grammar_count = int(report["grammar_count"])
    production_count = int(report["production_count"])
    subtree_count = len(report["subtrees"])
    motif_count = len(report["motifs"])

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BGF recurring structural evidence</title>
<style>
:root {{ color-scheme: light; --ink:#17212b; --muted:#5d6874; --line:#d8dee5;
  --paper:#fff; --wash:#f4f7f9; --accent:#315e75; --keyword:#e8f2f7;
  --punct:#f7eee4; }}
* {{ box-sizing:border-box }}
body {{ margin:0; color:var(--ink); background:var(--wash); font:15px/1.45 system-ui,sans-serif }}
main {{ max-width:1500px; margin:auto; padding:28px }}
h1 {{ margin:0 0 6px; font-size:30px }} h2 {{ margin-top:0 }}
.lede,.muted {{ color:var(--muted) }}
.summary {{ display:grid; grid-template-columns:repeat(4,minmax(130px,1fr)); gap:12px; margin:22px 0 }}
.stat,.panel,.card {{ background:var(--paper); border:1px solid var(--line); border-radius:9px }}
.stat {{ padding:16px }} .stat strong {{ display:block; font-size:25px }}
.panel {{ padding:20px; margin:16px 0 }}
.guide code,.shape {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace }}
.guide table {{ border-collapse:collapse; width:100% }}
th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:8px; vertical-align:top }}
.controls {{ display:grid; grid-template-columns:2fr repeat(3,1fr); gap:10px }}
input,select,button {{ width:100%; padding:9px; border:1px solid #b9c2ca; border-radius:6px; background:white }}
button {{ cursor:pointer }} .tabs {{ display:flex; gap:8px; margin:16px 0 }} .tabs button {{ width:auto }}
.tabs button.active {{ color:white; background:var(--accent); border-color:var(--accent) }}
.shape-link {{ width:auto; padding:2px 4px; border:0; color:var(--accent); background:transparent;
  text-align:left; text-decoration:underline; font:inherit; overflow-wrap:anywhere }}
.shape-link:hover {{ color:#173d50; background:var(--keyword) }}
.resultline {{ display:flex; justify-content:space-between; margin:12px 0; color:var(--muted) }}
.card {{ margin:10px 0; overflow:hidden }} .card summary {{ cursor:pointer; padding:14px; list-style:none }}
.card summary::-webkit-details-marker {{ display:none }}
.headline {{ display:grid; grid-template-columns:90px 115px minmax(0,1fr); gap:10px; align-items:start }}
.number {{ font-variant-numeric:tabular-nums }} .shape {{ overflow-wrap:anywhere }}
.relation {{ color:var(--accent); font-size:13px; margin-bottom:5px }}
.details {{ border-top:1px solid var(--line); padding:14px; background:#fbfcfd }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 }}
.chip {{ border-radius:12px; padding:2px 8px; font-family:ui-monospace,monospace; font-size:12px }}
.keyword {{ background:var(--keyword) }} .punctuation {{ background:var(--punct) }}
.lists {{ display:grid; grid-template-columns:1fr 1fr; gap:18px }}
pre {{ white-space:pre-wrap; overflow-wrap:anywhere; background:#eef2f4; padding:9px; border-radius:5px }}
.pager {{ display:flex; gap:10px; align-items:center; justify-content:center; margin:18px }}
.pager button {{ width:100px }}
@media(max-width:800px) {{ main{{padding:14px}} .summary{{grid-template-columns:1fr 1fr}}
  .controls,.headline,.lists{{grid-template-columns:1fr}} }}
</style>
</head>
<body><main>
<h1>BGF recurring structural evidence</h1>
<p class="lede">A navigable view of recurring production subtrees and selected positional relationships across the grammar corpus.</p>
<section class="summary">
 <div class="stat"><strong>{grammar_count:,}</strong>grammar files</div>
 <div class="stat"><strong>{production_count:,}</strong>productions</div>
 <div class="stat"><strong>{subtree_count:,}</strong>recurring subtrees</div>
 <div class="stat"><strong>{motif_count:,}</strong>structural patterns</div>
</section>
<section class="panel guide">
<h2>How to read this report</h2>
<p><code>N</code> means any nonterminal; its original name is ignored. Quoted strings are exact terminals.
<code>sequence</code>, <code>choice</code>, <code>optional</code>, <code>star</code>, <code>plus</code>,
<code>sepliststar</code>, and <code>seplistplus</code> correspond to BGF constructs. Selector annotations are omitted.</p>
<table><thead><tr><th>Field</th><th>Interpretation</th></tr></thead><tbody>
<tr><td>Frequency</td><td>Number of occurrences. Multiple occurrences may come from one production.</td></tr>
<tr><td>Languages</td><td>Number of distinct grammar files containing the evidence. Expand a row for their names.</td></tr>
<tr><td>Productions</td><td>Number of distinct source productions containing it. Expand a row for identifiers and examples.</td></tr>
<tr><td>Terminal class</td><td>Identity is always preserved. Identifier-shaped text is classified as keyword; everything else as punctuation.</td></tr>
</tbody></table>
<p><strong>Subtrees</strong> are all recurring AST fragments. <strong>Structural patterns</strong> are the requested positional observations such as
<code>sequence(T, N)</code>, where <code>T</code> is an exact terminal shown in the shape. These are deliberately structural descriptions, not semantic names.</p>
</section>
<div class="tabs"><button id="subtreesTab" class="active">Recurring subtrees</button><button id="motifsTab">Structural patterns</button></div>
<section class="panel">
 <div class="controls">
  <input id="search" type="search" placeholder="Search shapes, terminals, languages, productions…">
  <input id="minFrequency" type="number" min="2" value="2" title="Minimum occurrence frequency">
  <input id="minLanguages" type="number" min="1" value="1" title="Minimum grammar-file count">
  <select id="relation"><option value="">All structural relations</option></select>
 </div>
 <div class="controls" style="margin-top:10px">
  <select id="terminalClass"><option value="">Any terminal content</option><option value="present" selected>Has at least one terminal</option><option value="keyword">Has keyword</option><option value="punctuation">Has punctuation</option><option value="none">Has no terminal</option></select>
  <select id="sort"><option value="frequency">Sort by frequency</option><option value="languages">Sort by languages</option><option value="productions">Sort by productions</option><option value="shape">Sort by shape</option></select>
  <select id="pageSize"><option>25</option><option selected>50</option><option>100</option><option>250</option></select>
  <button id="reset">Reset filters</button>
 </div>
</section>
<div class="resultline"><span id="resultCount"></span><span id="pageLabel"></span></div>
<section id="results"></section>
<div class="pager"><button id="previous">Previous</button><button id="next">Next</button></div>
</main>
<script id="reportData" type="application/json">{payload}</script>
<script>
const report=JSON.parse(document.getElementById('reportData').textContent);
const $=id=>document.getElementById(id); let section='subtrees', page=0, exactShape=null;
const relations=[...new Set(report.motifs.map(x=>x.relation))].sort();
for(const value of relations){{const option=document.createElement('option');option.value=value;option.textContent=value;$('relation').append(option)}}
const escapeHTML=value=>String(value).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
function filtered(){{
 const query=$('search').value.toLocaleLowerCase(), minF=+$('minFrequency').value||0, minL=+$('minLanguages').value||0;
 const tc=$('terminalClass').value, relation=$('relation').value;
 let rows=report[section].filter(x=>x.frequency>=minF&&x.language_count>=minL&&(!relation||x.relation===relation));
 if(exactShape!==null) rows=rows.filter(x=>x.shape===exactShape);
 if(tc) rows=rows.filter(x=>tc==='present'?x.terminals.length>0:tc==='none'?!x.terminals.length:x.terminals.some(t=>t.class===tc));
 if(query) rows=rows.filter(x=>[x.shape,x.relation||'',...x.languages,...x.productions,...x.terminals.map(t=>t.value)].join('\\n').toLocaleLowerCase().includes(query));
 const sort=$('sort').value; rows.sort((a,b)=>sort==='shape'?a.shape.localeCompare(b.shape):(b[sort==='languages'?'language_count':sort==='productions'?'production_count':'frequency']-a[sort==='languages'?'language_count':sort==='productions'?'production_count':'frequency']||a.shape.localeCompare(b.shape)));
 return rows;
}}
function render(){{
 const rows=filtered(), size=+$('pageSize').value, pages=Math.max(1,Math.ceil(rows.length/size)); page=Math.min(page,pages-1);
 $('resultCount').textContent=`${{rows.length.toLocaleString()}} matching records`;$('pageLabel').textContent=`Page ${{page+1}} of ${{pages}}`;
 $('previous').disabled=page===0;$('next').disabled=page>=pages-1;$('relation').disabled=section==='subtrees';
 $('results').innerHTML=rows.slice(page*size,(page+1)*size).map(card).join('');
}}
function card(x){{
 const chips=x.terminals.length?x.terminals.map(t=>`<span class="chip ${{t.class}}">${{escapeHTML(JSON.stringify(t.value))}} · ${{t.class}}</span>`).join(''):'<span class="muted">No terminal in this shape</span>';
 const examples=x.examples.map(e=>`<p><span class="muted">${{escapeHTML(e.language)}} · ${{escapeHTML(e.production)}}</span></p><pre>${{escapeHTML(e.text)}}</pre>`).join('');
 const languages=x.languages.map(escapeHTML).join(', '), productions=x.productions.map(escapeHTML).join('\\n');
 const parents=(x.containing_structures||[]).map(p=>`<tr><td>${{p.frequency.toLocaleString()}}</td><td>${{p.language_count.toLocaleString()}}</td><td>${{p.production_count.toLocaleString()}}</td><td class="shape"><button class="shape-link" data-shape="${{escapeHTML(p.shape)}}" title="Open this exact recurring subtree">${{escapeHTML(p.shape)}}</button></td></tr>`).join('');
 const containing=x.containing_structures===undefined?'':`<h3>Recurring containing structures</h3>${{parents?`<p class="muted">Immediate parent shapes containing this subtree. Click a shape to open its exact recurring-subtree record.</p><table><thead><tr><th>Occurrences</th><th>Languages</th><th>Productions</th><th>Containing shape</th></tr></thead><tbody>${{parents}}</tbody></table>`:'<p class="muted">No recurring immediate containing structure met the frequency threshold.</p>'}}`;
 return `<details class="card"><summary><div class="headline"><div><strong class="number">${{x.frequency.toLocaleString()}}</strong><br><span class="muted">occurrences</span></div><div><strong>${{x.language_count.toLocaleString()}}</strong> languages<br><strong>${{x.production_count.toLocaleString()}}</strong> productions</div><div>${{x.relation?`<div class="relation">${{escapeHTML(x.relation)}}</div>`:''}}<div class="shape">${{escapeHTML(x.shape)}}</div></div></div></summary><div class="details"><h3>Exact terminals</h3><div class="chips">${{chips}}</div>${{containing}}<div class="lists"><div><h3>Grammar files</h3><p>${{languages||'None'}}</p><h3>Representative examples</h3>${{examples}}</div><div><h3>Source productions</h3><pre>${{productions}}</pre></div></div></div></details>`;
}}
function switchSection(value){{section=value;page=0;$('subtreesTab').classList.toggle('active',value==='subtrees');$('motifsTab').classList.toggle('active',value==='motifs');render()}}
$('subtreesTab').onclick=()=>{{exactShape=null;switchSection('subtrees')}};$('motifsTab').onclick=()=>{{exactShape=null;switchSection('motifs')}};
for(const id of ['search','minFrequency','minLanguages','relation','terminalClass','sort','pageSize']) $(id).addEventListener('input',()=>{{exactShape=null;page=0;render()}});
$('results').addEventListener('click',event=>{{
 const link=event.target.closest('.shape-link'); if(!link)return;
 exactShape=link.dataset.shape;$('search').value=exactShape;$('minFrequency').value=2;$('minLanguages').value=1;$('relation').value='';$('terminalClass').value='';
 switchSection('subtrees');scrollTo(0,document.querySelector('.tabs').offsetTop);
}});
$('previous').onclick=()=>{{page--;render();scrollTo(0,document.querySelector('.tabs').offsetTop)}};$('next').onclick=()=>{{page++;render();scrollTo(0,document.querySelector('.tabs').offsetTop)}};
$('reset').onclick=()=>{{exactShape=null;$('search').value='';$('minFrequency').value=2;$('minLanguages').value=1;$('relation').value='';$('terminalClass').value='present';$('sort').value='frequency';$('pageSize').value=50;page=0;render()}};
render();
</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="recurring-structures JSON file")
    parser.add_argument("output", type=Path, help="output HTML file")
    arguments = parser.parse_args()
    report = json.loads(arguments.input.read_text(encoding="utf-8"))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(render_report(report), encoding="utf-8")
    print(f"Wrote interactive report to {arguments.output}")


if __name__ == "__main__":
    main()
