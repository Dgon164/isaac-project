"""
Isaac — Desktop Application
Flask backend with command parser. Serves the GUI and handles all interaction.
"""

import json
import io
import sys
from flask import Flask, render_template, request, jsonify
from isaac import Isaac, tokenize, World

app = Flask(__name__)

# Global Isaac instance
isaac = Isaac()
world = World(isaac=isaac)


def capture_output(func, *args, **kwargs):
    """Capture print output from a function."""
    old = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        result = func(*args, **kwargs)
    finally:
        sys.stdout = old
    return result, buf.getvalue()


def parse_and_execute(text):
    """Parse user input and route to the appropriate Isaac method."""
    global isaac, world
    text = text.strip()
    if not text:
        return {"type": "error", "text": "Empty input."}

    low = text.lower()
    parts = text.split()
    cmd = parts[0].lower() if parts else ""

    # ── help ────────────────────────────────────────────────
    if cmd == "help":
        return {"type": "help", "text": HELP_TEXT}

    # ── status ──────────────────────────────────────────────
    if cmd == "status":
        st = isaac.status()
        lines = [f"Nodes: {st['nodes']}  Doors: {st['doors']}",
                 f"Types: {st['types']}  Rules: {st['rules']}  Lockouts: {st['lockouts']}",
                 f"Observations: {st['observations']}  Facts indexed: {st['facts_indexed']}",
                 f"Compiled: {st['compiled']}  Matrix: {st['matrix_shape']}",
                 f"Tags: {', '.join(st['tags']) if st['tags'] else 'none'}"]
        return {"type": "status", "text": "\n".join(lines), "data": st}

    # ── observe ─────────────────────────────────────────────
    if cmd == "observe":
        sentence = " ".join(parts[1:])
        tokens = tokenize(sentence)
        isaac.observe(tokens)
        return {"type": "ok", "text": f"Observed: {' '.join(tokens)}\nDoors created: {len(tokens)-1}"}

    # ── negative ────────────────────────────────────────────
    if cmd in ("negative", "neg", "bad"):
        sentence = " ".join(parts[1:])
        tokens = tokenize(sentence)
        isaac.observe_negative(tokens)
        return {"type": "ok", "text": f"Negative observed: {' '.join(tokens)}"}

    # ── teach ───────────────────────────────────────────────
    if cmd == "teach":
        rest = parts[1:]
        if len(rest) >= 3:
            subj, rel, obj = rest[0], rest[1], " ".join(rest[2:])
            isaac.teach(subj, rel, obj)
            return {"type": "ok", "text": f"Taught: {subj} {rel} {obj}"}
        return {"type": "error", "text": "Usage: teach <subject> <relation> <object>"}

    # ── crystallize ─────────────────────────────────────────
    if cmd == "crystallize":
        _, output = capture_output(isaac.crystallize, verbose=True)
        types_info = []
        for name, data in isaac.types.items():
            members = sorted(data["members"])
            types_info.append(f"  {name}: {members}")
        result = output.strip()
        if types_info:
            result += "\n\nTypes discovered:\n" + "\n".join(types_info)
        return {"type": "ok", "text": result if result else "Crystallized. No types found (need more data)."}

    # ── compile ─────────────────────────────────────────────
    if cmd == "compile":
        stats = isaac.compile()
        if stats:
            return {"type": "ok", "text": f"Compiled.\n  Frames: {stats['frames']:,}\n  Deltas: {stats['deltas']:,}\n  Nonzero: {stats['nonzero']:,}\n  Matrix: {stats['matrix_shape']}"}
        return {"type": "error", "text": "Nothing to compile. Feed some data first. (Note: compilation is automatic on query.)"}

    # ── lookup ──────────────────────────────────────────────
    if cmd == "lookup":
        context = tokenize(" ".join(parts[1:]))
        answer, conf = isaac.lookup(context)
        return {"type": "result", "text": f"lookup [{' '.join(context)}]\n→ {answer}  (confidence: {conf:.2f})"}

    # ── check ───────────────────────────────────────────────
    if cmd == "check":
        rest = " ".join(parts[1:])
        if "::" in rest:
            context_str, target = rest.split("::", 1)
            context = tokenize(context_str.strip())
            target = target.strip()
        elif " = " in rest:
            before, target = rest.rsplit(" = ", 1)
            context = tokenize(before.strip() + " =")
            target = target.strip()
        else:
            return {"type": "error", "text": "Usage: check <context> :: <target>  or  check 3 + 5 = 8"}
        match, conf = isaac.check(context, target)
        symbol = "✓" if match else "✗"
        return {"type": "result", "text": f"check [{' '.join(context)}] → {target}\n{symbol} match={match}  confidence={conf:.2f}"}

    # ── generate ────────────────────────────────────────────
    if cmd == "generate" or cmd == "gen":
        concept = parts[1] if len(parts) > 1 else None
        if not concept:
            return {"type": "error", "text": "Usage: generate <concept>"}
        chain = isaac.generate(concept)
        return {"type": "result", "text": f"generate '{concept}':\n→ {' '.join(chain)}"}

    # ── can ──────────────────────────────────────────────────
    if cmd == "can":
        if len(parts) >= 3:
            subj = parts[1]
            ability = parts[2]
            (result, chain), output = capture_output(
                isaac.can_check, subj, ability, verbose=True)
            if result is None:
                answer = "unknown"
            elif result:
                answer = "yes"
            else:
                answer = "no"
            return {"type": "result", "text": f"can {subj} {ability}?\n→ {answer}\n{output.strip()}"}
        return {"type": "error", "text": "Usage: can <subject> <ability>"}

    # ── is ... a ────────────────────────────────────────────
    if cmd == "is" and "a" in parts:
        a_idx = parts.index("a")
        subj = " ".join(parts[1:a_idx])
        target = " ".join(parts[a_idx+1:])
        if subj and target:
            found, chain = isaac.is_a_check(subj, target)
            symbol = "✓ yes" if found else "✗ no"
            return {"type": "result", "text": f"is {subj} a {target}?\n→ {symbol}\nchain: {' → '.join(chain)}"}

    # ── in ──────────────────────────────────────────────────
    if cmd == "contains" or (cmd == "is" and "in" in parts):
        if "in" in parts:
            in_idx = parts.index("in")
            item = " ".join(parts[1:in_idx])
            container = " ".join(parts[in_idx+1:])
        else:
            item = parts[1] if len(parts) > 1 else ""
            container = parts[2] if len(parts) > 2 else ""
        if item and container:
            found, chain = isaac.containment_check(item, container)
            symbol = "✓ yes" if found else "✗ no"
            return {"type": "result", "text": f"is {item} in {container}?\n→ {symbol}\nchain: {' → '.join(chain)}"}

    # ── logic ───────────────────────────────────────────────
    if cmd == "logic":
        expr = " ".join(parts[1:])
        result, trace = isaac.logic_eval(expr)
        return {"type": "result", "text": f"logic: {expr}\n→ {result}"}

    # ── compute ─────────────────────────────────────────────
    if cmd == "compute":
        rest = parts[1:]
        if len(rest) >= 3:
            try:
                a, op, b = int(rest[0]), rest[1], int(rest[2])
                (result, method), output = capture_output(
                    isaac.compute, a, op, b, memorize=True, verbose=True)
                return {"type": "result", "text": output.strip()}
            except (ValueError, IndexError):
                pass
        return {"type": "error", "text": "Usage: compute <number> <op> <number>  (e.g., compute 137 * 48)"}

    # ── solve ───────────────────────────────────────────────
    if cmd == "solve":
        problem = " ".join(parts[1:])
        _, output = capture_output(isaac.solve, problem, verbose=True)
        return {"type": "result", "text": f"solve: {problem}\n{output.strip()}"}

    # ── assess ──────────────────────────────────────────────
    if cmd == "assess":
        action = " ".join(parts[1:])
        (proceed, assessment), output = capture_output(
            isaac.plan_think_execute, action, verbose=True)
        return {"type": "result", "text": output.strip()}

    # ── chain / reason ──────────────────────────────────────
    if cmd in ("chain", "reason"):
        if len(parts) >= 3:
            subj = parts[1]
            rel = parts[2]
            chain = isaac.reason_chain(subj, rel)
            return {"type": "result", "text": f"{subj} {rel} chain:\n→ {' → '.join(chain)}"}
        return {"type": "error", "text": "Usage: chain <subject> <relation>"}

    # ── properties ──────────────────────────────────────────
    if cmd in ("properties", "props", "has"):
        if len(parts) >= 2:
            subj = parts[1]
            props = isaac.property_check(subj)
            if props:
                lines = [f"  {p} ({src})" for p, src in props]
                return {"type": "result", "text": f"{subj} has:\n" + "\n".join(lines)}
            return {"type": "result", "text": f"{subj}: no properties found"}
        return {"type": "error", "text": "Usage: properties <subject>"}

    # ── feed file ───────────────────────────────────────────
    if cmd == "feed":
        rest = " ".join(parts[1:])
        lines = [l.strip() for l in rest.split(";") if l.strip()]
        count = 0
        for line in lines:
            tokens = tokenize(line)
            if tokens:
                isaac.observe(tokens)
                count += 1
        return {"type": "ok", "text": f"Fed {count} observations."}

    # ── clear / reset ───────────────────────────────────────
    if cmd in ("clear", "reset"):
        isaac = Isaac()
        world = World(isaac=isaac)
        return {"type": "ok", "text": "Isaac reset. All knowledge cleared."}

    # ── fallback: if it looks like an equation, try to solve it ──
    if "?" in text and "=" in text:
        _, output = capture_output(isaac.solve, text, verbose=True)
        return {"type": "result", "text": f"solve: {text}\n{output.strip()}"}

    # ── fallback: treat as observation ──────────────────────
    tokens = tokenize(text)
    if tokens:
        isaac.observe(tokens)
        return {"type": "ok", "text": f"Observed: {' '.join(tokens)}\n(Didn't recognize a command — treated as observation. Type 'help' for commands.)"}

    return {"type": "error", "text": "Couldn't parse that. Type 'help' for available commands."}


