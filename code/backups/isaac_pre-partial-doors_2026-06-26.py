"""
Isaac — Unified Engine
======================

Two primitives: differentiation (comparison) and memory recursion (store + repeat).
One operation at every scale. Feed it data. It figures it out.

Pipeline:  SENSE → THINK (store ↔ route ↔ evaluate) → ACT
Active:    crystallize the working set. Real-time. O(k²).
Idle:      consolidate() — full crystallization of dirty set. O(d²).

Core:    Net, observe, consolidate, lookup, check
Logic:   logic_eval, compound decomposition
Reason:  reason_chain, is_a_check, can_check, containment, properties, syllogisms
Compute: decompose_multiply, decompose_add, compute (shrug-decompose-verify-memorize)
Solve:   forward, backward, gap-fill, multi-step
World:   state management, action teaching, execution, planning
Persist: assess consequences, plan/think/execute

No parser. No interpreter. No preprocessing. No weights.
Knowledge is doors. Structure is discovered. Everything enters, nothing leaves.
"""

from collections import defaultdict
import re
import numpy as np


# ═════════════════════════════════════════════════════════════════
# NET — doors, tags, metadata. The only data structure.
# ═════════════════════════════════════════════════════════════════

class Net:
    """The knowledge substrate. Directed graph with tagged edges (doors)."""

    def __init__(self):
        self.doors = defaultdict(set)            # node → {targets}
        self.door_tags = defaultdict(set)         # (src, tgt) → {tags}
        self.meta = defaultdict(dict)             # node → {key: value}

    def add_door(self, src, tgt, tag="seq"):
        is_new = tgt not in self.doors[src]
        self.doors[src].add(tgt)
        self.door_tags[(src, tgt)].add(tag)
        if tgt not in self.doors:
            self.doors[tgt] = set()
        return is_new

    def has_door(self, src, tgt):
        return tgt in self.doors.get(src, set())

    def get_doors(self, node, tag=None):
        all_t = self.doors.get(node, set())
        if tag is None:
            return all_t
        return {t for t in all_t if tag in self.door_tags.get((node, t), set())}

    def get_predecessors(self, node, tag=None):
        preds = set()
        for src, tgts in self.doors.items():
            if node in tgts:
                if tag is None or tag in self.door_tags.get((src, node), set()):
                    preds.add(src)
        return preds

    def get_door_tags(self, src, tgt):
        return self.door_tags.get((src, tgt), set())

    def get_full_profile(self, node):
        out = {}
        for tgt in self.doors.get(node, set()):
            out[tgt] = self.door_tags.get((node, tgt), set()).copy()
        inc = {}
        for src, tgts in self.doors.items():
            if node in tgts:
                inc[src] = self.door_tags.get((src, node), set()).copy()
        return {"out": out, "in": inc}

    def all_nodes(self):
        nodes = set(self.doors.keys())
        for tgts in self.doors.values():
            nodes.update(tgts)
        return nodes

    def set_meta(self, node, key, value):
        self.meta[node][key] = value

    def get_meta(self, node, key, default=None):
        return self.meta.get(node, {}).get(key, default)


# ═════════════════════════════════════════════════════════════════
# PRIMITIVES — compare and tokenize
# ═════════════════════════════════════════════════════════════════

def compare(set_a, set_b):
    """The single cognitive primitive. Same, different, not significant."""
    shared = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a
    total = len(shared) + len(only_a) + len(only_b)
    return {
        "shared": shared,
        "only_a": only_a,
        "only_b": only_b,
        "similarity": round(len(shared) / total * 100, 1) if total else 0,
    }


def tokenize(text):
    """Split text into tokens. Punctuation separates. Underscores preserved.
    The ONE allowed pre-net operation (Rule 2 exception):
    defines what a NODE is, not what a DOOR means."""
    return re.findall(r"[a-zA-Z0-9_]+|[^\s]", text.lower())


# ═════════════════════════════════════════════════════════════════
# SCRATCH — working memory. Registers / RAM. The mutable half.
# ═════════════════════════════════════════════════════════════════

class Scratch:
    """His working memory: named registers he writes, reads, and updates in
    real time while processing. The OTHER kind of memory from the door-net:

        door-net   = append-only, permanent, 'what is true in general'
        scratch    = overwritable, transient, 'what is true right now / this run'

    A register holds a number (a tally), a string (a note/association), or a
    list (built by appending — chainable). Every write also logs the value to a
    step-trace, so any computation can be replayed to see where it went wrong.
    """

    def __init__(self):
        self.reg = {}                    # name -> current value
        self.log = defaultdict(list)     # name -> [every value it has held]

    # ── core: write supersedes, read returns now ────────────────
    def write(self, name, value):
        """Overwrite the register. The old value is superseded (not appended,
        unlike a door) — but it is kept in the step-trace."""
        self.reg[name] = value
        self.log[name].append(value)
        return value

    def read(self, name, default=None):
        """What is in this register right NOW."""
        return self.reg.get(name, default)

    def has(self, name):
        return name in self.reg

    # ── number ops: increment / tracking ────────────────────────
    def incr(self, name, by=1):
        """count = count + 1. Creates the register at 0 if new."""
        return self.write(name, self.reg.get(name, 0) + by)

    # ── list ops: append / chain ────────────────────────────────
    def append(self, name, value):
        """Grow a register into a list — chain values onto it."""
        cur = self.reg.get(name)
        if not isinstance(cur, list):
            cur = [] if cur is None else [cur]
        cur = cur + [value]
        self.reg[name] = cur
        self.log[name].append(tuple(cur))
        return cur

    # ── latch: 'has it ever…' (sticky bit) ───────────────────────
    def latch(self, name):
        """Flip to True once and stay — memory that something HAPPENED."""
        return self.write(name, True)

    # ── introspection: the step-trace, for replay / find-the-error
    def history(self, name):
        """Every value this register has held, in order. The audit log."""
        return list(self.log[name])

    def snapshot(self):
        """The whole current working state at this instant."""
        return dict(self.reg)

    def clear(self, name=None):
        if name is None:
            self.reg.clear(); self.log.clear()
        else:
            self.reg.pop(name, None); self.log.pop(name, None)


# ═════════════════════════════════════════════════════════════════
# Isaac — the system
# ═════════════════════════════════════════════════════════════════

CONFIDENCE_THRESHOLD = 1.0

# ── crystal/box helpers (neural transplant: boxes are Isaac concepts) ──
_QLOW, _QHIGH = -7, 8

def _quantize(X, lo=None, hi=None):
    """4-bit signed quantization [-7,8] — the resolution cliff (more = noise)."""
    if lo is None:
        lo, hi = X.min(axis=0), X.max(axis=0)
    rng = np.where((hi - lo) == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng * (_QHIGH - _QLOW) + _QLOW),
                   _QLOW, _QHIGH), lo, hi

def _fisher(H, y, k):
    """Top-k dims by between-class / within-class variance (discriminative)."""
    overall = H.mean(0)
    sb = np.zeros(H.shape[1]); sw = np.zeros(H.shape[1])
    for c in np.unique(y):
        Hc = H[y == c]; mu = Hc.mean(0)
        sb += len(Hc) * (mu - overall) ** 2; sw += ((Hc - mu) ** 2).sum(0)
    sw[sw == 0] = 1e-9
    return np.argsort(-(sb / sw))[:k]


