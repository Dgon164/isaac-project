# THE ONE-FILE BODY v2 — the probe. Proven BEFORE install (house
# pattern: shape_fptp_probe.py was courted before it became the
# interpreter). Owner directive 2026-08-19: ONE FILE TOTAL for him;
# smaller files are worker RAM only, never the truth.
#
# Works on a scratchpad COPY of a protective .bak. Never reads or
# writes isaac-life. Writes only to the scratchpad.
#
# The format (v2): one file, sectioned inside.
#   header    magic + json section table (offsets, lengths, sha256)
#   core      the whole mind pickled WITH the big stores emptied —
#             keeps every cross-reference (world backref included)
#             in one object graph, no duplication
#   netgraph  vocabulary (every node name ONCE) + columnar edges
#             (src_id, tgt_id, count, tagset_id) + meta by id
#   history   the activation log — his diary, compressed hard,
#             loadable lazily later (still all kept, keep-everything)
#   journal   append-only tail: autosave = append deltas, never a
#             full rewrite; a torn tail truncates cleanly on load
# preds is DERIVED and never stored (rebuilt on load — the engine
# already owns that road via _ensure_preds).
#
# THE COURTS (equivalence court is standing law for any migration):
#   C1 ROUND TRIP  v1 him -> v2 file -> him, item-for-item equal:
#                  doors, door_tags, door_counts, meta, every other
#                  attribute deep-equal; preds-rebuilt reported.
#   C2 SIZE        plain numbers, v1 vs v2, per section.
#   C3 SPEED       save and load, measured.
#   C4 JOURNAL     append 3 deltas -> reload sees them; tear the
#                  tail mid-record -> reload survives, valid prefix
#                  applied, no crash.
#   C5 BEHAVIOR    200 sampled full-profiles identical + all_nodes
#                  identical after round trip.

import hashlib
import json
import lzma
import os
import pickle
import struct
import sys
import time
from collections import defaultdict

SCRATCH = (r"C:\Users\jtwee\AppData\Local\Temp\claude"
           r"\c--Users-jtwee-Downloads-New-folder--3-"
           r"\d93c0d2c-8d04-45aa-9f80-804c774fbc7e\scratchpad")
ENGINE = r"C:\Users\jtwee\Documents\isaac-project\code"
V1 = os.path.join(SCRATCH, "audit_copy.isaac")
V2 = os.path.join(SCRATCH, "probe_mind.isaac2")
sys.path.insert(0, ENGINE)
import isaac as isaac_mod                                  # noqa: E402

try:
    import numpy as np
except Exception:
    np = None

MAGIC = b"ISAAC2\x00\x01"
PRESET = 3          # lzma preset — measured 49MB in 1.2s at this level


def _pack(obj, preset=PRESET):
    return lzma.compress(
        pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL), preset=preset)


def _unpack(blob):
    return pickle.loads(lzma.decompress(blob))


# ── v2 save ──────────────────────────────────────────────────────