HELP_TEXT = """Commands:

  observe <sentence>         Feed a sentence
  negative <sentence>        Feed a negative example
  teach <subj> <rel> <obj>   Teach a fact (e.g., teach cat is_a mammal)
  feed <s1> ; <s2> ; ...     Feed multiple observations (semicolon-separated)

  crystallize                Discover types from structure (alias: consolidate)
  compile                    Build the inference matrix (automatic on query)
  consolidate                Full offline crystallization (sleep mode)

  lookup <context>           What comes next? (argmax)
  check <context> :: <target>   Is this claim true? (specific cell)
  check 3 + 5 = 8           Shorthand for check with =

  generate <concept>         Generate a sentence containing concept
  can <subject> <ability>    Can subject do ability?
  is <subject> a <target>    Is subject a target? (taxonomy chain)
  is <item> in <container>   Containment check
  chain <subject> <relation> Walk a relation chain
  properties <subject>       List properties (direct + inherited)
  logic <expression>         Evaluate logic (e.g., logic true and false)

  compute <a> <op> <b>       Math with decompose-when-shrug
  solve <problem>            Solve with unknowns (e.g., solve ? + 5 = 8)
  assess <action>            Persistence assessment

  status                     Show net statistics
  reset                      Clear all knowledge
  help                       Show this message

Anything not matching a command is treated as an observation."""


# ── Flask routes ────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/command", methods=["POST"])
def command():
    data = request.get_json()
    text = data.get("text", "")
    result = parse_and_execute(text)
    return jsonify(result)


@app.route("/api/status")
def status():
    return jsonify(isaac.status())


if __name__ == "__main__":
    app.run(debug=False, port=5000)