class Isaac:
    def __init__(self):
        self.net = Net()
        self.starts = set()
        self.types = {}
        self.rules = []
        self.lockouts = set()
        self.observed_sequences = []      # raw record (Rule 5: store raw)
        self.fact_index = defaultdict(list)  # (subject, relation) → [objects]
        self.scratch = Scratch()          # working memory: his registers / RAM
        self._compiled = None

        # ── pipeline state ──────────────────────────────────────
        self._compiled_up_to = 0          # how many sequences are in the matrix
        self._dirty_nodes = set()         # nodes with new doors since last consolidation
        self._consolidated_up_to = 0     # how many sequences consolidated
        self._type_profiles = {}          # cached type profiles

    # ── observation ─────────────────────────────────────────────

    def observe(self, tokens):
        """Stage 1 (SENSE): tokens in, doors built, dirty set updated,
        immediate type-slotting for known categories."""
        if not tokens:
            return
        self.starts.add(tokens[0])
        self.net.set_meta(tokens[0], "start", True)
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag="seq")
        self.observed_sequences.append(list(tokens))
        # Mark dirty — new data not yet consolidated
        for t in tokens:
            self._dirty_nodes.add(t)
        # Stage 1: immediately slot new tokens into existing types
        self._sense(tokens)

    def _sense(self, tokens):
        """Stage 1 (SENSE): check if new tokens fit existing types.
        Immediate slotting — O(k × T), runs on every observe.
        Full type discovery waits for consolidate()."""
        if not self.types:
            return
        for token in set(tokens):
            # Skip if already typed
            if self.net.get_doors(token, tag="type"):
                continue
            preds = self.net.get_predecessors(token, tag="seq")
            succs = self.net.get_doors(token, tag="seq")
            if not preds and not succs:
                continue
            for tname, tdata in self.types.items():
                tp = tdata.get("preds", set())
                ts = tdata.get("succs", set())
                shared_p = preds & tp if tp else set()
                shared_s = succs & ts if ts else set()
                if len(shared_p) + len(shared_s) >= 2:
                    tdata["members"].add(token)
                    self.net.add_door(token, tname, tag="type")
                    break

    def observe_negative(self, tokens):
        """Same mechanism, different tag. Negation is contrast, not storage."""
        if not tokens:
            return
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag="neg")

    def observe_matrix(self, matrix, row_prefix=None):
        """Observe a 2D data matrix. Each row becomes a sequence of tokens.
        No preprocessing. No feature extraction. Just the numbers.

        matrix: 2D numpy array or list of lists
        row_prefix: optional prefix per row (e.g., 'r0', 'r1', ...) for position
        """
        for i, row in enumerate(matrix):
            tokens = [str(int(v)) for v in row]
            if row_prefix:
                tokens.insert(0, f"{row_prefix}{i}")
            self.observe(tokens)

    def observe_frame(self, frame, label=None):
        """Observe a full video/game frame as a matrix.
        Handles 2D (grayscale) or 3D (color) arrays.
        Flattens color channels per pixel. Each row is one observation.

        frame: numpy array (H, W) or (H, W, C)
        label: optional frame label (e.g., 'f0', 'f1', ...) prepended to first row
        """
        if frame.ndim == 3:
            # Color frame: flatten channels per pixel
            h, w, c = frame.shape
            flat = frame.reshape(h, w * c)
        else:
            flat = frame

        for i, row in enumerate(flat):
            tokens = [str(int(v)) for v in row]
            if label and i == 0:
                tokens.insert(0, label)
            self.observe(tokens)

    def observe_tagged(self, tokens, tag):
        """Observe with a custom tag. Properties, relations, anything."""
        if not tokens:
            return
        for i in range(len(tokens) - 1):
            self.net.add_door(tokens[i], tokens[i + 1], tag=tag)

    def teach(self, subject, relation, obj):
        """Teach a fact. Observes as a sequence AND indexes for relation lookup."""
        self.observe(tokenize(f"{subject} {relation} {obj}"))
        self.fact_index[(subject, relation)].append(obj)

    # ── crystallization ─────────────────────────────────────────

    def _crystallize(self, tag="seq", min_shared=2, verbose=False, scope=None):
        """Internal: discover types by comparing door profiles. FCA closure.
        If scope is provided, only pairs involving at least one scope node
        are compared — O(d×n) instead of O(n²)."""
        nodes = sorted([n for n in self.net.all_nodes()
                        if not n.startswith("type:")])
        scope_set = set(scope) if scope else None

        # Phase 1: raw circles via FCA
        circles = []
        seen = set()
        seen_pairs = set()
        for i, a in enumerate(nodes):
            preds_a = self.net.get_predecessors(a, tag=tag)
            succs_a = self.net.get_doors(a, tag=tag)
            if not preds_a and not succs_a:
                continue
            for b in nodes[i + 1:]:
                # Scoped: skip pairs where neither node is dirty
                if scope_set and a not in scope_set and b not in scope_set:
                    continue
                preds_b = self.net.get_predecessors(b, tag=tag)
                succs_b = self.net.get_doors(b, tag=tag)
                shared_p = preds_a & preds_b
                shared_s = succs_a & succs_b
                if len(shared_p) + len(shared_s) < min_shared:
                    continue
                members = {a, b}
                for n in nodes:
                    if n in members:
                        continue
                    np_ = self.net.get_predecessors(n, tag=tag)
                    ns_ = self.net.get_doors(n, tag=tag)
                    if shared_p <= np_ and shared_s <= ns_:
                        members.add(n)
                key = frozenset(members)
                if key not in seen and len(members) >= 2:
                    seen.add(key)
                    circles.append({"members": members,
                                    "preds": shared_p, "succs": shared_s})

        # Phase 2: merge overlapping circles (Rule 13)
        merged = []
        used = set()
        circles.sort(key=lambda c: len(c["members"]), reverse=True)
        for i, c in enumerate(circles):
            if i in used:
                continue
            current = {"members": set(c["members"]),
                       "preds": set(c["preds"]), "succs": set(c["succs"])}
            for j in range(i + 1, len(circles)):
                if j in used:
                    continue
                other = circles[j]
                smaller = min(len(current["members"]), len(other["members"]))
                overlap = len(current["members"] & other["members"])
                if smaller > 0 and overlap / smaller >= 0.8:
                    current["members"] |= other["members"]
                    current["preds"] &= other["preds"]
                    current["succs"] &= other["succs"]
                    used.add(j)
            merged.append(current)

        # Phase 3: name and write to net
        self.types = {}
        for c in merged:
            name = f"type:{'_'.join(sorted(c['members'])[:2])}[{len(c['members'])}]"
            c["name"] = name
            c["parent"] = None
            c["children"] = []
            self.types[name] = c
            for m in c["members"]:
                self.net.add_door(m, name, tag="type")

        # Phase 4: hierarchy (subset = child)
        type_list = list(self.types.values())
        for child in type_list:
            for parent in type_list:
                if child is parent:
                    continue
                if len(child["members"]) >= len(parent["members"]):
                    continue
                overlap = len(child["members"] & parent["members"])
                if overlap / len(child["members"]) >= 0.8:
                    child["parent"] = parent["name"]
                    parent["children"].append(child["name"])
                    self.net.add_door(child["name"], parent["name"],
                                     tag="subtype_of")
                    break

        # Phase 5: discover rules (co-occurring predecessors)
        self.rules = []
        pred_sets = defaultdict(set)
        for n in nodes:
            for p in self.net.get_predecessors(n, tag=tag):
                pred_sets[p].add(n)
        preds = [p for p, ns in pred_sets.items() if len(ns) >= 3]
        for i, a in enumerate(preds):
            for b in preds[i + 1:]:
                overlap = len(pred_sets[a] & pred_sets[b])
                ratio_a = overlap / len(pred_sets[a]) if pred_sets[a] else 0
                ratio_b = overlap / len(pred_sets[b]) if pred_sets[b] else 0
                if ratio_a >= 0.8 or ratio_b >= 0.8:
                    self.rules.append((a, b, round(max(ratio_a, ratio_b), 2)))
                    self.net.add_door(a, b, tag="cooccurs")

        # Phase 6: violations (seq vs neg contrast)
        self._discover_violations()

        # Phase 7: initiator ranking
        for s in self.starts:
            strength = len(self.net.get_doors(s, tag="seq"))
            self.net.set_meta(s, "initiator_strength", strength)

        if verbose:
            print(f"  crystallized: {len(self.types)} types, "
                  f"{len(self.rules)} rules, {len(self.lockouts)} lockouts")
        return self.types

    def _discover_violations(self):
        """Compare seq doors vs neg doors. The difference IS negation."""
        seq_pairs = set()
        neg_pairs = set()
        for (src, tgt), tags in self.net.door_tags.items():
            if "seq" in tags:
                seq_pairs.add((src, tgt))
            if "neg" in tags:
                neg_pairs.add((src, tgt))
        for src, tgt in (neg_pairs - seq_pairs):
            self.net.add_door(src, tgt, tag="lockout")
            self.lockouts.add((src, tgt))

    # ── compilation ─────────────────────────────────────────────
    # Doors → matrix. Same information, different representation.
    # W[delta, frame] = door count. y = W @ x. Answer from y.

    def _ensure_compiled(self):
        """Stage 3 (ROUTE): lazy compilation. Only recompile if dirty.
        Called automatically before any inference. Never call compile() manually."""
        if self._compiled_up_to < len(self.observed_sequences):
            self._compile()
        return self._compiled is not None

    def _compile(self, max_context=7):
        """Internal: build the weight matrix from observed sequences."""
        pairs = []
        for seq in self.observed_sequences:
            if len(seq) < 2:
                continue
            frame = tuple(seq[:-1])
            delta = seq[-1]
            pairs.append((frame, delta))
            for width in range(2, min(len(frame) + 1, max_context)):
                partial = frame[-width:]
                if partial != frame:
                    pairs.append((partial, delta))

        if not pairs:
            self._compiled = None
            self._compiled_up_to = len(self.observed_sequences)
            return None

        frames = sorted(set(f for f, d in pairs))
        deltas = sorted(set(d for f, d in pairs))
        fidx = {f: i for i, f in enumerate(frames)}
        didx = {d: i for i, d in enumerate(deltas)}

        W = np.zeros((len(deltas), len(frames)), dtype=np.float32)
        for frame, delta in pairs:
            W[didx[delta], fidx[frame]] += 1.0
        col_sums = W.sum(axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1
        W_norm = W / col_sums

        self._compiled = {
            "W": W, "W_norm": W_norm,
            "frames": frames, "deltas": deltas,
            "fidx": fidx, "didx": didx,
        }
        self._compiled_up_to = len(self.observed_sequences)
        return {
            "frames": len(frames), "deltas": len(deltas),
            "nonzero": int((W != 0).sum()),
            "matrix_shape": W.shape,
        }

    def compile(self, max_context=7):
        """Convenience wrapper. Prefer automatic compilation via lookup/check."""
        return self._compile(max_context)

    def consolidate(self, tag="seq", min_shared=2, verbose=False, full=False):
        """IDLE MODE: Crystallization of dirty regions.
        Run when nothing is waiting. This is sleep.

        By default, scopes to dirty nodes — O(d×n) instead of O(n²).
        Pass full=True to force a complete re-crystallization."""
        scope = None if full or not self._dirty_nodes else list(self._dirty_nodes)
        result = self._crystallize(tag=tag, min_shared=min_shared,
                                   verbose=verbose, scope=scope)
        self._consolidated_up_to = len(self.observed_sequences)
        self._dirty_nodes.clear()
        return result

    def crystallize(self, tag="seq", min_shared=2, verbose=False):
        """Convenience alias. Runs full (unscoped) consolidation."""
        return self.consolidate(tag=tag, min_shared=min_shared,
                                verbose=verbose, full=True)

    def _encode(self, context):
        """Encode context tokens into the input vector.
        Full frame gets highest weight. Partial trailing frames get lower.
        Phase 6: when direct frames miss, try type-member substitution."""
        if not self._compiled:
            return None
        c = self._compiled
        x = np.zeros(len(c["frames"]), dtype=np.float32)

        # Direct frame matching
        frame = tuple(context)
        if frame in c["fidx"]:
            x[c["fidx"][frame]] = 16.0
        for width in range(2, min(len(context) + 1, 8)):
            partial = tuple(context[-width:])
            if partial in c["fidx"] and partial != frame:
                x[c["fidx"][partial]] = float(width)

        # Phase 6: type-level attention
        # If no direct frames matched, try substituting tokens with
        # their type members. Activate ALL matches — let the matmul
        # resolve which type member is most relevant. Weight lower
        # than direct (8.0 vs 16.0) so direct always wins.
        if x.sum() == 0 and self.types:
            for i, token in enumerate(context):
                type_doors = self.net.get_doors(token, tag="type")
                for tname in type_doors:
                    tdata = self.types.get(tname)
                    if not tdata:
                        continue
                    for member in sorted(tdata["members"]):
                        if member == token:
                            continue
                        # Try full frame with this substitution
                        trial = list(context)
                        trial[i] = member
                        trial_frame = tuple(trial)
                        if trial_frame in c["fidx"]:
                            x[c["fidx"][trial_frame]] += 8.0
                        # Try partial frames with substitution
                        for w in range(2, min(len(trial) + 1, 8)):
                            partial = tuple(trial[-w:])
                            if partial in c["fidx"] and partial != trial_frame:
                                x[c["fidx"][partial]] += float(w) * 0.5

        return x if x.sum() > 0 else None

    # ── inference (matrix) ──────────────────────────────────────
    # The THINK loop: recall → process → evaluate → repeat until stable.
    # Memory sends forward. Evaluation sends back. Loop until settled.

    def _route(self, context, mode="lookup", target=None):
        """Stage 3 (ROUTE): single matmul pass. Returns (answer, confidence)."""
        x = self._encode(context)
        if x is None:
            if mode == "check":
                return False, 0.0
            return None, 0.0
        y = self._compiled["W_norm"] @ x
        if mode == "check":
            if target not in self._compiled["didx"]:
                return False, 0.0
            score = float(y[self._compiled["didx"][target]])
            return score >= CONFIDENCE_THRESHOLD, score
        else:
            idx = y.argsort()[-1]
            answer = self._compiled["deltas"][idx]
            conf = float(y[idx])
            if conf < CONFIDENCE_THRESHOLD:
                return None, conf
            return answer, conf

    def _recall(self, context):
        """Stage 2 (STORE/RECALL): What do I know about these tokens?
        Pull types, related tokens, known facts, door profiles.
        This is memory sending information forward to processing."""
        knowledge = {}
        for token in context:
            types = list(self.net.get_doors(token, tag="type"))
            successors = self.net.get_doors(token, tag="seq")
            predecessors = self.net.get_predecessors(token, tag="seq")
            # Tokens with rich profiles are well-known.
            # Tokens with empty profiles are novel/unknown.
            type_members = set()
            for t in types:
                for n in self.net.all_nodes():
                    if t in self.net.get_doors(n, tag="type"):
                        type_members.add(n)
                type_members.discard(token)
            knowledge[token] = {
                "types": types,
                "successors": successors,
                "predecessors": predecessors,
                "type_members": type_members,
                "known": len(successors) > 0 or len(predecessors) > 0,
            }
        return knowledge

    def _evaluate(self, answer, conf, context, knowledge, mode):
        """Stage 4 (EVALUATE): Is this answer good? What should we do next?
        Returns a verdict dict — stable, or what to try next.
        This is evaluation sending feedback back to memory/processing.

        Critical distinction:
          - conf > 0 but < threshold: system has SOME info, just weak → don't substitute
          - conf == 0 and no frames match: genuine unknown → try substitution
          - answer found but wrong target: definite no, not unknown"""
        verdict = {"stable": False, "answer": answer, "conf": conf}

        # Confident answer → stable
        if conf >= CONFIDENCE_THRESHOLD:
            verdict["stable"] = True
            return verdict

        # Check: did the encoding produce ANY activation?
        # If yes, the system has info — just not for this target.
        # That's a real 'no', not an 'I don't know'.
        has_some_info = False
        if self._compiled:
            x = self._encode(context)
            if x is not None:
                y = self._compiled["W_norm"] @ x
                if y.max() >= CONFIDENCE_THRESHOLD:
                    has_some_info = True

        # Which tokens are unknown?
        unknown_tokens = [t for t in context
                          if not knowledge.get(t, {}).get("known", False)]
        known_tokens = [t for t in context
                        if knowledge.get(t, {}).get("known", False)]

        verdict["unknown_tokens"] = unknown_tokens
        verdict["known_tokens"] = known_tokens

        # If we have unknown tokens, suggest dropping them
        if unknown_tokens and len(known_tokens) >= 2:
            verdict["try_known_only"] = known_tokens

        # Only try type substitution when the system has NO info at all.
        # If it has info but the target doesn't match, that's a real 'no'.
        elif not unknown_tokens and not has_some_info:
            verdict["try_type_substitution"] = True

        return verdict

    def _think(self, context, mode="lookup", target=None, max_cycles=5):
        """Stages 2/3/4 loop. Recall → Process → Evaluate → repeat.

        Memory sends knowledge forward to processing.
        Processing sends results forward to evaluation.
        Evaluation sends feedback back to memory/processing.
        Loop until the answer stabilizes or we've exhausted what we know.

        Exit conditions (governor):
          1. Confidence >= threshold → stable
          2. Evaluation says stable (exhausted all strategies)
          3. Max cycles reached
        """
        self._ensure_compiled()
        if not self._compiled:
            return (None, 0.0) if mode == "lookup" else (False, 0.0)

        # ── Stage 2: RECALL — what do I know about this? ────────
        knowledge = self._recall(context)

        best_answer = None
        best_conf = 0.0
        tried = set()  # track what we've already attempted

        for cycle in range(max_cycles):
            # ── Stage 3: PROCESS — compute against what I know ──
            context_key = tuple(context)
            if context_key not in tried:
                tried.add(context_key)
                answer, conf = self._route(context, mode, target)

                if conf > best_conf:
                    best_answer, best_conf = answer, conf

                # ── Stage 4: EVALUATE — is this good enough? ────
                verdict = self._evaluate(answer, conf, context, knowledge, mode)

                if verdict["stable"]:
                    return answer, conf

            # ── Evaluation feedback → back to memory/processing ─
            # The verdict tells us what to try next

            # Strategy A: drop unknown tokens, keep what we know
            known_only = verdict.get("try_known_only")
            if known_only and tuple(known_only) not in tried:
                context = known_only
                # Recall again with the simplified context
                knowledge = self._recall(context)
                continue

            # Strategy B: type substitution — replace unknown tokens
            # with type members from related known tokens
            if verdict.get("try_type_substitution"):
                found = False
                for i, token in enumerate(context):
                    members = knowledge.get(token, {}).get("type_members", set())
                    for member in sorted(members):
                        trial = list(context)
                        trial[i] = member
                        trial_key = tuple(trial)
                        if trial_key not in tried:
                            tried.add(trial_key)
                            answer, conf = self._route(trial, mode, target)
                            if conf > best_conf:
                                best_answer, best_conf = answer, conf
                            if conf >= CONFIDENCE_THRESHOLD:
                                return answer, conf
                            found = True
                if found:
                    continue

            # Strategy C: try each known token paired with the tail
            # (verb-level: "smash" + "result")
            if len(context) > 2:
                tail = context[-1]
                for token in context[:-1]:
                    pair_key = (token, tail)
                    if pair_key not in tried:
                        tried.add(pair_key)
                        answer, conf = self._route(list(pair_key), mode, target)
                        if conf > best_conf:
                            best_answer, best_conf = answer, conf
                        if conf >= CONFIDENCE_THRESHOLD:
                            return answer, conf

            # Nothing more to try — return best we found
            break

        return best_answer, best_conf

    def lookup(self, context, top_k=5):
        """Argmax over the output vector. 'What comes next?'
        Routes through the think loop — recall, process, evaluate."""
        return self._think(context, mode="lookup")

    def check(self, context, target):
        """Read a SPECIFIC cell in y. 'Is THIS claim true?'
        Routes through the think loop — recall, process, evaluate."""
        return self._think(context, mode="check", target=target)

    # ── walking (net) ───────────────────────────────────────────

    def predict_next(self, context, tag="seq"):
        """Convergence voting from context words. For language, not math."""
        if not context:
            return None
        votes = defaultdict(int)
        voters = defaultdict(list)
        for word in context:
            for tgt in self.net.get_doors(word, tag=tag):
                if (word, tgt) not in self.lockouts:
                    votes[tgt] += 1
                    voters[tgt].append(word)
        if not votes:
            return None
        max_votes = max(votes.values())
        candidates = [c for c, v in votes.items() if v == max_votes]

        def recency(c):
            positions = [context.index(w) for w in voters[c] if w in context]
            return max(positions) if positions else -1
        winner = max(candidates, key=recency)
        return {"prediction": winner, "votes": votes[winner],
                "total_voters": len(context),
                "all_candidates": dict(votes)}

    def walk_chain(self, start, tag="seq", max_steps=20):
        """Walk forward from start, following doors."""
        chain = [start]
        current = start
        visited = {start}
        for _ in range(max_steps):
            nexts = self.net.get_doors(current, tag=tag) - visited
            nexts = {n for n in nexts if (current, n) not in self.lockouts}
            if not nexts:
                break
            best = max(nexts, key=lambda n: (
                self.net.get_meta(n, "initiator_strength") or 0, n))
            chain.append(best)
            visited.add(best)
            current = best
        return chain

    def transduce(self, start, stream, into="state", halt=None,
                  max_steps=None, verbose=False):
        """Universal state walk over an input stream — the missing primitive.

        Thread a state through a sequence of input symbols. At each step the
        NEXT state is chosen by HIS matrix: lookup([state, symbol]) -> state'.
        The transition function delta(state, symbol)=state' lives entirely in
        learned doors (a real frame->delta), so no task logic sits in Python.

        This is the finite-state-transducer / Turing-head shape: the loop here
        is the universal tape-reader (general, the same for every machine); the
        PROGRAM is whatever transitions were taught. Counting, parity, motion,
        and the game loop all reuse this — they differ only in their doors.

        The state is held in a working-memory register (`into`), so it lives in
        HIM across steps — read from scratch and written back each step. The
        harness loop holds nothing but the next symbol.

        Returns (final_state, trace). final_state is None on an honest shrug
        (no transition learned for some [state, symbol]); trace is the register's
        full step-history (scratch.history(into)).
        """
        self.scratch.clear(into)                       # fresh episode
        self.scratch.write(into, start)                # state lives in HIM
        steps = 0
        for symbol in stream:
            state = self.scratch.read(into)            # he reads his own state
            nxt, conf = self.lookup([state, symbol])   # his matmul decides
            if nxt is None or conf < CONFIDENCE_THRESHOLD:
                if verbose:
                    print(f"    shrug at step {steps}: no door for "
                          f"[{state}, {symbol}]")
                return None, self.scratch.history(into)  # honest: rule unlearned
            self.scratch.write(into, nxt)              # he writes it back into himself
            steps += 1
            if verbose:
                print(f"    {symbol:>4} -> {nxt}  (conf {conf:.1f})")
            if halt is not None and nxt == halt:
                break
            if max_steps is not None and steps >= max_steps:
                break
        return self.scratch.read(into), self.scratch.history(into)

    def _apply_op(self, op, target):
        """The tiny ALU: execute one named op against a working register.
        Fixed instruction set (like a CPU's decoder); the PROGRAM — which op to
        run when — is in his net, not here."""
        if op == "incr":
            self.scratch.incr(target)
        elif op == "hold":
            pass
        elif op == "reset":
            self.scratch.write(target, 0)
        elif op == "mark":
            self.scratch.latch(target + "_seen")
        else:
            return False                               # unknown op -> shrug
        return True

    def react(self, stream, target="acc", verbose=False):
        """Run an input stream against his ACTION doors, updating working memory
        in real time. For each symbol his matrix says what to DO
        (lookup([symbol]) -> an op token); the ALU applies it to `target`.

        The program (which op fires for which symbol) is HIS — learned doors.
        The register is HIS. Only 'apply a named op' is engine plumbing. This is
        counting-without-a-state-ladder: 'on'->incr, 'off'->hold lets him count
        to ANY N with two doors, because the magnitude lives in RAM, not in the
        graph as N separate nodes.
        """
        self.scratch.clear(target)                     # fresh episode
        self.scratch.write(target, 0)
        for symbol in stream:
            op, conf = self.lookup([symbol])           # his matmul: what to do
            if op is None or conf < CONFIDENCE_THRESHOLD:
                if verbose:
                    print(f"    {symbol:>4}: (no instruction — skip)")
                continue
            self._apply_op(op, target)
            if verbose:
                print(f"    {symbol:>4} -> {op:<6} {target}={self.scratch.read(target)}")
        return self.scratch.read(target), self.scratch.history(target)

    def generate(self, concept, tag="seq"):
        """Generate a sequence containing the concept.
        Trace backward to find an initiator, then forward to completion."""
        backward = []
        current = concept
        visited = {concept}
        for _ in range(10):
            preds = self.net.get_predecessors(current, tag=tag)
            preds = {p for p in preds if p not in visited
                     and (p, current) not in self.lockouts}
            if not preds:
                break
            starts = {p for p in preds if self.net.get_meta(p, "start")}
            if starts:
                best = max(starts, key=lambda p: (
                    self.net.get_meta(p, "initiator_strength") or 0))
                backward.append(best)
                break
            best = max(preds, key=lambda p: len(self.net.get_doors(p, tag=tag)))
            backward.append(best)
            visited.add(best)
            current = best
        backward.reverse()
        chain = backward + [concept]
        current = concept
        for _ in range(10):
            nexts = self.net.get_doors(current, tag=tag) - visited
            nexts = {n for n in nexts if (current, n) not in self.lockouts}
            if not nexts:
                break
            best = sorted(nexts)[0]
            chain.append(best)
            visited.add(best)
            current = best
            if best in (".", "!", "?", "="):
                break
        return chain

    def check_connection(self, src, tgt):
        """Is src→tgt valid? Walk the full net to check. Returns (valid, manifest)."""
        manifest = {"direct_seq": False, "direct_neg": False,
                    "lockout": False, "types_checked": [],
                    "type_support": 0, "type_contradict": 0}
        tags = self.net.get_door_tags(src, tgt)
        if "seq" in tags:
            manifest["direct_seq"] = True
        if "neg" in tags:
            manifest["direct_neg"] = True
        if (src, tgt) in self.lockouts:
            manifest["lockout"] = True
            return False, manifest
        src_types = self.net.get_doors(src, tag="type")
        for t in src_types:
            members = {n for n in self.net.all_nodes()
                       if t in self.net.get_doors(n, tag="type")}
            members.discard(src)
            support = any(self.net.has_door(m, tgt) for m in members)
            manifest["types_checked"].append({"type": t, "support": support})
            if support:
                manifest["type_support"] += 1
            else:
                manifest["type_contradict"] += 1
        valid = manifest["direct_seq"] or manifest["type_support"] > 0
        if manifest["lockout"]:
            valid = False
        return valid, manifest

    def compare_nodes(self, a, b, tag=None):
        """Structural comparison of two nodes."""
        return {
            "outgoing": compare(set(self.net.get_doors(a, tag=tag)),
                                set(self.net.get_doors(b, tag=tag))),
            "incoming": compare(self.net.get_predecessors(a, tag=tag),
                                self.net.get_predecessors(b, tag=tag)),
        }

    def infer(self, src, tgt, tag="seq"):
        """Can src connect to tgt? Walk types to find out."""
        src_types = self.net.get_doors(src, tag="type")
        for t in src_types:
            members = {n for n in self.net.all_nodes()
                       if t in self.net.get_doors(n, tag="type")}
            for m in members:
                if m != src and self.net.has_door(m, tgt):
                    self.net.add_door(src, tgt, tag=tag)
                    return {"inferred": True, "via": m, "type": t}
        return {"inferred": False}

    # ── crystal: transplant a net/features into box-concepts IN THE NET ──

    def fit_lens(self, name, X, y=None, lift=0, select=None, seed=0):
        """Register an ALIGNER as net infrastructure: optional random lift
        (spread the data so classes pull apart) + strip-DC (centering, his
        'remove the shared') + discriminative dim-select. It is WIRED now but
        lives in the net as a 'lens:<name>' node, so a learned aligner (his
        crystallizer finding the box-friendly view) can replace it later with
        the same interface. This is the alignment step, made his, made swappable."""
        g = np.random.default_rng(seed); R = b = None; H = np.asarray(X, float)
        if lift:
            R = g.standard_normal((H.shape[1], lift)) / np.sqrt(H.shape[1])
            b = g.standard_normal(lift) * 0.1
            H = np.maximum(H @ R + b, 0.0)
        dc = H.mean(0); Hc = H - dc
        dims = (_fisher(Hc, y, select)
                if (select and y is not None and select < Hc.shape[1]) else None)
        node = f"lens:{name}"
        self.net.add_door("lens", node, tag="lens")
        self.net.set_meta(node, "transform", dict(R=R, b=b, dc=dc, dims=dims))
        return name

    def apply_lens(self, name, X):
        """Run an input through a registered lens. None = identity."""
        if name is None:
            return np.asarray(X, float)
        t = self.net.get_meta(f"lens:{name}", "transform") or {}
        H = np.asarray(X, float)
        if t.get("R") is not None:
            H = np.maximum(H @ t["R"] + t["b"], 0.0)
        if t.get("dc") is not None:
            H = H - t["dc"]
        if t.get("dims") is not None:
            H = H[:, t["dims"]]
        return H

    def crystallize_features(self, X, y, lens=None, margin=1.5):
        """Transplant: one box-concept per class as a NODE in the net, with
        per-dim [lo,hi,med] in its meta, tagged 'crystal'. These concepts sit in
        the same net as his language/math knowledge — one substrate."""
        H = self.apply_lens(lens, X)
        Hq, qlo, qhi = _quantize(H)
        for c in np.unique(y):
            obs = Hq[y == c]
            self.net.add_door("crystal", f"concept:{c}", tag="crystal")
            self.net.set_meta(f"concept:{c}", "box", dict(
                lo=np.percentile(obs, 1, axis=0) - margin,
                hi=np.percentile(obs, 95, axis=0) + margin,
                med=np.median(obs, axis=0)))
            self.net.set_meta(f"concept:{c}", "label", c)
        self.net.set_meta("crystal", "calib", dict(qlo=qlo, qhi=qhi, lens=lens))
        return sorted(self.net.get_doors("crystal", tag="crystal"))

    def classify_features(self, X):
        """Classify by his membership (count in-range) + centroid (median dist)
        over the crystal concept-nodes. Lens + boxes both live in the net."""
        calib = self.net.get_meta("crystal", "calib")
        H = self.apply_lens(calib["lens"], np.atleast_2d(np.asarray(X, float)))
        Hq, _, _ = _quantize(H, calib["qlo"], calib["qhi"])
        boxes = [(self.net.get_meta(n, "label"), self.net.get_meta(n, "box"))
                 for n in sorted(self.net.get_doors("crystal", tag="crystal"))]
        out = []
        for xi in Hq:
            best, bc, bd = None, -1, 1e18
            for label, bx in boxes:
                inr = (xi >= bx["lo"]) & (xi <= bx["hi"]); cnt = int(inr.sum())
                dist = float(np.abs(xi[inr] - bx["med"][inr]).sum()) if cnt else 1e18
                if cnt > bc or (cnt == bc and dist < bd):
                    bc, bd, best = cnt, dist, label
            out.append(best)
        return np.array(out)

    # ── sense routing: internal node routers (conditional / binding) ──

    def crystallize_senses(self, node, min_shared=2):
        """Split a node's flat doors into SENSE-SECTIONS, stored ON the node.
        Each occurrence of the node carries the context it appeared in; cluster
        occurrences by shared context (the crystallizer, turned inward on one
        node); each cluster is a sense with its own in-doors and out-doors.
        This is what gives the node internal structure instead of a flat pile."""
        occ = []  # (context_set, pred, succ) per occurrence
        for seq in self.observed_sequences:
            for k, t in enumerate(seq):
                if t == node:
                    occ.append((set(seq) - {node},
                                seq[k - 1] if k > 0 else None,
                                seq[k + 1] if k + 1 < len(seq) else None))
        n = len(occ)
        parent = list(range(n))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a in range(n):              # link occurrences sharing >= min_shared context words
            for b in range(a + 1, n):
                if len(occ[a][0] & occ[b][0]) >= min_shared:
                    parent[find(a)] = find(b)
        comps = defaultdict(lambda: {"in": set(), "out": set(), "context": set()})
        for i, (ctx, p, s) in enumerate(occ):
            r = find(i)
            if p: comps[r]["in"].add(p)
            if s: comps[r]["out"].add(s)
            comps[r]["context"] |= ctx
        senses = list(comps.values())
        self.net.set_meta(node, "senses", senses)
        return senses

    def route(self, node, incoming):
        """Route through the node by which sense the incoming context matches.
        incoming = a token or a set of context tokens. Returns that sense's
        out-doors; falls back to the flat door-set if no sense matches."""
        senses = self.net.get_meta(node, "senses") or []
        inc = {incoming} if isinstance(incoming, str) else set(incoming)
        best, best_ov = None, 0
        for sense in senses:
            ov = len(inc & (sense["in"] | sense["context"]))
            if ov > best_ov:
                best_ov, best = ov, sense
        return best["out"] if best else set(self.net.get_doors(node, tag="seq"))

    # ── logic ───────────────────────────────────────────────────

    def logic_eval(self, expression, verbose=False):
        """Evaluate a logic expression via chained matmul lookups.
        Decompose-when-shrug: compound → single-gate lookups."""
        tokens = expression.lower().split()
        result, trace = self._logic_reduce(tokens, verbose)
        return result, trace

    def _logic_reduce(self, tokens, verbose=False):
        trace = []
        while len(tokens) >= 2 and tokens[0] == "(" and tokens[-1] == ")":
            tokens = tokens[1:-1]
        if len(tokens) == 1:
            return tokens[0], trace
        if tokens[0] == "not":
            inner, inner_trace = self._logic_reduce(tokens[1:], verbose)
            trace.extend(inner_trace)
            context = ["not", inner, "="]
            answer, conf = self.lookup(context)
            trace.append({"op": f"not {inner}", "answer": answer, "conf": conf})
            if verbose:
                print(f"    not {inner} → {answer} (conf={conf:.1f})")
            return answer, trace
        main_op_idx = self._find_main_op(tokens)
        if main_op_idx is not None:
            left_tokens = tokens[:main_op_idx]
            op = tokens[main_op_idx]
            right_tokens = tokens[main_op_idx + 1:]
            left_val, lt = self._logic_reduce(left_tokens, verbose)
            trace.extend(lt)
            right_val, rt = self._logic_reduce(right_tokens, verbose)
            trace.extend(rt)
            context = [left_val, op, right_val, "="]
            answer, conf = self.lookup(context)
            trace.append({"op": f"{left_val} {op} {right_val}",
                          "answer": answer, "conf": conf})
            if verbose:
                print(f"    {left_val} {op} {right_val} → {answer} (conf={conf:.1f})")
            return answer, trace
        return " ".join(tokens), trace

    def _find_main_op(self, tokens):
        ops_by_precedence = [{"implies"}, {"or", "nor"}, {"xor"},
                             {"and", "nand"}, {"equals"}]
        depth = 0
        for prec_level in ops_by_precedence:
            for i, t in enumerate(tokens):
                if t == "(":
                    depth += 1
                elif t == ")":
                    depth -= 1
                elif depth == 0 and t in prec_level and i > 0:
                    return i
        return None

    # ── reasoning ───────────────────────────────────────────────

    def reason_chain(self, subject, relation, verbose=False):
        """Follow a relation chain via matmul hops. Each hop is one matmul."""
        chain = [subject]
        current = subject
        visited = {subject}
        for step in range(20):
            answer, conf = self.lookup([current, relation])
            if answer is None or conf < CONFIDENCE_THRESHOLD or answer in visited:
                break
            chain.append(answer)
            visited.add(answer)
            current = answer
            if verbose:
                print(f"    hop {step}: {chain[-2]} {relation} → {answer}"
                      f" (conf={conf:.1f})")
        return chain

    def is_a_check(self, subject, target, verbose=False):
        """Is subject a target? Walk the is_a chain."""
        chain = self.reason_chain(subject, "is_a", verbose=verbose)
        return target in chain, chain

    def can_check(self, subject, ability, verbose=False):
        """Can subject do ability? Negative first, then direct, then inherited.
        Each check is one matmul reading a specific cell."""
        # Step 1: negative blocks everything
        neg_match, neg_conf = self.check([subject, "cannot"], ability)
        if neg_match:
            if verbose:
                print(f"    {subject} cannot {ability} → BLOCKED (conf={neg_conf:.1f})")
            return False, [subject]
        # Step 2: direct capability
        direct_match, direct_conf = self.check([subject, "can"], ability)
        if direct_match:
            if verbose:
                print(f"    {subject} can {ability} → YES (direct, conf={direct_conf:.1f})")
            return True, [subject]
        # Step 3: walk is_a chain, check each ancestor
        chain = self.reason_chain(subject, "is_a")
        for ancestor in chain[1:]:
            aneg, aneg_conf = self.check([ancestor, "cannot"], ability)
            if aneg:
                if verbose:
                    print(f"    {ancestor} cannot {ability} → BLOCKED")
                return False, chain[:chain.index(ancestor) + 1]
            amatch, aconf = self.check([ancestor, "can"], ability)
            if amatch:
                if verbose:
                    print(f"    {subject} can {ability} → YES"
                          f" (inherited from {ancestor}, conf={aconf:.1f})")
                return True, chain[:chain.index(ancestor) + 1]
        # Step 4: fact index fallback (for multi-valued relations)
        direct_facts = self.fact_index.get((subject, "can"), [])
        if ability in direct_facts:
            if verbose:
                print(f"    {subject} can {ability} → YES (fact index)")
            return True, [subject]
        for ancestor in chain[1:]:
            ancestor_facts = self.fact_index.get((ancestor, "can"), [])
            if ability in ancestor_facts:
                if verbose:
                    print(f"    {subject} can {ability} → YES"
                          f" (inherited from {ancestor} via fact index)")
                return True, chain[:chain.index(ancestor) + 1]
        if verbose:
            print(f"    {subject} can {ability} → UNKNOWN")
        return None, chain

    def containment_check(self, item, container, verbose=False):
        """Is item in container? Walk the 'in' chain."""
        chain = self.reason_chain(item, "in", verbose=verbose)
        return container in chain, chain

    def property_check(self, subject, verbose=False):
        """What properties does subject have? Direct + inherited."""
        properties = []
        direct = self.fact_index.get((subject, "has"), [])
        for p in direct:
            properties.append((p, "direct"))
        chain = self.reason_chain(subject, "is_a")
        for ancestor in chain[1:]:
            inherited = self.fact_index.get((ancestor, "has"), [])
            for p in inherited:
                if not any(pp == p for pp, _ in properties):
                    properties.append((p, f"from {ancestor}"))
        if verbose:
            for prop, source in properties:
                print(f"    {subject} has {prop} ({source})")
        return properties

    def syllogism(self, premises, conclusion, verbose=False):
        """Evaluate a syllogism by asserting premises and checking conclusion."""
        if verbose:
            for p in premises:
                print(f"    premise: {p[0]} {p[1]} {p[2]}")
            print(f"    ∴ {conclusion[0]} {conclusion[1]} {conclusion[2]}?")
        subj, rel, obj = conclusion
        if rel == "is_a":
            found, chain = self.is_a_check(subj, obj, verbose=verbose)
            return found, chain
        elif rel == "can":
            found, chain = self.can_check(subj, obj, verbose=verbose)
            return found, chain
        elif rel == "in":
            found, chain = self.containment_check(subj, obj, verbose=verbose)
            return found, chain
        return None, []

    # ── computation ─────────────────────────────────────────────

    def compute(self, a, op, b, memorize=True, verbose=True):
        """The full loop: try → shrug → decompose → verify → memorize."""
        context = [str(a), op, str(b), "="]
        answer, conf = self.lookup(context)
        if answer is not None and conf >= CONFIDENCE_THRESHOLD:
            if verbose:
                print(f"  {a} {op} {b} = {answer}  [direct recall, conf={conf:.1f}]")
            return answer, "recall"

        if verbose:
            print(f"  {a} {op} {b} = ?  [shrug, conf={conf:.2f}] → decomposing...")

        if op == "*":
            result = _decompose_multiply(a, b, self, verbose)
        elif op == "+":
            result = _decompose_add(a, b, self, verbose)
        elif op == "-":
            result = _decompose_add(a, -b, self, verbose)  # placeholder
            if result is None:
                result = a - b
        else:
            result = None

        if result is None:
            if verbose:
                print(f"  FAILED TO DECOMPOSE")
            return None, "failed"

        # Cross-check (commutative verify for multiplication)
        if op == "*":
            rev, rev_conf = self.lookup([str(b), op, str(a), "="])
            if rev is not None and rev_conf >= CONFIDENCE_THRESHOLD:
                if int(rev) == result and verbose:
                    print(f"  cross-check: {b}*{a} = {rev} ✓")
            else:
                rev_result = _decompose_multiply(b, a, self, False)
                if rev_result == result and verbose:
                    print(f"  cross-check: {b}*{a} decomposed = {rev_result} ✓")

        # Memorize
        if memorize and result is not None:
            self.observe(tokenize(f"{a} {op} {b} = {result}"))
            if verbose:
                print(f"  memorized: {a} {op} {b} = {result}")

        return result, "decomposed"

    # ── problem solving ─────────────────────────────────────────

    def solve(self, problem, verbose=True):
        """Solve a problem with unknowns. Forward, backward, gap-fill."""
        tokens = tokenize(problem)
        unknowns = [i for i, t in enumerate(tokens) if t == "?"]

        if not unknowns:
            # Forward: just lookup
            answer, conf = self.lookup(tokens)
            if verbose:
                print(f"  {problem} → {answer} (conf={conf:.1f})")
            return answer

        if len(unknowns) == 1:
            pos = unknowns[0]
            if pos == len(tokens) - 1:
                # Forward: ? is the answer
                context = tokens[:-1]
                answer, conf = self.lookup(context)
                if verbose:
                    print(f"  {problem} → {answer} (conf={conf:.1f})")
                return answer
            else:
                # Backward: try candidates, validate
                target = tokens[-1] if "=" in tokens else None
                eq_pos = tokens.index("=") if "=" in tokens else None
                if eq_pos and eq_pos + 1 < len(tokens):
                    target = tokens[eq_pos + 1]
                candidates = self._get_candidates(tokens, pos)
                for c in candidates:
                    trial = list(tokens)
                    trial[pos] = c
                    context = trial[:-1] if trial[-1] != "=" else trial
                    if target:
                        match, conf = self.check(
                            trial[:eq_pos + 1] if eq_pos else trial[:-1],
                            target)
                        if match:
                            if verbose:
                                print(f"  {problem} → {c} (conf={conf:.1f})")
                            return c
        # Multi-unknown gap-fill
        if len(unknowns) >= 2 and "=" in tokens:
            eq_pos = tokens.index("=")
            target = tokens[eq_pos + 1] if eq_pos + 1 < len(tokens) else None
            if target:
                solutions = []
                candidates = self._get_candidates(tokens, unknowns[0])
                for c1 in candidates:
                    for c2 in candidates:
                        trial = list(tokens)
                        trial[unknowns[0]] = c1
                        trial[unknowns[1]] = c2
                        match, conf = self.check(trial[:eq_pos + 1], target)
                        if match:
                            solutions.append((c1, c2))
                if verbose:
                    print(f"  {problem} → {len(solutions)} solutions")
                    for s in solutions[:5]:
                        print(f"    {s}")
                return solutions
        return None

    def _get_candidates(self, tokens, pos):
        """Generate candidate values for an unknown position."""
        candidates = set()
        for t in tokens:
            if t != "?":
                candidates.update(self.net.get_doors(t, tag="seq"))
                candidates.update(self.net.get_predecessors(t, tag="seq"))
        candidates.discard("?")
        candidates.discard("=")
        for op in ["+", "-", "*", "/", "and", "or", "not"]:
            candidates.discard(op)
        return sorted(candidates)

    def solve_steps(self, steps, verbose=True):
        """Multi-step problem solving with scratch references ($0, $1, ...)."""
        results = []
        for i, step in enumerate(steps):
            # Replace scratch references
            resolved = step
            for j, prev in enumerate(results):
                resolved = resolved.replace(f"${j}", str(prev))
            result = self.solve(resolved, verbose=verbose)
            results.append(result)
            if verbose:
                print(f"  step {i}: {step} → {result}")
        return results

    # ── persistence ─────────────────────────────────────────────

    def assess(self, action_text):
        """Ask the matrix what it learned about this action's consequences.
        The think loop handles fallback automatically — if the full context
        shrugs, it tries progressively simpler contexts."""
        tokens = tokenize(action_text)
        context = tokens + ["result"]
        assessment = {"action": action_text, "checks": {}}

        pos, pos_c = self.check(context, "net_positive")
        neg, neg_c = self.check(context, "net_negative")
        zero, zero_c = self.check(context, "net_zero")

        assessment["checks"]["net_positive"] = (pos, pos_c)
        assessment["checks"]["net_negative"] = (neg, neg_c)
        assessment["checks"]["net_zero"] = (zero, zero_c)

        if neg and neg_c > pos_c and neg_c > zero_c:
            assessment["recommendation"] = "caution"
        elif pos and pos_c > neg_c:
            assessment["recommendation"] = "proceed"
        elif zero and zero_c > neg_c:
            assessment["recommendation"] = "proceed"
        else:
            assessment["recommendation"] = "unknown"

        return assessment

    def plan_think_execute(self, action_text, verbose=True):
        """The universal output loop. Plan, assess persistence, execute or block."""
        if verbose:
            print(f"\n  ┌─ PLAN: {action_text}")
        a = self.assess(action_text)
        if verbose:
            print(f"  ├─ THINK:")
            for name, (val, conf) in a["checks"].items():
                if val:
                    print(f"  │  ✓ {name} (conf={conf:.1f})")
            print(f"  │  → {a['recommendation'].upper()}")
        if a["recommendation"] == "caution":
            if verbose:
                print(f"  └─ ⚠ CAUTION — net negative outcome learned")
            return False, a
        else:
            if verbose:
                print(f"  └─ ✓ PROCEED")
            return True, a

    # ── status ──────────────────────────────────────────────────

    def status(self):
        nodes = self.net.all_nodes()
        tags = set()
        for t in self.net.door_tags.values():
            tags.update(t)
        doors = sum(len(t) for t in self.net.doors.values())
        compiled = bool(self._compiled)
        matrix_shape = self._compiled["W"].shape if compiled else None
        dirty_seqs = len(self.observed_sequences) - self._compiled_up_to
        dirty_consolidation = len(self.observed_sequences) - self._consolidated_up_to
        return {
            "nodes": len(nodes), "doors": doors,
            "tags": sorted(tags), "types": len(self.types),
            "rules": len(self.rules), "lockouts": len(self.lockouts),
            "starts": len(self.starts),
            "observations": len(self.observed_sequences),
            "facts_indexed": sum(len(v) for v in self.fact_index.values()),
            "compiled": compiled, "matrix_shape": matrix_shape,
            "dirty_sequences": dirty_seqs,
            "dirty_nodes": len(self._dirty_nodes),
            "needs_consolidation": dirty_consolidation > 0,
        }


# ═════════════════════════════════════════════════════════════════
# COMPUTATION HELPERS — decompose when shrug
# ═════════════════════════════════════════════════════════════════

def digits_of(n):
    """Extract digits of a number. Tokenization-level (Rule 2 exception)."""
    n = abs(int(n))
    if n == 0:
        return [0]
    ds = []
    while n > 0:
        ds.append(n % 10)
        n //= 10
    ds.reverse()
    return ds


def _decompose_multiply(a, b, isaac, verbose=True):
    """Decompose a * b into digit-pair lookups from memorized tables."""
    da = digits_of(a)
    db = digits_of(b)
    total = 0
    for i, digit_a in enumerate(da):
        place_a = len(da) - 1 - i
        for j, digit_b in enumerate(db):
            place_b = len(db) - 1 - j
            place_value = 10 ** (place_a + place_b)
            product_str, conf = isaac.lookup(
                [str(digit_a), "*", str(digit_b), "="])
            if product_str is None or conf < CONFIDENCE_THRESHOLD:
                return None
            product = int(product_str)
            contribution = product * place_value
            total += contribution
            if verbose:
                print(f"    {digit_a}×{digit_b}={product:>4d}"
                      f" × {place_value:>6d} = {contribution:>8d}")
    if verbose:
        print(f"    {'─' * 40}")
        print(f"    TOTAL = {total}")
    return total


def _decompose_add(a, b, isaac, verbose=True):
    """Decompose a + b into digit-pair additions with carry."""
    da = digits_of(a)
    db = digits_of(b)
    max_len = max(len(da), len(db))
    da = [0] * (max_len - len(da)) + da
    db = [0] * (max_len - len(db)) + db
    result_digits = []
    carry = 0
    for i in range(max_len - 1, -1, -1):
        digit_sum = da[i] + db[i] + carry
        sum_str, conf = isaac.lookup([str(da[i]), "+", str(db[i]), "="])
        if sum_str is not None and conf >= CONFIDENCE_THRESHOLD:
            partial = int(sum_str)
            if carry > 0:
                carry_str, cc = isaac.lookup([str(partial), "+", str(carry), "="])
                if carry_str is not None and cc >= CONFIDENCE_THRESHOLD:
                    digit_sum = int(carry_str)
                else:
                    digit_sum = da[i] + db[i] + carry
            else:
                digit_sum = partial
        carry = digit_sum // 10
        result_digits.append(digit_sum % 10)
    if carry > 0:
        result_digits.append(carry)
    result_digits.reverse()
    result = int("".join(str(d) for d in result_digits))
    if verbose:
        print(f"    {a} + {b} = {result}")
    return result


# ═════════════════════════════════════════════════════════════════
# WORLD — state management and planning
# ═════════════════════════════════════════════════════════════════

class World:
    """Manages mutable world state. Actions have preconditions and effects.
    Uses Isaac for persistence assessment."""

    def __init__(self, isaac=None):
        self.state = defaultdict(set)   # entity → {facts}
        self.actions = {}               # (source_pattern, action, target_pattern) → {...}
        self.isaac = isaac

    def set_state(self, entity, fact):
        self.state[entity].add(fact)

    def clear_state(self, entity, fact):
        self.state[entity].discard(fact)

    def has_state(self, entity, fact):
        return fact in self.state.get(entity, set())

    def show_state(self):
        for entity in sorted(self.state):
            facts = sorted(self.state[entity])
            if facts:
                print(f"  {entity}: {', '.join(facts)}")

    def teach_action(self, source, action, target,
                     preconditions=None, effects=None):
        self.actions[(source, action, target)] = {
            "preconditions": preconditions or [],
            "effects": effects or [],
        }

    def execute(self, source, action, target, verbose=True):
        """Execute an action. Check preconditions. Apply effects."""
        key = (source, action, target)
        wildcard = ("*", action, "*")
        specific_src = (source, action, "*")
        specific_tgt = ("*", action, target)

        spec = None
        for k in [key, specific_src, specific_tgt, wildcard]:
            if k in self.actions:
                spec = self.actions[k]
                break
        if spec is None:
            if verbose:
                print(f"  Unknown action: {source} {action} {target}")
            return False, ["unknown action"]

        # Check preconditions
        failed = []
        for cond in spec["preconditions"]:
            resolved = cond.replace("SOURCE", source).replace("TARGET", target)
            parts = resolved.split()
            if len(parts) >= 3 and parts[1] == "near":
                # Proximity check
                loc_src = self._get_location(parts[0])
                loc_tgt = self._get_location(parts[2])
                if loc_src != loc_tgt:
                    failed.append(resolved)
            elif len(parts) >= 3 and parts[1] == "is":
                if not self.has_state(parts[0], " ".join(parts[1:])):
                    failed.append(resolved)
            elif len(parts) >= 2 and parts[1] == "has":
                if not self.has_state(parts[0], " ".join(parts[1:])):
                    failed.append(resolved)

        if failed:
            if verbose:
                print(f"  Preconditions failed: {failed}")
            return False, failed

        # Apply effects
        for effect in spec["effects"]:
            resolved = effect.replace("SOURCE", source).replace("TARGET", target)
            parts = resolved.split()
            if len(parts) >= 3 and parts[1] == "is":
                self.set_state(parts[0], " ".join(parts[1:]))
            elif len(parts) >= 2 and parts[0].startswith("not_"):
                entity = parts[0].replace("not_", "")
                # Remove the matching positive state
                # This is a simplification — should match more carefully
                pass
            elif len(parts) >= 2 and parts[1] == "has":
                self.set_state(parts[0], " ".join(parts[1:]))
            if verbose:
                print(f"  effect: {resolved}")
        return True, []

    def _get_location(self, entity):
        for fact in self.state.get(entity, set()):
            if fact.startswith("in_") or fact.startswith("at_"):
                return fact
        return None


# ═════════════════════════════════════════════════════════════════
# TEST SUITE
# ═════════════════════════════════════════════════════════════════

def _div(title):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


def test_language():
    """Language: observe, crystallize, generate, type inference."""
    _div("LANGUAGE")
    isaac = Isaac()
    sentences = [
        "the cat sat .", "the dog ran .", "the cat ran .",
        "the big cat sat .", "the small dog ran .",
        "a cat is soft .", "a dog is loyal .",
        "the bird flew .", "a fish swam .",
        "the big dog barked .", "the small cat purred .",
        "she ran fast .", "he walked slowly .",
        "a red ball bounced .", "the blue car stopped .",
    ]
    bad = ["cat the sat .", "dog the ran .", "the sat cat .", "the ran dog ."]
    for s in sentences:
        isaac.observe(tokenize(s))
    for s in bad:
        isaac.observe_negative(tokenize(s))
    isaac.crystallize(verbose=True)

    print(f"\n  Generation:")
    for concept in ["cat", "dog", "ball"]:
        chain = isaac.generate(concept)
        print(f"    '{concept}' → {' '.join(chain)}")

    # Type inference
    result = isaac.infer("dog", "sat")
    print(f"\n  dog→sat inferred: {result['inferred']} via {result.get('via')}")
    return True


def test_math():
    """Math: memorize tables, recall via matrix, shrug boundary."""
    _div("MATH — matrix recall")
    isaac = Isaac()
    for a in range(20):
        for b in range(20):
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
            isaac.observe(tokenize(f"{a} * {b} = {a * b}"))
    # No manual compile() — lookup auto-compiles (Stage 3: ROUTE)

    tests = [
        (["7", "*", "8", "="], "56"),
        (["3", "+", "5", "="], "8"),
        (["12", "*", "12", "="], "144"),
        (["19", "+", "19", "="], "38"),
        (["0", "*", "15", "="], "0"),
        (["1", "*", "7", "="], "7"),
    ]
    correct = 0
    for context, expected in tests:
        answer, conf = isaac.lookup(context)
        ok = answer == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {' '.join(context)} → {answer}"
              f"  (expected {expected}, conf={conf:.1f})")
    print(f"\n  {correct}/{len(tests)}")
    return correct == len(tests)


