#!/usr/bin/env python3
"""
Intellon v4 — Desktop GUI
Run: python -m intellon.gui
"""
import sys, os, threading, time, queue
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import readline
except ImportError:
    pass

from intellon.core.engine import Engine
from intellon.core.models import Tier, NodeFlag
from intellon.core.training import load_wordnet, load_file, process_text, CORE_VOCABULARY
from intellon.core.thinker import Thinker
from intellon.core.curriculum import run_curriculum
from intellon.core.datasources import load_wordnet_full, load_brown_corpus, load_conceptnet, BROWN_CATEGORIES
from intellon.core import storage

BG="#1e1e2e"; FG="#cdd6f4"; BG2="#313244"; BG3="#45475a"
ACCENT="#89b4fa"; GREEN="#a6e3a1"; YELLOW="#f9e2af"; RED="#f38ba8"; DIM="#6c7086"; MAUVE="#cba6f7"

if sys.platform == "win32":
    os.system("")


class IntellonGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Intellon v4")
        self.root.geometry("1200x800")
        self.root.configure(bg=BG)
        self.root.minsize(900, 600)
        self.engine = None
        self.thinker = None
        self.debug_mode = tk.BooleanVar(value=False)
        self.training_mode = tk.BooleanVar(value=False)
        self.thinking_active = tk.BooleanVar(value=True)

        # Work queue — one job at a time, in order
        self._work_queue = queue.Queue()
        self._busy = False

        self._build_ui()
        self._boot()

    # ==================================================================
    # Work Queue — the single worker thread
    # ==================================================================

    def _start_worker(self):
        """Single worker thread. Pulls jobs from queue, runs them in order.
           Thinking runs ONLY when the queue is empty and no job is active."""
        def worker():
            while True:
                # Try to get work
                try:
                    job = self._work_queue.get(timeout=0.05)
                except queue.Empty:
                    # No work — think if enabled
                    if self.thinker and self.thinking_active.get() and not self._busy:
                        try:
                            thought = self.thinker.tick()
                            if thought and thought.discovery:
                                time.sleep(self.thinker._min_delay)
                            else:
                                time.sleep(self.thinker._idle_delay)
                        except:
                            time.sleep(0.1)
                    else:
                        time.sleep(0.1)
                    continue

                # Got work — pause thinking, run job
                self._busy = True
                if self.thinker:
                    self.thinker.pause()
                try:
                    job()
                except Exception as e:
                    self._w(self.output, f"  Error: {e}\n\n", "error")
                finally:
                    self._busy = False
                    self._work_queue.task_done()
                    # Resume thinking if queue is now empty
                    if self._work_queue.empty() and self.thinking_active.get() and self.thinker:
                        self.thinker.start()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _enqueue(self, fn):
        """Put a job on the queue. It will run after anything already queued."""
        self._work_queue.put(fn)

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self):
        style = ttk.Style(); style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=("Consolas", 10))
        style.configure("Header.TLabel", background=BG, foreground=ACCENT, font=("Consolas", 13, "bold"))
        style.configure("Status.TLabel", background=BG2, foreground=DIM, font=("Consolas", 9))
        style.configure("TButton", background=BG3, foreground=FG, font=("Consolas", 9), padding=4)
        style.map("TButton", background=[("active", ACCENT)], foreground=[("active", BG)])
        style.configure("Accent.TButton", background=ACCENT, foreground=BG, font=("Consolas", 9, "bold"))
        style.map("Accent.TButton", background=[("active", GREEN)])
        style.configure("TCheckbutton", background=BG, foreground=FG, font=("Consolas", 9))

        main = ttk.Frame(self.root, padding=6); main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main); header.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(header, text="Intellon v4", style="Header.TLabel").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Booting...")
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.RIGHT, padx=8)
        self.think_status_var = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.think_status_var, foreground=MAUVE, background=BG, font=("Consolas", 9)).pack(side=tk.RIGHT, padx=8)

        btnbar = ttk.Frame(main); btnbar.pack(fill=tk.X, pady=(0, 4))
        for txt, cmd in [("\U0001f9ea Curriculum", self._on_curriculum), ("\U0001f4da WordNet", self._on_wordnet),
                         ("\U0001f4d6 Full WordNet", self._on_wordnet_full), ("\U0001f4d5 Brown Corpus", self._on_brown),
                         ("\U0001f310 ConceptNet", self._on_conceptnet), ("\U0001f4c4 Train File", self._on_train_file),
                         ("\U0001f4be Save", self._on_save), ("\U0001f4c2 Load", self._on_load),
                         ("\U0001f4ca Stats", self._on_stats)]:
            ttk.Button(btnbar, text=txt, command=cmd).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btnbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=6, fill=tk.Y, pady=2)
        ttk.Checkbutton(btnbar, text="Debug", variable=self.debug_mode).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(btnbar, text="Training", variable=self.training_mode, command=self._on_training_toggle).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(btnbar, text="\U0001f9e0 Thinking", variable=self.thinking_active, command=self._on_thinking_toggle).pack(side=tk.LEFT, padx=2)

        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL); paned.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        left = ttk.Frame(paned); paned.add(left, weight=3)
        ttk.Label(left, text="Input / Output", foreground=DIM, background=BG, font=("Consolas", 9)).pack(anchor=tk.W)
        self.output = scrolledtext.ScrolledText(left, wrap=tk.WORD, font=("Consolas", 10), bg=BG2, fg=FG, insertbackground=FG, selectbackground=ACCENT, selectforeground=BG, relief=tk.FLAT, padx=10, pady=8, state=tk.DISABLED)
        self.output.pack(fill=tk.BOTH, expand=True)
        for t, c in [("header", ACCENT), ("pattern", GREEN), ("new", YELLOW), ("dim", DIM), ("error", RED), ("input_echo", ACCENT)]:
            self.output.tag_configure(t, foreground=c, font=("Consolas", 10, "bold") if t in ("header", "pattern") else ("Consolas", 10))

        center = ttk.Frame(paned); paned.add(center, weight=2)
        ttk.Label(center, text="Autonomous Thinking", foreground=MAUVE, background=BG, font=("Consolas", 9)).pack(anchor=tk.W)
        self.think_log = scrolledtext.ScrolledText(center, wrap=tk.WORD, font=("Consolas", 9), bg=BG2, fg=FG, insertbackground=FG, relief=tk.FLAT, padx=8, pady=6, state=tk.DISABLED)
        self.think_log.pack(fill=tk.BOTH, expand=True)
        for t, c in [("discovery", GREEN), ("thought", DIM), ("type", MAUVE), ("dim", DIM)]:
            self.think_log.tag_configure(t, foreground=c)

        right = ttk.Frame(paned); paned.add(right, weight=2)
        sf = ttk.Frame(right); sf.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(sf, text="\U0001f50d", background=BG).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        se = ttk.Entry(sf, textvariable=self.search_var, font=("Consolas", 10))
        se.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        se.bind("<Return>", lambda e: self._on_search())
        ttk.Button(sf, text="Inspect", command=self._on_search).pack(side=tk.LEFT)
        self.inspector = scrolledtext.ScrolledText(right, wrap=tk.WORD, font=("Consolas", 9), bg=BG2, fg=FG, insertbackground=FG, relief=tk.FLAT, padx=8, pady=6, state=tk.DISABLED)
        self.inspector.pack(fill=tk.BOTH, expand=True)
        for t, c in [("label", ACCENT), ("dim", DIM), ("green", GREEN)]:
            self.inspector.tag_configure(t, foreground=c, font=("Consolas", 9, "bold") if t == "label" else ("Consolas", 9))

        inf = ttk.Frame(main); inf.pack(fill=tk.X)
        self.input_entry = tk.Entry(inf, font=("Consolas", 12), bg=BG3, fg=FG, insertbackground=FG, relief=tk.FLAT, bd=8)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.focus_set()
        ttk.Button(inf, text="Send", style="Accent.TButton", command=self._on_enter).pack(side=tk.RIGHT)

    # ==================================================================
    # Helpers
    # ==================================================================

    def _w(self, widget, text, tag=None):
        def do():
            widget.configure(state=tk.NORMAL)
            if tag:
                widget.insert(tk.END, text, tag)
            else:
                widget.insert(tk.END, text)
            widget.see(tk.END)
            widget.configure(state=tk.DISABLED)
        if threading.current_thread() is threading.main_thread():
            do()
        else:
            self.root.after(0, do)

    def _clr(self, widget):
        def do():
            widget.configure(state=tk.NORMAL); widget.delete("1.0", tk.END); widget.configure(state=tk.DISABLED)
        if threading.current_thread() is threading.main_thread():
            do()
        else:
            self.root.after(0, do)

    def _update_status(self):
        if not self.engine: return
        lib = self.engine.librarian
        def do():
            self.status_var.set(f"{lib.node_count} nodes | {lib.foundation_count} fdn | {lib.session_count} sessions")
        self.root.after(0, do)

    # ==================================================================
    # Boot
    # ==================================================================

    def _boot(self):
        def do():
            self.engine = Engine(run_boot=True)
            self.thinker = Thinker(self.engine)
            self.thinker.set_callback(self._on_thought)
            self.thinker.start()
            self._update_status()
            self._w(self.output, f"Intellon v4 booted \u2014 {self.engine.librarian.node_count} nodes, {self.engine.librarian.foundation_count} foundation\n", "header")
            self._w(self.output, "\U0001f9ea Curriculum \u2192 \U0001f4da WordNet \u2192 \U0001f4d5 Brown Corpus \u2192 \U0001f310 ConceptNet \u2192 your data\n\n", "dim")
            # Start the single worker thread
            self._start_worker()
        threading.Thread(target=do, daemon=True).start()

    def _on_thought(self, thought):
        ts = self.thinker.stats
        def do():
            self.think_status_var.set(f"\U0001f4ad {ts['thoughts']} thoughts, {ts['discoveries']} discoveries")
        self.root.after(0, do)
        self._w(self.think_log, f"[{thought.thought_type.value}] ", "type")
        self._w(self.think_log, f"{thought.description}\n", "thought")
        if thought.discovery:
            self._w(self.think_log, f"  \U0001f4a1 {thought.discovery}\n", "discovery")
        self._w(self.think_log, f"  ({thought.records_produced} records)\n\n", "dim")
        self._update_status()

    def _on_thinking_toggle(self):
        if not self.thinker: return
        if self.thinking_active.get():
            if not self._busy:
                self.thinker.start()
            self._w(self.think_log, "\u2014 Thinking enabled \u2014\n\n", "type")
        else:
            self.thinker.pause()
            self._w(self.think_log, "\u2014 Thinking disabled \u2014\n\n", "dim")

    # ==================================================================
    # Input — queued like everything else
    # ==================================================================

    def _on_enter(self, event=None):
        text = self.input_entry.get().strip()
        if not text: return
        self.input_entry.delete(0, tk.END)
        if not self.engine:
            self._w(self.output, "Still booting...\n", "error"); return
        self._w(self.output, f"> {text}\n", "input_echo")

        def job():
            lib = self.engine.librarian
            if self.debug_mode.get():
                a = lib.bundle(text)
                rn = [lib.get_node(x).name for x in a.metadata["recognized"] if lib.get_node(x)]
                self._w(self.output, f"  recognized: {', '.join(rn) if rn else '(none)'}\n", "dim")
                self._w(self.output, f"  context: {len(a.context)}, foundation: {len(a.foundation)} (k={lib._top_k}, depth={lib._walk_depth})\n", "dim")
            result = self.engine.process(text)
            if result.synthesis and isinstance(result.synthesis.content, dict):
                p = result.synthesis.content.get("pattern")
                if p and p.get("pattern_str"):
                    self._w(self.output, f"  pattern: {p['pattern_str']}\n", "pattern")
                    for pos, fillers in p.get("slots", {}).items():
                        self._w(self.output, f"    slot [{pos}]: {', '.join(fillers)}\n", "dim")
            if result.stubs:
                nw = list(dict.fromkeys(s.name for s in result.stubs if s.name))
                if nw: self._w(self.output, f"  new: {', '.join(nw)}\n", "new")
            self._w(self.output, f"  [{len(result.notepad)} records, {lib.node_count} nodes]\n\n", "dim")
            self._update_status()

        self._enqueue(job)

    # ==================================================================
    # Button handlers — all enqueue work
    # ==================================================================

    def _on_curriculum(self):
        if not self.engine: return
        def job():
            self._w(self.output, "Running curriculum: Logic \u2192 Arithmetic \u2192 Comparison...\n", "header")
            def progress(name, i, total):
                if i == 1 or i == total or i % 20 == 0:
                    self._w(self.output, f"  {name}: {i}/{total}\n", "dim")
            stats = run_curriculum(self.engine, through_phase=3, on_progress=progress)
            self._w(self.output, f"  \u2713 {stats['total_observations']} observations, {stats['nodes_created']} new nodes\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_wordnet(self):
        if not self.engine: return
        def job():
            pre = self.engine.librarian.node_count
            self._w(self.output, "Loading core WordNet vocabulary (174 words)...\n", "header")
            reg = load_wordnet(self.engine.librarian, tier=Tier.IMPORTANT, engine=self.engine)
            self._w(self.output, f"  \u2713 {len(reg)} words, {self.engine.librarian.node_count - pre} new nodes\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_wordnet_full(self):
        if not self.engine: return
        def job():
            self._w(self.output, "Loading FULL WordNet (~84K words)...\n", "header")
            def progress(phase, cur, total):
                if cur % 10000 == 0 or cur == total:
                    self._w(self.output, f"  {phase}: {cur:,}/{total:,}\n", "dim")
            stats = load_wordnet_full(self.engine.librarian, tier=Tier.IMPORTANT, engine=self.engine, on_progress=progress)
            self._w(self.output, f"  \u2713 {stats['words_imported']:,} words, {stats['nodes_created']:,} new nodes\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_brown(self):
        if not self.engine: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Brown Corpus")
        dialog.geometry("350x200")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="Brown Corpus \u2014 57K English sentences", style="Header.TLabel").pack(pady=(10, 5))
        ttk.Label(dialog, text="How many sentences?").pack()
        choice = tk.StringVar(value="1000")
        for label, val in [("1,000 (quick test)", "1000"), ("5,000 (good sample)", "5000"),
                           ("10,000 (substantial)", "10000"), ("All 57,000 (full)", "0")]:
            ttk.Radiobutton(dialog, text=label, variable=choice, value=val).pack(anchor=tk.W, padx=40)
        def go():
            n = int(choice.get())
            dialog.destroy()
            def job():
                limit = n if n > 0 else None
                self._w(self.output, f"Loading Brown Corpus ({n if n > 0 else 'all'} sentences)...\n", "header")
                def progress(cat, cur, total):
                    self._w(self.output, f"  {cat}: {cur:,}/{total:,}\n", "dim")
                stats = load_brown_corpus(self.engine, max_sentences=limit, tier=Tier.VALIDATED, on_progress=progress)
                self._w(self.output, f"  \u2713 {stats['sentences_processed']:,} sentences, {stats['nodes_created']:,} new nodes, {stats['notepad_records']:,} records\n\n", "pattern")
                self._update_status()
            self._enqueue(job)
        ttk.Button(dialog, text="Load", style="Accent.TButton", command=go).pack(pady=10)

    def _on_conceptnet(self):
        if not self.engine: return
        fp = filedialog.askopenfilename(title="Select ConceptNet assertions CSV",
            filetypes=[("CSV/TSV", "*.csv *.tsv"), ("Gzipped", "*.gz"), ("All", "*.*")])
        if not fp: return
        def job():
            self._w(self.output, f"Loading ConceptNet from {os.path.basename(fp)}...\n", "header")
            self._w(self.output, "  (Download from: github.com/commonsense/conceptnet5/wiki/Downloads)\n", "dim")
            def progress(cur, total):
                if cur % 100000 == 0:
                    self._w(self.output, f"  {cur:,}/{total:,} assertions\n", "dim")
            stats = load_conceptnet(self.engine.librarian, fp, min_weight=1.0, tier=Tier.VALIDATED, on_progress=progress)
            self._w(self.output, f"  \u2713 {stats['assertions_loaded']:,} assertions, {stats['nodes_created']:,} new nodes, {stats['relations_created']:,} relations\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_train_file(self):
        if not self.engine: return
        fp = filedialog.askopenfilename(title="Select training file",
            filetypes=[("All supported", "*.txt *.csv *.json *.pdf *.md"), ("Text", "*.txt *.md"),
                       ("CSV", "*.csv"), ("JSON", "*.json"), ("PDF", "*.pdf"), ("All", "*.*")])
        if not fp: return
        def job():
            ext = os.path.splitext(fp)[1]
            self._w(self.output, f"Training: {os.path.basename(fp)} ({ext})...\n", "header")
            stats = load_file(self.engine, fp, tier=Tier.VALIDATED)
            if "error" in stats:
                self._w(self.output, f"  Error: {stats['error']}\n\n", "error"); return
            parts = []
            for k, l in [("pages", "pages"), ("sentences_processed", "sentences"),
                         ("rows_processed", "rows"), ("items_processed", "items")]:
                if k in stats: parts.append(f"{stats[k]} {l}")
            parts.append(f"{stats.get('nodes_created', stats.get('nodes_after', 0) - stats.get('nodes_before', 0))} new nodes")
            self._w(self.output, f"  \u2713 {', '.join(parts)}\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_save(self):
        if not self.engine: return
        fp = filedialog.asksaveasfilename(title="Save", defaultextension=".db",
            filetypes=[("SQLite", "*.db"), ("All", "*.*")], initialfile="intellon.db")
        if not fp: return
        def job():
            storage.save(self.engine.librarian, fp)
            self._w(self.output, f"Saved {self.engine.librarian.node_count} nodes \u2192 {os.path.basename(fp)}\n\n", "pattern")
        self._enqueue(job)

    def _on_load(self):
        fp = filedialog.askopenfilename(title="Load", filetypes=[("SQLite", "*.db"), ("All", "*.*")])
        if not fp: return
        def job():
            self.engine = Engine(run_boot=False)
            storage.load(self.engine.librarian, fp)
            self.thinker = Thinker(self.engine)
            self.thinker.set_callback(self._on_thought)
            self.thinker.start()
            self._w(self.output, f"Loaded {self.engine.librarian.node_count} nodes \u2190 {os.path.basename(fp)}\n\n", "pattern")
            self._update_status()
        self._enqueue(job)

    def _on_stats(self):
        if not self.engine: return
        self._clr(self.inspector)
        self._w(self.inspector, "Calculating...\n", "dim")
        def job():
            lib = self.engine.librarian; nodes = lib.get_all_nodes()
            tc = {}; td = tp = 0
            for n in nodes:
                tc[n.tier.name] = tc.get(n.tier.name, 0) + 1; td += len(n.definitions); tp += len(n.pointers)
            self._clr(self.inspector)
            self._w(self.inspector, "NETWORK\n\n", "label")
            for l, v in [("Nodes", lib.node_count), ("Foundation", lib.foundation_count),
                         ("Sessions", lib.session_count), ("Definitions", td), ("Pointers", tp)]:
                self._w(self.inspector, f"  {l+':':<14} {v}\n")
            self._w(self.inspector, "\nTIERS\n", "label")
            for t in ["INITIATOR", "IMPORTANT", "VALIDATED", "TRIAL"]:
                c = tc.get(t, 0); self._w(self.inspector, f"  {t:<12} {c:>5}  {chr(9608) * min(c // 2, 25)}\n")
            if self.thinker:
                ts = self.thinker.stats
                self._w(self.inspector, "\nTHINKING\n", "label")
                self._w(self.inspector, f"  Thoughts:     {ts['thoughts']}\n  Discoveries:  {ts['discoveries']}\n  Active:       {'yes' if ts['running'] and not ts['paused'] else 'no'}\n")
            self._w(self.inspector, "\nBUNDLING\n", "label")
            self._w(self.inspector, f"  Top-K:        {lib._top_k}\n  Walk depth:   {lib._walk_depth}\n")
            if lib._time_history:
                avg = sum(lib._time_history) / len(lib._time_history)
                self._w(self.inspector, f"  Avg time:     {avg*1000:.0f}ms\n")
            self._w(self.inspector, "\nTOP NODES\n", "label")
            for n in sorted(nodes, key=lambda n: n.tallies.get("sessions_involved", 0), reverse=True)[:12]:
                si = n.tallies.get("sessions_involved", 0)
                if si > 0: self._w(self.inspector, f"  {n.name:<14} {si:>3} sessions  {n.tier.name}\n")
        self._enqueue(job)

    def _on_search(self):
        term = self.search_var.get().strip()
        if not term or not self.engine: return
        self._clr(self.inspector)
        self._w(self.inspector, f"Searching \"{term}\"...\n", "dim")
        def job():
            lib = self.engine.librarian
            ids = lib.recognize(term.lower())
            if not ids:
                ms = [n for n in lib.get_all_nodes() if term.lower() in n.name.lower()]
                if not ms:
                    self._clr(self.inspector)
                    self._w(self.inspector, f'Not found: "{term}"\n'); return
                ids = [m.id for m in ms[:5]]
            self._clr(self.inspector)
            for nid in ids[:3]:
                node = lib.get_node(nid)
                if not node: continue
                self._w(self.inspector, f"{node.name}", "label")
                self._w(self.inspector, f"  [{node.id[:12]}...]\n", "dim")
                self._w(self.inspector, f"Tier: {node.tier.name}  Flags: {', '.join(f.value for f in node.flags)}\n\n")
                if node.definitions:
                    self._w(self.inspector, "Definitions:\n", "label")
                    for d in node.definitions[:6]:
                        self._w(self.inspector, f"  {d.number}. {str(d.content)[:65]}\n")
                    if len(node.definitions) > 6: self._w(self.inspector, f"  ... +{len(node.definitions) - 6} more\n", "dim")
                if node.char_pointers:
                    chars = [lib.get_node(cp).name if lib.get_node(cp) else "?" for cp in node.char_pointers]
                    self._w(self.inspector, f"\nChars: {' \u2192 '.join(chars)}\n", "green")
                if node.pointers:
                    self._w(self.inspector, f"\nPointers ({len(node.pointers)}):\n", "label")
                    for p in node.pointers[:10]:
                        t = lib.get_node(p.target); self._w(self.inspector, f"  {p.relation} \u2192 {t.name if t else p.target[:20]}\n")
                    if len(node.pointers) > 10: self._w(self.inspector, f"  ... +{len(node.pointers) - 10} more\n", "dim")
                if node.tallies:
                    top = sorted(node.tallies.items(), key=lambda x: -x[1])[:5]
                    self._w(self.inspector, "\nTallies: ", "label")
                    self._w(self.inspector, ", ".join(f"{k}={v}" for k, v in top) + "\n")
                self._w(self.inspector, "\n")
        self._enqueue(job)

    def _on_training_toggle(self):
        if self.engine:
            self.engine.librarian.set_training_mode(self.training_mode.get(), Tier.VALIDATED)

    def run(self):
        self.root.mainloop()


def main():
    IntellonGUI().run()

if __name__ == "__main__":
    main()
