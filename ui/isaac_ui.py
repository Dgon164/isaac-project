"""
ISAAC UI — one file, stdlib only. A human console for a live mind.

    python isaac_ui.py          then open  http://127.0.0.1:8674

Three panels: CONVERSE (teach / observe / ask), DISCOVER (paste a table,
get a verdict card: equation, scope, rivals + probes; apply laws),
REMEMBER (search the findings ledger; save / load / new / fork minds).
"""
import io
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from isaac import Isaac, tokenize

MINDS = Path(__file__).resolve().parents[1] / "data" / "minds"
MINDS.mkdir(parents=True, exist_ok=True)
LEDGER = Path(__file__).resolve().parents[1] / "data" / "findings.jsonl"

STATE = {"isaac": Isaac(), "name": "unsaved mind"}
STATE["isaac"].ledger_path = str(LEDGER)
LOCK = threading.Lock()


def parse_table(text, target):
    rows = [r for r in text.strip().splitlines() if r.strip()]
    sep = "," if "," in rows[0] else None
    head = [h.strip() for h in rows[0].split(sep)]
    data = [[c.strip() for c in r.split(sep)] for r in rows[1:]]
    cols = {h: [] for h in head}
    for r in data:
        for h, v in zip(head, r):
            cols[h].append(float(v))
    if target not in cols:
        target = head[-1]
    y = np.array(cols.pop(target))
    names = list(cols)
    X = np.column_stack([cols[h] for h in names])
    return X, y, names, target


def api(handler, body):
    isaac = STATE["isaac"]
    p = handler.path.split("?")[0]
    if p == "/api/status":
        laws = sorted(n for n in isaac.net.get_doors("law", tag="law"))
        return dict(mind=STATE["name"], nodes=len(isaac.net.all_nodes()),
                    findings=len(isaac.findings),
                    laws=[{"name": n[4:],
                           "eq": (isaac.net.get_meta(n, "equation") or "")[:90]}
                          for n in laws],
                    minds=[f.name for f in MINDS.glob("*.isaac")])
    if p == "/api/teach":
        isaac.teach(body["subject"], body["relation"], body["object"])
        return dict(ok=f"taught: {body['subject']} {body['relation']} "
                       f"{body['object']}")
    if p == "/api/observe":
        isaac.observe(tokenize(body["text"]))
        return dict(ok=f"observed {len(tokenize(body['text']))} tokens")
    if p == "/api/ask":
        toks = tokenize(body["text"])
        if len(toks) >= 2 and toks[-1] == "?":
            objs = isaac.fact_index.get((toks[0], toks[1]), [])
            return dict(answer=", ".join(map(str, objs)) or
                        "(no fact — honest shrug)")
        nxt, conf = isaac.lookup(toks)
        return dict(answer=f"{nxt} (conf {conf:.2f})" if nxt
                    else "(shrug — not enough experience)")
    if p == "/api/discover":
        X, y, names, target = parse_table(body["table"], body.get("target", ""))
        name = body.get("name") or target
        res = isaac.discover(X[:20000], y[:20000], name=name)
        res["columns"] = names
        res["target"] = target
        res["name"] = name
        return res
    if p == "/api/apply":
        rows = [r for r in body["table"].strip().splitlines() if r.strip()]
        try:                                   # header row is optional here
            [float(c) for c in rows[0].split(",")]
            data = rows
        except ValueError:
            data = rows[1:]
        vals = np.array([[float(c) for c in r.split(",")] for r in data])
        pred = isaac.apply_law(body["name"], vals)
        if pred is None:
            return dict(error="no such law / wrong column count")
        return dict(predictions=[round(float(v), 4) for v in pred])
    if p == "/api/findings":
        return dict(findings=isaac.recall_findings(
            kind=body.get("kind") or None,
            contains=body.get("q") or None, limit=30))
    if p == "/api/save":
        name = (body.get("name") or "mind").replace(" ", "_")
        isaac.save(str(MINDS / f"{name}.isaac"))
        STATE["name"] = name
        return dict(ok=f"saved as {name}.isaac")
    if p == "/api/load":
        STATE["isaac"] = Isaac.load(str(MINDS / body["name"]))
        STATE["isaac"].ledger_path = str(LEDGER)
        STATE["name"] = body["name"].replace(".isaac", "")
        return dict(ok=f"loaded {body['name']}")
    if p == "/api/new":
        STATE["isaac"] = Isaac()
        STATE["isaac"].ledger_path = str(LEDGER)
        STATE["name"] = "unsaved mind"
        return dict(ok="fresh mind")
    if p == "/api/fork":
        STATE["isaac"] = isaac.fork()
        STATE["name"] = STATE["name"] + "-fork"
        return dict(ok=f"forked -> {STATE['name']}")
    return dict(error="unknown endpoint")


HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Isaac</title><style>
:root{--bg:#101418;--panel:#171d24;--ink:#d7dde4;--dim:#7b8794;
--acc:#5fb3a1;--warn:#d4a25a;--line:#232c36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 system-ui,Segoe UI,sans-serif}
header{padding:10px 18px;border-bottom:1px solid var(--line);display:flex;
gap:14px;align-items:baseline}
header b{color:var(--acc);font-size:18px}#mind{color:var(--dim)}
main{display:grid;grid-template-columns:1fr 1.2fr 1fr;gap:12px;padding:12px}
section{background:var(--panel);border:1px solid var(--line);border-radius:8px;
padding:12px;min-height:200px}
h2{margin:0 0 8px;font-size:13px;letter-spacing:.12em;color:var(--dim);
text-transform:uppercase}
input,textarea,select{width:100%;background:#0c1013;border:1px solid var(--line);
color:var(--ink);border-radius:6px;padding:7px;margin:3px 0;font:13px/1.4
ui-monospace,Consolas,monospace}
textarea{min-height:110px;resize:vertical}
button{background:var(--acc);color:#08110e;border:0;border-radius:6px;
padding:7px 12px;margin:4px 4px 0 0;font-weight:600;cursor:pointer}
button.ghost{background:transparent;color:var(--acc);border:1px solid var(--acc)}
.row{display:flex;gap:6px}.row>*{flex:1}
#log,#fout{font:12px/1.5 ui-monospace,Consolas,monospace;white-space:pre-wrap;
background:#0c1013;border-radius:6px;padding:8px;max-height:260px;
overflow:auto;border:1px solid var(--line)}
.card{border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:6px;padding:8px;margin:6px 0;font:12px/1.5 ui-monospace,monospace}
.card.warn{border-left-color:var(--warn)}
.k{color:var(--dim)} .v{color:var(--acc)} .laws div{font:12px ui-monospace,
monospace;padding:2px 0;border-bottom:1px dotted var(--line)}
small{color:var(--dim)}</style></head><body>
<header><b>ISAAC</b><span id="mind">…</span>
<span style="margin-left:auto"><small id="stat"></small></span></header>
<main>
<section><h2>Mind</h2>
<div class="row"><input id="savename" placeholder="name this mind">
<button onclick="post('/api/save',{name:val('savename')})">save</button></div>
<div class="row"><select id="minds"></select>
<button onclick="post('/api/load',{name:val('minds')})">load</button></div>
<button class="ghost" onclick="post('/api/new',{})">new mind</button>
<button class="ghost" onclick="post('/api/fork',{})">fork (counterfactual)</button>
<h2 style="margin-top:14px">Laws he holds</h2><div class="laws" id="laws"></div>
</section>
<section><h2>Converse</h2>
<div class="row"><input id="ts" placeholder="subject"><input id="tr"
placeholder="relation"><input id="to" placeholder="object">
<button onclick="post('/api/teach',{subject:val('ts'),relation:val('tr'),
object:val('to')})">teach</button></div>
<div class="row"><input id="obs" placeholder="observe a sentence…">
<button onclick="post('/api/observe',{text:val('obs')})">observe</button></div>
<div class="row"><input id="ask" placeholder="ask: 'the cat sat on the' or 'cat is_a ?'">
<button onclick="ask()">ask</button></div>
<div id="log"></div></section>
<section><h2>Discover</h2>
<textarea id="table" placeholder="paste a table (CSV with header)&#10;a,T&#10;0.387,0.241&#10;0.723,0.615&#10;1.0,1.0&#10;1.524,1.881&#10;5.203,11.86&#10;9.537,29.46&#10;19.19,84.01&#10;30.07,164.8"></textarea>
<div class="row"><input id="target" placeholder="target column (default: last)">
<input id="lawname" placeholder="law name"></div>
<button onclick="discover()">discover the law</button>
<div id="verdict"></div>
<h2 style="margin-top:12px">Remember</h2>
<div class="row"><input id="q" placeholder="search findings…">
<button onclick="findings()">search</button></div>
<div id="fout"></div></section>
</main><script>
const val=id=>document.getElementById(id).value;
const put=(id,h)=>document.getElementById(id).innerHTML=h;
function logln(s){const l=document.getElementById('log');
l.textContent+=s+"\\n";l.scrollTop=l.scrollHeight}
async function post(p,b){const r=await fetch(p,{method:'POST',
body:JSON.stringify(b)});const j=await r.json();
if(j.ok)logln("· "+j.ok);if(j.error)logln("! "+j.error);status();return j}
async function ask(){const j=await post('/api/ask',{text:val('ask')});
logln("you: "+val('ask'));logln("isaac: "+(j.answer||"?"))}
async function discover(){put('verdict','<small>thinking…</small>');
const j=await post('/api/discover',{table:val('table'),
target:val('target'),name:val('lawname')});
if(j.error){put('verdict','<div class=card>'+j.error+'</div>');return}
let riv=(j.rivals||[]).map(r=>`tied with <b>${r.rival}</b> (F ${r.F}) — probe: sample ${'x'+r.probe.feature} near ${r.probe.x}`).join('<br>');
put('verdict',`<div class="card ${j.verdict=='UNDERSTOOD'?'':'warn'}">
<span class=v>${j.verdict}</span> <span class=k>[${j.scope}]</span><br>
<b>${j.equation}</b><br>
<span class=k>R² ${j.r2.toFixed(3)} · edge ${j.r2_edge.toFixed(3)} ·
captured ${j.captured_r2.toFixed(3)} · columns ${j.columns.join(', ')}
→ ${j.target}</span>${riv?'<br>'+riv:''}</div>`)}
async function findings(){const j=await post('/api/findings',{q:val('q')});
put('fout',(j.findings||[]).map(f=>`#${f.id} [${f.kind}] ${f.name} — ${
f.verdict||f.status||''} ${f.equation?'· '+f.equation.slice(0,60):''}`)
.join("\\n")||"(nothing)")}
async function status(){const r=await fetch('/api/status',{method:'POST',
body:'{}'});const j=await r.json();
put('mind','⌂ '+j.mind);put('stat',j.nodes+' nodes · '+j.findings+' findings');
put('laws',j.laws.map(l=>`<div><b>${l.name}</b> <span class=k>${l.eq}</span></div>`).join('')||'<small>none yet</small>');
const m=document.getElementById('minds');
m.innerHTML=j.minds.map(x=>`<option>${x}</option>`).join('')}
status();</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, HTML, "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        try:
            with LOCK:
                out = api(self, body)
            self._send(200, json.dumps(Isaac._jsonable(out), default=str))
        except Exception as e:
            self._send(200, json.dumps({"error": f"{type(e).__name__}: {e}"}))


if __name__ == "__main__":
    port = 8674
    print(f"Isaac is listening — open http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