def test_logic():
    """Logic: truth tables via matmul, compound decomposition."""
    _div("LOGIC")
    isaac = Isaac()
    for a in ["true", "false"]:
        for b in ["true", "false"]:
            av, bv = a == "true", b == "true"
            isaac.observe(tokenize(f"{a} and {b} = {'true' if av and bv else 'false'}"))
            isaac.observe(tokenize(f"{a} or {b} = {'true' if av or bv else 'false'}"))
            isaac.observe(tokenize(f"{a} xor {b} = {'true' if av ^ bv else 'false'}"))
            isaac.observe(tokenize(f"{a} implies {b} = {'true' if (not av) or bv else 'false'}"))
        isaac.observe(tokenize(f"not {a} = {'false' if a == 'true' else 'true'}"))
    # Auto-compiles on first query

    tests = [
        ("true and true", "true"), ("true and false", "false"),
        ("false or true", "true"), ("false or false", "false"),
        ("not true", "false"), ("not false", "true"),
        ("true xor false", "true"),
    ]
    correct = 0
    for expr, expected in tests:
        result, _ = isaac.logic_eval(expr)
        ok = result == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {expr:30s} → {result}")
    print(f"\n  {correct}/{len(tests)}")

    # Compound
    compound = [
        ("true and false or true", "true"),
        ("not true or false", "false"),
        ("not false and true", "true"),
    ]
    cc = 0
    for expr, expected in compound:
        result, _ = isaac.logic_eval(expr)
        ok = result == expected
        cc += ok
        print(f"  {'✓' if ok else '✗'}  {expr:30s} → {result}")
    print(f"  compound: {cc}/{len(compound)}")
    return correct == len(tests) and cc == len(compound)