def save_v2(mind, path):
    net = mind.net
    # 1) set the big stores aside; empty them on the live object so
    #    the core pickle stays small. finally-restores: an exception
    #    can never leave him gutted in RAM.
    aside = dict(doors=net.doors, door_tags=net.door_tags,
                 door_counts=net.door_counts, meta=net.meta,
                 preds=net.preds, log=mind.activation_log)
    try:
        net.doors = defaultdict(set)
        net.door_tags = defaultdict(set)
        net.door_counts = defaultdict(int)
        net.meta = defaultdict(dict)
        net.preds = defaultdict(set)
        mind.activation_log = type(aside["log"])()
        core = _pack(mind)
    finally:
        net.doors, net.door_tags = aside["doors"], aside["door_tags"]
        net.door_counts, net.meta = aside["door_counts"], aside["meta"]
        net.preds = aside["preds"]
        mind.activation_log = aside["log"]

    # 2) the graph, columnar: every node name stored ONCE
    names = set(aside["doors"].keys()) | set(aside["meta"].keys())
    for tgts in aside["doors"].values():
        names |= tgts
    for (s, t) in aside["door_tags"]:
        names.add(s); names.add(t)
    for (s, t) in aside["door_counts"]:
        names.add(s); names.add(t)
    vocab = sorted(names)
    nid = {n: i for i, n in enumerate(vocab)}

    tagsets, tagset_id = [], {}
    def _tsid(fs):
        if fs not in tagset_id:
            tagset_id[fs] = len(tagsets)
            tagsets.append(sorted(fs))
        return tagset_id[fs]

    srcs, tgts_a, counts, tsids = [], [], [], []
    seen = set()
    for s, ts in aside["doors"].items():
        for t in ts:
            srcs.append(nid[s]); tgts_a.append(nid[t])
            counts.append(aside["door_counts"].get((s, t), 0))
            tsids.append(_tsid(frozenset(
                aside["door_tags"].get((s, t), set()))))
            seen.add((s, t))
    # strays: tag/count entries with no live door (old minds may
    # carry them; kept exactly — the court demands item-for-item)
    stray_tags = [(nid[s], nid[t], sorted(v))
                  for (s, t), v in aside["door_tags"].items()
                  if (s, t) not in seen]
    stray_counts = [(nid[s], nid[t], c)
                    for (s, t), c in aside["door_counts"].items()
                    if (s, t) not in seen]
    door_keys = [nid[s] for s in aside["doors"]]      # empty-set keys too
    meta_ids = {nid[k]: v for k, v in aside["meta"].items()}
    netgraph = _pack(dict(vocab=vocab, srcs=srcs, tgts=tgts_a,
                          counts=counts, tsids=tsids, tagsets=tagsets,
                          stray_tags=stray_tags,
                          stray_counts=stray_counts,
                          door_keys=door_keys, meta=meta_ids))

    history = _pack(aside["log"])

    # 3) one file: magic + json table + sections + (journal tail)
    sections = [("core", core), ("netgraph", netgraph),
                ("history", history)]
    table = []
    off = 0
    for name, blob in sections:
        table.append(dict(name=name, off=off, len=len(blob),
                          sha=hashlib.sha256(blob).hexdigest()))
        off += len(blob)
    head = json.dumps(dict(version=2, sections=table)).encode()
    tmp = path + ".writing"
    with open(tmp, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<I", len(head)))
        f.write(head)
        for _, blob in sections:
            f.write(blob)
    os.replace(tmp, path)                      # write-then-swap, kept
    return {n: len(b) for n, b in sections}


# ── v2 load ──────────────────────────────────────────────────────

def load_v2(path, replay_journal=True):
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(MAGIC):
        raise ValueError("not a v2 mind file")
    p = len(MAGIC)
    (hlen,) = struct.unpack_from("<I", data, p); p += 4
    head = json.loads(data[p:p + hlen]); p += hlen
    base = p
    sec = {}
    for s in head["sections"]:
        blob = data[base + s["off"]: base + s["off"] + s["len"]]
        if hashlib.sha256(blob).hexdigest() != s["sha"]:
            raise ValueError(f"section {s['name']} corrupt")
        sec[s["name"]] = blob
    body_end = base + sum(s["len"] for s in head["sections"])

    mind = _unpack(sec["core"])
    g = _unpack(sec["netgraph"])
    vocab = g["vocab"]
    net = mind.net
    net.doors = defaultdict(set)
    net.door_tags = defaultdict(set)
    net.door_counts = defaultdict(int)
    net.meta = defaultdict(dict)
    for k in g["door_keys"]:
        net.doors[vocab[k]]                      # restore empty entries
    tagsets = [set(ts) for ts in g["tagsets"]]
    for s_i, t_i, c, ts_i in zip(g["srcs"], g["tgts"],
                                 g["counts"], g["tsids"]):
        s, t = vocab[s_i], vocab[t_i]
        net.doors[s].add(t)
        if tagsets[ts_i]:
            net.door_tags[(s, t)] = set(tagsets[ts_i])
        if c:
            net.door_counts[(s, t)] = c
    for s_i, t_i, tags in g["stray_tags"]:
        net.door_tags[(vocab[s_i], vocab[t_i])] = set(tags)
    for s_i, t_i, c in g["stray_counts"]:
        net.door_counts[(vocab[s_i], vocab[t_i])] = c
    for k_i, v in g["meta"].items():
        net.meta[vocab[k_i]] = v
    net.preds = defaultdict(set)                 # DERIVED: rebuild
    for s, ts in net.doors.items():
        for t in ts:
            net.preds[t].add(s)
    mind.activation_log = _unpack(sec["history"])

    if replay_journal:
        applied, torn = _journal_replay(net, data, body_end)
        return mind, applied, torn
    return mind, 0, False


# ── the journal tail: autosave = append, never rewrite ──────────

def journal_append(path, ops):
    payload = pickle.dumps(ops, protocol=pickle.HIGHEST_PROTOCOL)
    rec = (struct.pack("<I", len(payload))
           + hashlib.sha256(payload).digest()[:8] + payload)
    with open(path, "ab") as f:
        f.write(rec)


def _journal_replay(net, data, pos):
    applied, torn = 0, False
    while pos < len(data):
        if pos + 12 > len(data):
            torn = True; break
        (plen,) = struct.unpack_from("<I", data, pos)
        sha = data[pos + 4: pos + 12]
        payload = data[pos + 12: pos + 12 + plen]
        if (len(payload) < plen
                or hashlib.sha256(payload).digest()[:8] != sha):
            torn = True; break
        for op in pickle.loads(payload):
            if op[0] == "add_door":
                net.add_door(op[1], op[2], tag=op[3])
            elif op[0] == "set_meta":
                net.set_meta(op[1], op[2], op[3])
        applied += 1
        pos += 12 + plen
    return applied, torn


# ── deep equality (cycle-safe, numpy-safe) ───────────────────────

def deep_eq(a, b, seen=None, path="$"):
    if seen is None:
        seen = set()
    key = (id(a), id(b))
    if key in seen:
        return True, ""
    seen.add(key)
    if type(a) is not type(b) and not (
            isinstance(a, dict) and isinstance(b, dict)):
        if np is not None and isinstance(a, np.ndarray):
            pass
        else:
            return False, f"{path}: type {type(a).__name__}" \
                          f" vs {type(b).__name__}"
    if np is not None and isinstance(a, np.ndarray):
        ok = isinstance(b, np.ndarray) and np.array_equal(a, b)
        return ok, "" if ok else f"{path}: ndarray differs"
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            d = set(a.keys()) ^ set(b.keys())
            return False, f"{path}: key diff ({len(d)} keys)"
        for k in a:
            ok, why = deep_eq(a[k], b[k], seen, f"{path}.{k!r}")
            if not ok:
                return False, why
        return True, ""
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False, f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            ok, why = deep_eq(x, y, seen, f"{path}[{i}]")
            if not ok:
                return False, why
        return True, ""
    if isinstance(a, (set, frozenset)):
        ok = a == b
        return ok, "" if ok else f"{path}: set differs"
    if hasattr(a, "__dict__") and hasattr(b, "__dict__") \
            and not isinstance(a, type):
        return deep_eq(vars(a), vars(b), seen, path + ".__dict__")
    try:
        ok = bool(a == b)
    except Exception:
        ok = False
    return ok, "" if ok else f"{path}: value differs"


# ── the run ──────────────────────────────────────────────────────

def main():
    print("ONE-FILE BODY v2 PROBE")
    t0 = time.perf_counter()
    orig = isaac_mod.Isaac.load(V1)
    print(f"v1 load: {time.perf_counter() - t0:.1f}s "
          f"({os.path.getsize(V1) / 1048576:.1f}MB)")

    t0 = time.perf_counter()
    sizes = save_v2(orig, V2)
    t_save = time.perf_counter() - t0
    v2_size = os.path.getsize(V2)
    print(f"\nC2 SIZE   v1 {os.path.getsize(V1) / 1048576:.1f}MB -> "
          f"v2 {v2_size / 1048576:.1f}MB  "
          f"({os.path.getsize(V1) / v2_size:.1f}x smaller)")
    for n, b in sizes.items():
        print(f"          section {n:9s} {b / 1048576:5.1f}MB")
    print(f"C3 SPEED  v2 save {t_save:.1f}s", end="")

    t0 = time.perf_counter()
    twin, applied, torn = load_v2(V2)
    print(f"   v2 load {time.perf_counter() - t0:.1f}s")

    # C1 the equivalence court — item for item or stop
    fails = []
    for name, a, b in [
            ("doors", dict(orig.net.doors), dict(twin.net.doors)),
            ("door_tags", dict(orig.net.door_tags),
             dict(twin.net.door_tags)),
            ("door_counts", dict(orig.net.door_counts),
             dict(twin.net.door_counts)),
            ("meta", dict(orig.net.meta), dict(twin.net.meta)),
            ("activation_log", orig.activation_log,
             twin.activation_log)]:
        ok, why = deep_eq(a, b)
        print(f"C1 {name:15s} {'EXACT' if ok else 'FAIL  ' + why}")
        if not ok:
            fails.append(name)
    # preds: derived — rebuilt vs the original's live index (report)
    ok, why = deep_eq(dict(orig.net.preds), dict(twin.net.preds))
    print(f"C1 preds(rebuilt)  {'EXACT' if ok else 'DIFFERS: ' + why}"
          f"  (derived index, report-only)")
    # every other attribute of the mind
    skip = {"net", "activation_log"}
    for name in sorted(vars(orig)):
        if name in skip:
            continue
        ok, why = deep_eq(getattr(orig, name),
                          getattr(twin, name, None))
        if not ok:
            fails.append(name)
            print(f"C1 attr {name:20s} FAIL {why}")
    n_attr = len([n for n in vars(orig) if n not in skip])
    print(f"C1 {n_attr} other attributes: "
          f"{'ALL EXACT' if not any(f not in ('doors','door_tags','door_counts','meta','activation_log') for f in fails) else 'see fails'}")

    # C5 behavior: sampled profiles + all_nodes
    nodes = sorted(orig.net.all_nodes())
    step = max(1, len(nodes) // 200)
    sample = nodes[::step][:200]
    bad = sum(1 for n in sample
              if orig.net.get_full_profile(n)
              != twin.net.get_full_profile(n))
    same_nodes = orig.net.all_nodes() == twin.net.all_nodes()
    print(f"C5 BEHAVIOR  {len(sample)} profiles: "
          f"{len(sample) - bad}/{len(sample)} identical; "
          f"all_nodes {'identical' if same_nodes else 'DIFFER'}")
    if bad or not same_nodes:
        fails.append("behavior")

    # C4 the journal: append -> reload sees it; torn tail survives
    journal_append(V2, [("add_door", "probe:a", "probe:b", "seq"),
                        ("set_meta", "probe:a", "kind", "probe")])
    journal_append(V2, [("add_door", "probe:b", "probe:c", "seq")])
    m2, applied, torn = load_v2(V2)
    j1 = (applied == 2 and not torn
          and m2.net.has_door("probe:a", "probe:b")
          and m2.net.has_door("probe:b", "probe:c")
          and m2.net.get_meta("probe:a", "kind") == "probe")
    print(f"C4 JOURNAL   append+replay: "
          f"{'GREEN' if j1 else 'FAIL'} ({applied} records)")
    with open(V2, "ab") as f:                    # tear the tail
        f.write(struct.pack("<I", 9999) + b"\x00" * 20)
    m3, applied3, torn3 = load_v2(V2)
    j2 = (applied3 == 2 and torn3
          and m3.net.has_door("probe:b", "probe:c"))
    print(f"C4 TORN TAIL survives: {'GREEN' if j2 else 'FAIL'} "
          f"(valid prefix {applied3} applied, tear detected)")
    if not (j1 and j2):
        fails.append("journal")

    print(f"\nVERDICT: {'ALL COURTS GREEN' if not fails else 'FAILS: ' + ', '.join(sorted(set(fails)))}")


if __name__ == "__main__":
    main()
