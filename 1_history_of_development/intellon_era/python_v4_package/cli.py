#!/usr/bin/env python3
"""
Intellon v4 — Interactive CLI

Commands:
  (any text)      Process through the engine
  /train FILE     Load a text file in training mode
  /wordnet        Load core vocabulary from WordNet
  /wordnet WORDS  Load specific words (comma-separated)
  /node NAME      Inspect a node by name
  /search TERM    Search for nodes matching a term
  /stats          Show network statistics
  /save FILE      Save network to SQLite
  /load FILE      Load network from SQLite
  /debug          Toggle debug output
  /training on|off  Toggle training mode
  /quit           Exit
"""

import sys
import os
try:
    import readline
except ImportError:
    pass

# Enable ANSI colors on Windows
if sys.platform == "win32":
    os.system("")  # triggers Windows to enable VT100 escape sequences

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intellon.core.engine import Engine
from intellon.core.models import Tier, NodeFlag
from intellon.core.training import load_wordnet, load_text_file, load_file, process_text, CORE_VOCABULARY
from intellon.core import storage


# --- Formatting helpers (works without rich) ---

def bold(s): return f"\033[1m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"
def green(s): return f"\033[32m{s}\033[0m"
def yellow(s): return f"\033[33m{s}\033[0m"
def cyan(s): return f"\033[36m{s}\033[0m"
def red(s): return f"\033[31m{s}\033[0m"
def magenta(s): return f"\033[35m{s}\033[0m"