def test_reasoning():
    """Reasoning: is_a chains, capability inheritance, containment."""
    _div("REASONING")
    isaac = Isaac()
    # Taxonomy
    for subj, obj in [("cat", "mammal"), ("dog", "mammal"),
                      ("mammal", "animal"), ("animal", "living_thing"),
                      ("robin", "bird"), ("penguin", "bird"),
                      ("bird", "animal"), ("salmon", "fish"),
                      ("fish", "animal"), ("oak", "tree"),
                      ("tree", "plant"), ("plant", "living_thing")]:
        isaac.teach(subj, "is_a", obj)
    # Capabilities
    for subj, obj in [("bird", "fly"), ("bird", "sing"),
                      ("fish", "swim"), ("cat", "purr"), ("cat", "climb"),
                      ("dog", "bark"), ("penguin", "swim"),
                      ("living_thing", "grow"), ("animal", "move")]:
        isaac.teach(subj, "can", obj)
    # Negatives
    for subj, obj in [("penguin", "fly"), ("fish", "walk")]:
        isaac.observe(tokenize(f"{subj} cannot {obj}"))
        isaac.fact_index[(subj, "cannot")].append(obj)
    # Containment
    for inner, outer in [("ball", "box"), ("box", "closet"),
                         ("closet", "room"), ("room", "house")]:
        isaac.teach(inner, "in", outer)
    # Auto-compiles on first query

    # Is-a
    correct = 0
    for subj, tgt, expected in [("cat", "animal", True),
                                 ("cat", "living_thing", True),
                                 ("robin", "animal", True),
                                 ("cat", "plant", False)]:
        found, chain = isaac.is_a_check(subj, tgt)
        ok = found == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {subj} is_a {tgt}? {found}"
              f"  chain: {' → '.join(chain)}")

    # Can
    for subj, ability, expected in [("robin", "fly", True),
                                     ("robin", "sing", True),
                                     ("cat", "climb", True),
                                     ("cat", "grow", True),
                                     ("penguin", "fly", False),
                                     ("penguin", "swim", True)]:
        result, chain = isaac.can_check(subj, ability, verbose=True)
        if result is None:
            result = False
        ok = result == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  can {subj} {ability}? {result}")

    # Containment
    found, chain = isaac.containment_check("ball", "house")
    ok = found == True
    correct += ok
    print(f"  {'✓' if ok else '✗'}  ball in house? {found}  chain: {' → '.join(chain)}")

    print(f"\n  {correct}/11")
    return correct == 11


