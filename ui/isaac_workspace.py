"""
ISAAC WORKSPACE — one file, stdlib + numpy only. Three channels, hard walls.

    python isaac_workspace.py       then open  http://127.0.0.1:8675

  /file      — inputs. Human-owned content, processed as whole units.
               Isaac reads; he NEVER writes here. The source stays pristine.
  /in  /say  — the discussion. Humans write via /in, Isaac writes via /say.
               Append-only; he cannot alter what was said. His side is only
               what his machinery actually emits — a unit, or silence.
  /findings  — his output structure: laws and the ledger. He writes and
               amends it (supersession, never erasure). Humans comment.

Nothing in this file generates words attributed to Isaac. Console text
(actions, telemetry) renders as instrument readout, visually distinct
from his voice. Bad answers are his to give; silence is his shrug.
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from isaac import Isaac, tokenize

ROOT = Path(__file__).resolve().parents[1]
MINDS = ROOT / "data" / "minds"
MINDS.mkdir(parents=True, exist_ok=True)
LEDGER = ROOT / "data" / "findings.jsonl"
PROJECT = ROOT / "data" / "workspace_project.json"

MAX_ROWS = 20000              # discover cap — the engine is synchronous

STATE = {"isaac": Isaac(), "name": "unsaved mind"}
STATE["isaac"].ledger_path = str(LEDGER)
LOCK = threading.Lock()

PROJ = {"content": [], "chat": [], "comments": {}, "seq": 0}
if PROJECT.exists():
    try:
        PROJ.update(json.loads(PROJECT.read_text(encoding="utf-8")))
    except Exception:
        pass


def save_project():
    PROJECT.write_text(json.dumps(PROJ, ensure_ascii=False, indent=1),
                       encoding="utf-8")


def nid():
    PROJ["seq"] += 1
    return PROJ["seq"]


def post_msg(who, text, meta=""):
    """who: 'you' (/in) · 'isaac' (/say, verbatim engine output only)
            · 'inst' (instrument telemetry — the console, never Isaac)"""
    m = dict(id=nid(), who=who, text=text, meta=meta,
             ts=time.strftime("%H:%M"))
    PROJ["chat"].append(m)
    return m


def his_turn(isaac, context):
    """Pull once on Isaac's output machinery. Whatever comes back is
    posted verbatim as /say; nothing = no /say entry. The readout of
    the pull itself is telemetry."""
    nxt, conf = isaac.lookup(context)
    if nxt is not None:
        post_msg("isaac", str(nxt), f"/say · lookup conf {conf:.2f}")
    else:
        post_msg("inst", "∅", f"output pull: below threshold "
                 f"(conf {conf:.2f}) — his shrug, shown raw")


def looks_like_table(text):
    rows = [r for r in text.strip().splitlines() if r.strip()]
    if len(rows) < 3:
        return False
    sep = "," if "," in rows[1] else None
    try:
        [float(c) for c in rows[1].split(sep)]
        [float(c) for c in rows[2].split(sep)]
        return True
    except ValueError:
        return False


def parse_table(text, target=""):
    rows = [r for r in text.strip().splitlines() if r.strip()]
    sep = "," if "," in rows[0] else None
    head = [h.strip() for h in rows[0].split(sep)]
    try:                                   # header row is optional
        [float(c) for c in head]
        head = [f"c{i}" for i in range(len(head))]
        data = rows
    except ValueError:
        data = rows[1:]
    cols = {h: [] for h in head}
    for r in data:
        for h, v in zip(head, [c.strip() for c in r.split(sep)]):
            cols[h].append(float(v))
    if target not in cols:
        target = head[-1]
    y = np.array(cols.pop(target))
    names = list(cols)
    X = np.column_stack([cols[h] for h in names])
    return X, y, names, target


# ------------------------------------------------------------------------ api
def api(path, body):
    isaac = STATE["isaac"]

    if path == "/api/state":
        laws = sorted(n for n in isaac.net.get_doors("law", tag="law"))
        return dict(
            mind=STATE["name"],
            status=dict(nodes=len(isaac.net.all_nodes()),
                        findings=len(isaac.findings)),
            minds=[f.name for f in MINDS.glob("*.isaac")],
            laws=[dict(name=n[4:],
                       eq=(isaac.net.get_meta(n, "equation") or "")[:120])
                  for n in laws],
            content=[dict(id=c["id"], name=c["name"], kind=c["kind"],
                          lines=c["text"].count("\n") + 1,
                          chars=len(c["text"]),
                          processed=c.get("processed", ""),
                          preview="\n".join(c["text"].splitlines()[:4]))
                     for c in PROJ["content"]],
            chat=PROJ["chat"][-200:],
            findings=isaac.recall_findings(limit=30),
            comments=PROJ["comments"])

    # ------------------------------------------------------- /in (+ /say)
    if path == "/api/in":
        t = body["text"].strip()
        if not t:
            return dict(ok=True)
        if t.startswith("/teach"):        # explicit operator act, labeled
            p = t.split()[1:]
            if len(p) >= 3:
                isaac.teach(p[0], p[1], " ".join(p[2:]))
                post_msg("inst", f"operator taught: {p[0]} {p[1]} "
                         f"{' '.join(p[2:])}", "/teach")
            else:
                post_msg("inst", "usage: /teach subject relation object",
                         "/teach")
            save_project()
            return dict(ok=True)
        post_msg("you", t, "/in")
        toks = tokenize(t)
        if toks:
            before = len(isaac.net.all_nodes())
            isaac.observe(toks)
            grew = len(isaac.net.all_nodes()) - before
            post_msg("inst", f"ingested {len(toks)} tokens"
                     + (f" · {grew} new nodes" if grew else ""),
                     "observe")
            his_turn(isaac, toks)
        save_project()
        return dict(ok=True)

    # ------------------------------------------------------------- /file
    if path == "/api/content/add":
        text = body["text"]
        kind = "table" if looks_like_table(text) else "text"
        item = dict(id=nid(), name=body.get("name") or f"item {PROJ['seq']}",
                    kind=kind, text=text, processed="",
                    added=time.strftime("%m-%d %H:%M"))
        PROJ["content"].append(item)
        post_msg("inst", f"/file added: “{item['name']}” "
                 f"({kind}, {len(text)} chars)", "content")
        save_project()
        return dict(ok=True, id=item["id"])

    if path == "/api/content/update":
        for c in PROJ["content"]:
            if c["id"] == body["id"]:
                if "text" in body:
                    c["text"] = body["text"]
                    c["kind"] = ("table" if looks_like_table(body["text"])
                                 else "text")
                    c["processed"] = ""
                if body.get("name"):
                    c["name"] = body["name"]
                save_project()
                return dict(ok=True)
        return dict(error="no such content")

    if path == "/api/content/remove":
        PROJ["content"] = [c for c in PROJ["content"] if c["id"] != body["id"]]
        save_project()
        return dict(ok=True)

    if path == "/api/content/process":
        # one whole unit, directly: tables -> discover (verdict lands in
        # /findings via his own ledger); text -> ingested line by line.
        for c in PROJ["content"]:
            if c["id"] != body["id"]:
                continue
            if c["kind"] == "table":
                X, y, names, target = parse_table(c["text"],
                                                  body.get("target", ""))
                name = body.get("name") or f"{c['name']}:{target}"
                capped = len(y) > MAX_ROWS
                res = isaac.discover(X[:MAX_ROWS], y[:MAX_ROWS], name=name)
                res.update(columns=names, target=target, name=name)
                c["processed"] = time.strftime("%m-%d %H:%M")
                post_msg("inst", f"processed “{c['name']}” as a "
                         f"unit: discover({', '.join(names)} → {target})"
                         f" → his verdict {res['verdict']} filed to "
                         "/findings"
                         + (f" (capped {MAX_ROWS}/{len(y)} rows)"
                            if capped else ""), "discover")
                save_project()
                return res
            n = 0
            last = None
            for line in c["text"].splitlines():
                tk = tokenize(line)
                if tk:
                    isaac.observe(tk)
                    n += len(tk)
                    last = tk
            c["processed"] = time.strftime("%m-%d %H:%M")
            post_msg("inst", f"processed “{c['name']}” as a unit: "
                     f"{n} tokens ingested", "observe")
            if last:
                his_turn(isaac, last)
            save_project()
            return dict(ok=True)
        return dict(error="no such content")

    # --------------------------------------------------------- /findings
    if path == "/api/apply":
        for c in PROJ["content"]:
            if c["id"] == body["id"]:
                rows = [r for r in c["text"].strip().splitlines()
                        if r.strip()]
                sep = "," if "," in rows[0] else None
                try:
                    [float(x) for x in rows[0].split(sep)]
                    data = rows
                except ValueError:
                    data = rows[1:]
                vals = np.array([[float(x) for x in r.split(sep)]
                                 for r in data])
                pred = isaac.apply_law(body["law"], vals)
                if pred is None and vals.shape[1] > 1:
                    # the table likely still carries its target column
                    pred = isaac.apply_law(body["law"], vals[:, :-1])
                if pred is None:
                    return dict(error="no such law / wrong column count")
                shown = ", ".join(f"{float(v):.4g}" for v in pred[:12])
                more = f" … ({len(pred)} total)" if len(pred) > 12 else ""
                post_msg("inst", f"applied his law “{body['law']}” "
                         f"to “{c['name']}”: {shown}{more}",
                         "apply_law")
                save_project()
                return dict(predictions=[float(v) for v in pred])
        return dict(error="no such content")

    if path == "/api/confirm":
        for c in PROJ["content"]:
            if c["id"] == body["id"] and c["kind"] == "table":
                X, y, _, _ = parse_table(c["text"], body.get("target", ""))
                res = isaac.confirm(body["law"], X[:MAX_ROWS], y[:MAX_ROWS])
                post_msg("inst", f"confirm ran: “{body['law']}” "
                         f"vs “{c['name']}” → his status: "
                         f"{res.get('status')}", "confirm")
                save_project()
                return res
        return dict(error="content item is not a table")

    if path == "/api/comment":
        PROJ["comments"].setdefault(body["key"], []).append(
            dict(text=body["text"], ts=time.strftime("%m-%d %H:%M")))
        save_project()
        return dict(ok=True)

    # -------------------------------------------------------------- mind
    if path == "/api/mind":
        act = body["action"]
        if act == "save":
            name = (body.get("name") or "mind").replace(" ", "_")
            isaac.save(str(MINDS / f"{name}.isaac"))
            STATE["name"] = name
            post_msg("inst", f"mind saved as {name}.isaac", "save")
        elif act == "load":
            STATE["isaac"] = Isaac.load(str(MINDS / body["name"]))
            STATE["isaac"].ledger_path = str(LEDGER)
            STATE["name"] = body["name"].replace(".isaac", "")
            post_msg("inst", f"mind loaded: {STATE['name']}", "load")
        elif act == "new":
            STATE["isaac"] = Isaac()
            STATE["isaac"].ledger_path = str(LEDGER)
            STATE["name"] = "unsaved mind"
            post_msg("inst", "fresh mind (project channels persist)", "new")
        elif act == "fork":
            STATE["isaac"] = isaac.fork()
            STATE["name"] = STATE["name"] + "-fork"
            post_msg("inst", f"forked → {STATE['name']}", "fork")
        save_project()
        return dict(ok=True)

    return dict(error="unknown endpoint")


# ------------------------------------------------------------------ frontend
HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Isaac Workspace</title><style>
:root{--bg:#101418;--panel:#171d24;--ink:#d7dde4;--dim:#7b8794;
--acc:#5fb3a1;--warn:#d4a25a;--you:#3d5a80;--line:#232c36}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 system-ui,Segoe UI,sans-serif;height:100vh;display:flex;
flex-direction:column;overflow:hidden}
header{padding:8px 16px;border-bottom:1px solid var(--line);display:flex;
gap:12px;align-items:center;flex:none}
header b{color:var(--acc);font-size:17px}
header input,header select{background:#0c1013;border:1px solid var(--line);
color:var(--ink);border-radius:6px;padding:5px 8px;font:12px ui-monospace,
Consolas,monospace}
button{background:var(--acc);color:#08110e;border:0;border-radius:6px;
padding:6px 11px;font-weight:600;cursor:pointer;font-size:12px}
button.ghost{background:transparent;color:var(--acc);
border:1px solid var(--acc)}
button.dim{background:transparent;color:var(--dim);
border:1px solid var(--line)}
main{flex:1;display:grid;grid-template-columns:0.9fr 1.4fr 1.1fr;gap:10px;
padding:10px;min-height:0}
section{background:var(--panel);border:1px solid var(--line);
border-radius:10px;display:flex;flex-direction:column;min-height:0}
h2{margin:0;padding:10px 12px 2px;font-size:12px;letter-spacing:.14em;
color:var(--dim);text-transform:uppercase;flex:none}
h2 small{text-transform:none;letter-spacing:0;font-weight:400}
.body{flex:1;overflow-y:auto;padding:4px 10px 10px;min-height:0}
.foot{flex:none;padding:8px 10px;border-top:1px solid var(--line)}
small{color:var(--dim)}
textarea,input.wide{width:100%;background:#0c1013;border:1px solid
var(--line);color:var(--ink);border-radius:6px;padding:7px;
font:12px/1.45 ui-monospace,Consolas,monospace}
textarea{resize:vertical}
.card{border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:6px;padding:8px;margin:7px 0;
font:12px/1.5 ui-monospace,Consolas,monospace}
.card.warn{border-left-color:var(--warn)}
.card .nm{color:var(--acc);font-weight:700}
.card .kd{color:var(--dim);margin-left:6px}
.card pre{margin:5px 0;white-space:pre-wrap;color:var(--dim);
max-height:72px;overflow:hidden}
.card .ops{margin-top:5px;display:flex;gap:4px;flex-wrap:wrap;
align-items:center}
.msg{margin:8px 0;max-width:92%}
.msg .bub{padding:7px 11px;border-radius:10px;white-space:pre-wrap;
font-size:13px}
.msg.you{margin-left:auto}
.msg.you .bub{background:var(--you);border-radius:10px 10px 2px 10px}
.msg.isaac .bub{background:#0c1013;border:2px solid var(--acc);
border-radius:10px 10px 10px 2px;font:15px ui-monospace,Consolas,monospace;
color:var(--acc)}
.msg.inst{max-width:100%}
.msg.inst .bub{background:transparent;border:0;padding:0 4px;
font:11px ui-monospace,Consolas,monospace;color:var(--dim)}
.msg .meta{font:10px ui-monospace,monospace;color:var(--dim);
padding:2px 4px}
.msg.you .meta{text-align:right}
.msg.inst .meta{display:none}
.cmt{border-top:1px dotted var(--line);margin-top:5px;padding-top:4px;
color:var(--ink)}
.chatrow{display:flex;gap:6px}
.chatrow textarea{flex:1;min-height:38px;max-height:120px}
#spin{color:var(--warn);display:none;font-size:12px;padding:2px 4px}
</style></head><body>
<header><b>ISAAC</b><span id="mind" style="color:var(--dim)">…</span>
<span style="margin-left:auto"></span>
<small id="stat"></small>
<input id="savename" placeholder="mind name" style="width:110px">
<button onclick="mind('save',{name:val('savename')})">save</button>
<select id="minds"></select>
<button class="ghost" onclick="mind('load',{name:val('minds')})">load</button>
<button class="dim" onclick="mind('new',{})">new</button>
<button class="dim" onclick="mind('fork',{})">fork</button>
</header>
<main>
<section><h2>/file — inputs <small>· he reads, never writes</small>
</h2>
<div class="body" id="content"></div>
<div class="foot">
<input class="wide" id="cname" placeholder="name this content…">
<textarea id="ctext" placeholder="paste text or a CSV table…"
style="min-height:64px;margin-top:4px"></textarea>
<div style="display:flex;gap:6px;margin-top:5px">
<button onclick="addContent()">add</button>
<button class="ghost" onclick="fileEl.click()">upload file(s)</button>
<input type="file" id="file" multiple style="display:none"></div>
</div></section>
<section><h2>/in · /say — the discussion <small>· append-only
</small></h2>
<div class="body" id="chat"></div>
<div class="foot"><span id="spin">working…</span>
<div class="chatrow">
<textarea id="say" placeholder="/in — goes to Isaac whole. His /say is only what he emits; silence is his."></textarea>
<button onclick="send()" style="align-self:flex-end">send</button>
</div></div></section>
<section><h2>/findings — his output <small>· he amends, you comment
</small></h2>
<div class="body" id="find"></div>
</section>
</main><script>
const val=id=>document.getElementById(id).value;
const el=id=>document.getElementById(id);
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
.replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const fileEl=el('file');
let S=null,busy=false;

async function post(p,b){const r=await fetch(p,{method:'POST',
body:JSON.stringify(b||{})});return r.json()}

async function refresh(){S=await post('/api/state');render()}

function render(){
el('mind').textContent='\\u2302 '+S.mind;
el('stat').textContent=S.status.nodes+' nodes \\u00b7 '
+S.status.findings+' findings';
el('minds').innerHTML=S.minds.map(m=>'<option>'+esc(m)+'</option>').join('');
// /file
el('content').innerHTML=S.content.map(c=>{
let ops='<button onclick="processItem('+c.id+')">process</button>';
if(c.kind=='table')ops='<input id="tg'+c.id+'" placeholder="target col" '
+'style="width:72px;background:#0c1013;border:1px solid var(--line);'
+'color:var(--ink);border-radius:5px;padding:4px;font-size:11px">'
+'<input id="ln'+c.id+'" placeholder="law name" style="width:72px;'
+'background:#0c1013;border:1px solid var(--line);color:var(--ink);'
+'border-radius:5px;padding:4px;font-size:11px">'+ops;
ops+='<button class="dim" onclick="editItem('+c.id+')">edit</button>'
+'<button class="dim" onclick="rmItem('+c.id+')">remove</button>';
return '<div class="card"><span class="nm">'+esc(c.name)+'</span>'
+'<span class="kd">'+c.kind+' \\u00b7 '+c.lines+' lines'
+(c.processed?' \\u00b7 processed '+c.processed:' \\u00b7 unprocessed')
+'</span><pre>'+esc(c.preview)+'</pre>'
+'<div class="ops">'+ops+'</div>'
+'<div id="ed'+c.id+'"></div></div>'}).join('')
||'<small>no inputs yet \\u2014 paste or upload below. content here is '
+'immutable to Isaac.</small>';
// /in /say
el('chat').innerHTML=S.chat.map(m=>
'<div class="msg '+m.who+'"><div class="bub">'+esc(m.text)+'</div>'
+'<div class="meta">'+(m.who=='you'?'you \\u00b7 /in':'isaac \\u00b7 /say')
+(m.meta&&m.who!='you'?' \\u00b7 '+esc(m.meta):'')+' \\u00b7 '+m.ts
+'</div></div>').join('')
||'<small>nothing said yet. what you send is ingested whole; what he '
+'emits comes back verbatim \\u2014 even one token, even nothing.</small>';
el('chat').scrollTop=el('chat').scrollHeight;
// /findings
let laws=S.laws.map(l=>{
let sels=S.content.filter(c=>c.kind=='table');
let opts=sels.map(c=>'<option value="'+c.id+'">'+esc(c.name)+'</option>')
.join('');
let act=sels.length?'<div class="ops"><select id="tb'+esc(l.name)
+'" style="background:#0c1013;color:var(--ink);border:1px solid '
+'var(--line);border-radius:5px;font-size:11px">'+opts+'</select>'
+'<button class="dim" onclick="applyLaw(\\''+esc(l.name)+'\\')">apply'
+'</button><button class="dim" onclick="confirmLaw(\\''+esc(l.name)
+'\\')">confirm</button></div>':'';
return '<div class="card"><span class="nm">'+esc(l.name)+'</span>'
+'<pre style="max-height:none">'+esc(l.eq)+'</pre>'+act+'</div>'}).join('');
let leds=S.findings.map(f=>{
let key=f.kind+':'+(f.name||f.id);
let cs=(S.comments[key]||[]).map(c=>'<div class="cmt">\\u270e '
+esc(c.text)+' <small>'+c.ts+'</small></div>').join('');
return '<div class="card '+((f.verdict||'')=='UNDERSTOOD'?'':'warn')+'">'
+'<span class="nm">#'+f.id+' '+esc(f.name||'')+'</span>'
+'<span class="kd">'+esc(f.kind||'')+' \\u00b7 '
+esc(f.verdict||f.status||'')+'</span>'
+(f.equation?'<pre style="max-height:none">'+esc(f.equation)+'</pre>':'')
+cs+'<div class="ops"><input id="cm'+f.id+'" placeholder="comment / '
+'question / requested change\\u2026" style="flex:1;background:#0c1013;'
+'border:1px solid var(--line);color:var(--ink);border-radius:5px;'
+'padding:4px;font-size:11px"><button class="dim" onclick="comment(\\''
+key+'\\','+f.id+')">add</button></div></div>'}).join('');
el('find').innerHTML=(laws?'<small>laws he holds</small>'+laws:'')
+(leds?'<small>the ledger \\u2014 his records, kept his way</small>'+leds
:'<small>nothing filed yet \\u2014 process a table in /file and his '
+'verdict lands here</small>')}

async function act(fn){if(busy)return;busy=true;el('spin').style.display=
'inline';try{await fn()}finally{busy=false;
el('spin').style.display='none';refresh()}}

function send(){const t=val('say');if(!t.trim())return;el('say').value='';
act(()=>post('/api/in',{text:t}))}
el('say').addEventListener('keydown',e=>{
if(e.key=='Enter'&&!e.shiftKey){e.preventDefault();send()}});

function addContent(){const t=val('ctext');if(!t.trim())return;
el('ctext').value='';act(()=>post('/api/content/add',
{name:val('cname'),text:t}))}
fileEl.addEventListener('change',()=>{[...fileEl.files].forEach(f=>{
const rd=new FileReader();rd.onload=()=>act(()=>post('/api/content/add',
{name:f.name,text:rd.result}));rd.readAsText(f)});fileEl.value=''});
function rmItem(id){act(()=>post('/api/content/remove',{id}))}
function processItem(id){const tg=el('tg'+id),ln=el('ln'+id);
act(()=>post('/api/content/process',
{id,target:tg?tg.value:'',name:ln?ln.value:''}))}
function editItem(id){
el('ed'+id).innerHTML='<textarea id="et'+id+'" style="min-height:90px;'
+'margin-top:5px"></textarea><button onclick="saveItem('+id
+')" style="margin-top:4px">save changes</button>';
loadFull(id)}
async function loadFull(id){const s=await post('/api/content/full',{id});
el('et'+id).value=s.text||''}
function saveItem(id){const t=val('et'+id);
act(()=>post('/api/content/update',{id,text:t}))}
function applyLaw(n){const id=+val('tb'+n);
act(()=>post('/api/apply',{law:n,id}))}
function confirmLaw(n){const id=+val('tb'+n);
act(()=>post('/api/confirm',{law:n,id}))}
function comment(key,fid){const t=val('cm'+fid);if(!t.trim())return;
act(()=>post('/api/comment',{key,text:t}))}
function mind(action,extra){act(()=>post('/api/mind',
Object.assign({action},extra)))}

refresh();setInterval(()=>{if(!busy)refresh()},6000);
</script></body></html>"""


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
        if self.path == "/":
            self._send(200, HTML, "text/html; charset=utf-8")
        else:
            self._send(404, "{}")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        path = self.path.split("?")[0]
        try:
            if path == "/api/content/full":       # full text, no engine work
                item = next((c for c in PROJ["content"]
                             if c["id"] == body["id"]), None)
                out = (dict(text=item["text"]) if item
                       else dict(error="no such content"))
            else:
                with LOCK:
                    out = api(path, body)
            self._send(200, json.dumps(Isaac._jsonable(out), default=str))
        except Exception as e:
            self._send(200, json.dumps({"error": f"{type(e).__name__}: {e}"}))


if __name__ == "__main__":
    port = 8675
    print(f"Isaac workspace — open http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