class CLI:
    def __init__(self):
        self.engine = None
        self.debug = False

    def boot(self):
        """Initialize the engine with boot sequence."""
        print(f"\n{bold('Intellon v4 — Intellon Prototype')}")
        print(dim("Differentiation engine with register-based processing\n"))

        print("  Booting...", end="", flush=True)
        self.engine = Engine(run_boot=True)
        lib = self.engine.librarian
        print(f" {green('✓')} {lib.node_count} nodes, {lib.foundation_count} foundation")

    def run(self):
        """Main REPL loop."""
        self.boot()
        print(f"\n  Type text to process, or {cyan('/help')} for commands.\n")

        while True:
            try:
                raw = input(f"{bold('>')} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                break

            if not raw:
                continue

            if raw.startswith("/"):
                if not self._handle_command(raw):
                    break
            else:
                self._process_input(raw)

    def _process_input(self, text: str):
        """Process text through the engine and show results."""
        lib = self.engine.librarian

        # Show what the librarian recognizes
        assignment = lib.bundle(text)
        recognized = assignment.metadata["recognized"]
        recognized_names = []
        for addr in recognized:
            node = lib.get_node(addr)
            if node:
                recognized_names.append(node.name)

        if self.debug:
            print(f"\n  {dim('Recognized:')} {', '.join(recognized_names) if recognized_names else '(none)'}")
            print(f"  {dim('Context nodes:')} {len(assignment.context)}")
            print(f"  {dim('Foundation nodes:')} {len(assignment.foundation)}")

        # Process
        result = self.engine.process(text)

        # Show token pattern if found
        if result.synthesis and isinstance(result.synthesis.content, dict):
            content = result.synthesis.content
            pattern = content.get("pattern")

            if pattern and pattern.get("pattern_str"):
                print(f"\n  {cyan('Pattern:')} {pattern['pattern_str']}")
                if pattern.get("slots"):
                    for pos, fillers in pattern["slots"].items():
                        print(f"    {dim(f'slot [{pos}]:')} {', '.join(fillers)}")

            if self.debug:
                nc = content.get("node_comparisons", {})
                if nc:
                    print(f"  {dim('Comparisons:')} {nc.get('total', 0)} total — {nc.get('same', 0)} same, {nc.get('different', 0)} different")
                aspects = content.get("aspects", {})
                for asp, counts in list(aspects.items())[:5]:
                    print(f"    {dim(asp)}: {counts['same']}S {counts['diff']}D")

        # Show stubs created
        if result.stubs:
            new_words = [s.name for s in result.stubs if s.name]
            unique_new = list(dict.fromkeys(new_words))
            if unique_new:
                print(f"  {yellow('New:')} {', '.join(unique_new)}")

        # Summary line
        records = len(result.notepad)
        print(f"  {dim(f'[{records} records, {lib.node_count} nodes]')}")

    def _handle_command(self, raw: str) -> bool:
        """Handle a / command. Returns False to quit."""
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/exit", "/q"):
            return False

        elif cmd == "/help":
            print(__doc__)

        elif cmd == "/stats":
            self._show_stats()

        elif cmd == "/debug":
            self.debug = not self.debug
            print(f"  Debug: {green('on') if self.debug else red('off')}")

        elif cmd == "/wordnet":
            self._load_wordnet(arg)

        elif cmd == "/train":
            self._train_file(arg)

        elif cmd == "/training":
            self._toggle_training(arg)

        elif cmd == "/node":
            self._inspect_node(arg)

        elif cmd == "/search":
            self._search_nodes(arg)

        elif cmd == "/save":
            self._save(arg)

        elif cmd == "/load":
            self._load(arg)

        elif cmd == "/top":
            self._show_top(arg)

        else:
            print(f"  {red('Unknown command.')} Type {cyan('/help')} for options.")

        return True

    def _show_stats(self):
        lib = self.engine.librarian
        all_nodes = lib.get_all_nodes()

        tier_counts = {}
        flag_counts = {}
        total_defs = 0
        total_ptrs = 0
        for n in all_nodes:
            tier_counts[n.tier.name] = tier_counts.get(n.tier.name, 0) + 1
            total_defs += len(n.definitions)
            total_ptrs += len(n.pointers)
            for f in n.flags:
                flag_counts[f.value] = flag_counts.get(f.value, 0) + 1

        print(f"\n  {bold('Network Statistics')}")
        print(f"  {'Nodes:':<20} {lib.node_count}")
        print(f"  {'Foundation:':<20} {lib.foundation_count}")
        print(f"  {'Sessions:':<20} {lib.session_count}")
        print(f"  {'Definitions:':<20} {total_defs}")
        print(f"  {'Pointers:':<20} {total_ptrs}")

        print(f"\n  {bold('Tiers:')}")
        for t in ["INITIATOR", "IMPORTANT", "VALIDATED", "TRIAL"]:
            count = tier_counts.get(t, 0)
            bar = "█" * min(count // 2, 40)
            print(f"    {t:<12} {count:>5}  {dim(bar)}")

        print(f"\n  {bold('Flags:')}")
        for f, c in sorted(flag_counts.items(), key=lambda x: -x[1]):
            print(f"    {f:<12} {c:>5}")

    def _load_wordnet(self, arg: str):
        lib = self.engine.librarian
        if arg:
            words = [w.strip() for w in arg.split(",")]
        else:
            words = CORE_VOCABULARY

        pre = lib.node_count
        print(f"  Loading {len(words)} words from WordNet...", end="", flush=True)
        reg = load_wordnet(lib, words=words, tier=Tier.IMPORTANT)
        print(f" {green('✓')} {len(reg)} imported, {lib.node_count - pre} new nodes")

    def _train_file(self, arg: str):
        if not arg:
            print(f"  {red('Usage:')} /train FILEPATH")
            return
        if not os.path.exists(arg):
            print(f"  {red('File not found:')} {arg}")
            return

        ext = os.path.splitext(arg)[1].lower()
        print(f"  Training on {arg} ({ext or 'text'})...", end="", flush=True)
        stats = load_file(self.engine, arg, tier=Tier.VALIDATED)

        if "error" in stats:
            print(f" {red(stats['error'])}")
            return

        print(f" {green('✓')}")
        if "pages" in stats:
            print(f"    Pages: {stats['pages']}")
        if "sentences_processed" in stats:
            print(f"    Sentences: {stats['sentences_processed']}")
        if "rows_processed" in stats:
            print(f"    Rows: {stats['rows_processed']}")
        if "items_processed" in stats:
            print(f"    Items: {stats['items_processed']}")
        print(f"    New nodes: {stats.get('nodes_created', stats.get('nodes_after', 0) - stats.get('nodes_before', 0))}")
        if "notepad_records" in stats:
            print(f"    Notepad records: {stats['notepad_records']}")

    def _toggle_training(self, arg: str):
        if arg.lower() in ("on", "true", "1"):
            self.engine.librarian.set_training_mode(True, Tier.VALIDATED)
            print(f"  Training mode: {green('on')} (tier=VALIDATED)")
        elif arg.lower() in ("off", "false", "0"):
            self.engine.librarian.set_training_mode(False)
            print(f"  Training mode: {red('off')}")
        else:
            print(f"  {red('Usage:')} /training on|off")

    def _inspect_node(self, arg: str):
        if not arg:
            print(f"  {red('Usage:')} /node NAME")
            return

        lib = self.engine.librarian
        ids = lib.recognize(arg.lower())
        if not ids:
            print(f"  {red('Not found:')} \"{arg}\"")
            return

        for node_id in ids[:3]:
            node = lib.get_node(node_id)
            if not node:
                continue

            print(f"\n  {bold(node.name)} {dim(f'[{node.id[:12]}...]')}")
            print(f"  Tier: {cyan(node.tier.name)}  Flags: {', '.join(f.value for f in node.flags)}")

            if node.definitions:
                print(f"  {bold('Definitions:')}")
                for d in node.definitions[:6]:
                    content = str(d.content)[:70]
                    ptrs = f" {dim(f'({len(d.pointers)} ptrs)')}" if d.pointers else ""
                    print(f"    {d.number}. {content}{ptrs}")
                if len(node.definitions) > 6:
                    print(f"    {dim(f'... +{len(node.definitions) - 6} more')}")

            if node.char_pointers:
                chars = []
                for cp in node.char_pointers:
                    cn = lib.get_node(cp)
                    chars.append(cn.name if cn else "?")
                print(f"  Chars: {' → '.join(chars)}")

            if node.pointers:
                print(f"  {bold('Pointers:')} ({len(node.pointers)})")
                for p in node.pointers[:8]:
                    target = lib.get_node(p.target)
                    tname = target.name if target else p.target[:20]
                    print(f"    {p.relation} → {tname}")
                if len(node.pointers) > 8:
                    print(f"    {dim(f'... +{len(node.pointers) - 8} more')}")

            if node.tallies:
                top_tallies = sorted(node.tallies.items(), key=lambda x: -x[1])[:5]
                tally_str = ", ".join(f"{k}={v}" for k, v in top_tallies)
                print(f"  Tallies: {tally_str}")

    def _search_nodes(self, arg: str):
        if not arg:
            print(f"  {red('Usage:')} /search TERM")
            return

        lib = self.engine.librarian
        term = arg.lower()
        results = []
        for node in lib.get_all_nodes():
            if term in node.name.lower():
                results.append(node)

        if not results:
            print(f"  {red('No nodes matching')} \"{arg}\"")
            return

        print(f"\n  {len(results)} node(s) matching \"{arg}\":")
        for n in results[:20]:
            defs = len(n.definitions)
            ptrs = len(n.pointers)
            refs = n.tallies.get("referenced", 0)
            print(f"    {n.name:<20} tier={n.tier.name:<10} defs={defs} ptrs={ptrs} refs={refs}")
        if len(results) > 20:
            print(f"    {dim(f'... +{len(results) - 20} more')}")

    def _show_top(self, arg: str):
        """Show top N most referenced nodes."""
        n = int(arg) if arg.isdigit() else 15
        lib = self.engine.librarian
        all_nodes = lib.get_all_nodes()
        top = sorted(all_nodes, key=lambda nd: nd.tallies.get("sessions_involved", 0), reverse=True)[:n]

        print(f"\n  {bold(f'Top {n} by session involvement:')}")
        for nd in top:
            si = nd.tallies.get("sessions_involved", 0)
            refs = nd.tallies.get("referenced", 0)
            if si > 0:
                bar = "█" * min(si // 2, 30)
                print(f"    {nd.name:<15} {si:>4} sessions  {refs:>4} refs  {nd.tier.name:<10} {dim(bar)}")

    def _save(self, arg: str):
        path = arg or "intellon.db"
        print(f"  Saving to {path}...", end="", flush=True)
        storage.save(self.engine.librarian, path)
        print(f" {green('✓')} ({self.engine.librarian.node_count} nodes)")

    def _load(self, arg: str):
        path = arg or "intellon.db"
        if not os.path.exists(path):
            print(f"  {red('File not found:')} {path}")
            return
        print(f"  Loading from {path}...", end="", flush=True)
        # Create fresh engine without boot (we're loading state)
        self.engine = Engine(run_boot=False)
        storage.load(self.engine.librarian, path)
        print(f" {green('✓')} ({self.engine.librarian.node_count} nodes)")


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