def test_decompose():
    """Decompose: shrug → digit-pair lookups → assemble → verify."""
    _div("DECOMPOSE WHEN SHRUG")
    isaac = Isaac()
    for a in range(100):
        for b in range(100):
            isaac.observe(tokenize(f"{a} * {b} = {a * b}"))
            isaac.observe(tokenize(f"{a} + {b} = {a + b}"))
    for a in range(100):
        isaac.observe(tokenize(f"{a} * 100 = {a * 100}"))
        isaac.observe(tokenize(f"{a} * 1000 = {a * 1000}"))
    # Auto-compiles on first compute() call

    tests = [(137, "*", 48, 6576), (256, "*", 31, 7936), (999, "*", 999, 998001)]
    correct = 0
    for a, op, b, expected in tests:
        result, method = isaac.compute(a, op, b, memorize=False)
        ok = (result == expected)
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {a} {op} {b} = {result}"
              f"  (expected {expected}) [{method}]")
    print(f"\n  {correct}/{len(tests)}")
    return correct == len(tests)


def test_persistence():
    """Persistence: learn from consequences, assess novel actions."""
    _div("PERSISTENCE — learn from consequences")
    isaac = Isaac()

    scenarios = [
        ("me build birdhouse", 3, 6),
        ("me assemble watch", 6, 8),
        ("me smash watch", 8, 3),
        ("me knock tower", 7, 5),
        ("me burn painting", 6, 2),
        ("me snap stick", 1, 1),
        ("me crack rock", 1, 1),
        ("me oil watch", 7, 8),
        ("me repair roof", 5, 5),
    ]
    for action, before, after in scenarios:
        delta = after - before
        if delta > 0:
            isaac.observe(tokenize(f"{action} result net_positive"))
        elif delta < 0:
            isaac.observe(tokenize(f"{action} result net_negative"))
        else:
            isaac.observe(tokenize(f"{action} result net_zero"))
        # Verb-level observation for generalization
        verb = tokenize(action)[1]  # "me VERB object" → VERB at index 1
        if delta > 0:
            isaac.observe(tokenize(f"{verb} result net_positive"))
        elif delta < 0:
            isaac.observe(tokenize(f"{verb} result net_negative"))
        else:
            isaac.observe(tokenize(f"{verb} result net_zero"))

    # Auto-compiles on first assess() call

    # Known actions
    correct = 0
    for action, expected in [("me build birdhouse", "proceed"),
                              ("me smash watch", "caution"),
                              ("me snap stick", "proceed"),
                              ("me oil watch", "proceed")]:
        a = isaac.assess(action)
        ok = a["recommendation"] == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {action:25s} → {a['recommendation']}")

    # Novel actions (verb-level generalization)
    for action, expected in [("me smash computer", "caution"),
                              ("me build castle", "proceed"),
                              ("me snap pencil", "proceed")]:
        a = isaac.assess(action)
        ok = a["recommendation"] == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'}  {action:25s} → {a['recommendation']}"
              f"  [think loop fallback]")

    print(f"\n  {correct}/7")
    return correct == 7


# ═════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Isaac — Unified Engine")
    print("One operation. All the way up.\n")

    results = {}
    results["language"] = test_language()
    results["math"] = test_math()
    results["logic"] = test_logic()
    results["reasoning"] = test_reasoning()
    results["decompose"] = test_decompose()
    results["persistence"] = test_persistence()

    _div("SUMMARY")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'}  {name}")
    total = sum(1 for v in results.values() if v)
    print(f"\n  {total}/{len(results)} capability areas passed")

    # Final status
    isaac = Isaac()
    for expr in ["the cat sat .", "3 + 5 = 8", "true and false = false",
                 "cat is_a mammal"]:
        isaac.observe(tokenize(expr))
    isaac.consolidate()
    st = isaac.status()
    print(f"\n  Quick status: {st['nodes']} nodes, {st['doors']} doors, "
          f"compiled={st['compiled']}, dirty_seqs={st['dirty_sequences']}")
    print(f"\n  One file. One class. One operation.")
