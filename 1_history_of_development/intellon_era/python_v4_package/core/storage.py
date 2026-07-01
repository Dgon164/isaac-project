"""
Intellon v4 — SQLite Persistence

Save and load the entire knowledge network to/from disk.
The system retains what it learns between sessions.
"""

from __future__ import annotations
import sqlite3
import json
from typing import TYPE_CHECKING
from datetime import datetime

from .models import Node, Tier, NodeFlag, Definition, Pointer, Constraint, Origin, NodeContext

if TYPE_CHECKING:
    from .librarian import Librarian


DB_VERSION = 1


def save(librarian: Librarian, path: str):
    """Save the entire network to a SQLite database."""
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS meta")
    c.execute("DROP TABLE IF EXISTS nodes")
    c.execute("DROP TABLE IF EXISTS definitions")
    c.execute("DROP TABLE IF EXISTS pointers")
    c.execute("DROP TABLE IF EXISTS char_pointers")
    c.execute("DROP TABLE IF EXISTS constraints")
    c.execute("DROP TABLE IF EXISTS tallies")
    c.execute("DROP TABLE IF EXISTS foundation")

    c.execute("""CREATE TABLE meta (
        key TEXT PRIMARY KEY, value TEXT
    )""")
    c.execute("""CREATE TABLE nodes (
        id TEXT PRIMARY KEY,
        name TEXT,
        tier INTEGER,
        flags TEXT,
        origin_session TEXT,
        origin_inputs TEXT,
        origin_timestamp TEXT
    )""")
    c.execute("""CREATE TABLE definitions (
        node_id TEXT, number INTEGER, content TEXT,
        pointers TEXT, see_also TEXT,
        PRIMARY KEY (node_id, number)
    )""")
    c.execute("""CREATE TABLE pointers (
        node_id TEXT, target TEXT, relation TEXT
    )""")
    c.execute("""CREATE TABLE char_pointers (
        node_id TEXT, position INTEGER, target TEXT
    )""")
    c.execute("""CREATE TABLE constraints (
        node_id TEXT, subject TEXT, relation TEXT, object TEXT, polarity INTEGER
    )""")
    c.execute("""CREATE TABLE tallies (
        node_id TEXT, category TEXT, count INTEGER,
        PRIMARY KEY (node_id, category)
    )""")
    c.execute("""CREATE TABLE foundation (id TEXT PRIMARY KEY)""")

    # Meta
    c.execute("INSERT INTO meta VALUES (?, ?)", ("version", str(DB_VERSION)))
    c.execute("INSERT INTO meta VALUES (?, ?)", ("node_count", str(librarian.node_count)))
    c.execute("INSERT INTO meta VALUES (?, ?)", ("saved_at", datetime.utcnow().isoformat()))

    # Nodes
    all_nodes = librarian.get_all_nodes()
    for node in all_nodes:
        flags_str = json.dumps([f.value for f in node.flags])
        origin_session = node.origin.session_id if node.origin else ""
        origin_inputs = json.dumps(node.origin.inputs) if node.origin else "[]"
        origin_ts = node.origin.timestamp.isoformat() if node.origin else ""

        c.execute("INSERT INTO nodes VALUES (?,?,?,?,?,?,?)", (
            node.id, node.name, int(node.tier), flags_str,
            origin_session, origin_inputs, origin_ts,
        ))

        for defn in node.definitions:
            defn_ptrs = json.dumps([{"target": p.target, "relation": p.relation} for p in defn.pointers])
            defn_sa = json.dumps(defn.see_also)
            content_str = json.dumps(defn.content) if not isinstance(defn.content, str) else defn.content
            c.execute("INSERT INTO definitions VALUES (?,?,?,?,?)", (
                node.id, defn.number, content_str, defn_ptrs, defn_sa,
            ))

        for ptr in node.pointers:
            c.execute("INSERT INTO pointers VALUES (?,?,?)", (node.id, ptr.target, ptr.relation))

        for i, cp in enumerate(node.char_pointers):
            c.execute("INSERT INTO char_pointers VALUES (?,?,?)", (node.id, i, cp))

        for con in node.constraints:
            c.execute("INSERT INTO constraints VALUES (?,?,?,?,?)", (
                node.id, con.subject, con.relation, con.object, int(con.polarity),
            ))

        for cat, count in node.tallies.items():
            c.execute("INSERT INTO tallies VALUES (?,?,?)", (node.id, cat, count))

    # Foundation set
    for addr in librarian._foundation:
        c.execute("INSERT INTO foundation VALUES (?)", (addr,))

    conn.commit()
    conn.close()


def load(librarian: Librarian, path: str):
    """Load a network from a SQLite database into the librarian."""
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # Load nodes
    c.execute("SELECT * FROM nodes")
    for row in c.fetchall():
        node_id, name, tier_int, flags_str, origin_session, origin_inputs, origin_ts = row

        flags = set()
        for fv in json.loads(flags_str):
            try:
                flags.add(NodeFlag(fv))
            except ValueError:
                pass

        origin = None
        if origin_session:
            origin = Origin(
                session_id=origin_session,
                inputs=json.loads(origin_inputs),
                timestamp=datetime.fromisoformat(origin_ts) if origin_ts else datetime.utcnow(),
            )

        node = Node(
            id=node_id,
            name=name,
            tier=Tier(tier_int),
            flags=flags,
            origin=origin,
        )

        # Definitions
        c2 = conn.cursor()
        c2.execute("SELECT number, content, pointers, see_also FROM definitions WHERE node_id=? ORDER BY number", (node_id,))
        for drow in c2.fetchall():
            dnum, dcontent, dptrs_str, dsa_str = drow
            dptrs = [Pointer(target=p["target"], relation=p["relation"]) for p in json.loads(dptrs_str)]
            dsa = json.loads(dsa_str)
            # Try to parse content as JSON (for non-string content)
            try:
                parsed = json.loads(dcontent)
                if isinstance(parsed, str):
                    parsed = dcontent  # Keep as string
                dcontent = parsed
            except (json.JSONDecodeError, TypeError):
                pass
            node.definitions.append(Definition(number=dnum, content=dcontent, pointers=dptrs, see_also=dsa))

        # Pointers
        c2.execute("SELECT target, relation FROM pointers WHERE node_id=?", (node_id,))
        for prow in c2.fetchall():
            node.pointers.append(Pointer(target=prow[0], relation=prow[1]))

        # Char pointers
        c2.execute("SELECT target FROM char_pointers WHERE node_id=? ORDER BY position", (node_id,))
        node.char_pointers = [r[0] for r in c2.fetchall()]

        # Constraints
        c2.execute("SELECT subject, relation, object, polarity FROM constraints WHERE node_id=?", (node_id,))
        for crow in c2.fetchall():
            node.constraints.append(Constraint(subject=crow[0], relation=crow[1], object=crow[2], polarity=bool(crow[3])))

        # Tallies
        c2.execute("SELECT category, count FROM tallies WHERE node_id=?", (node_id,))
        for trow in c2.fetchall():
            node.tallies[trow[0]] = trow[1]

        librarian.store_node(node)

    # Foundation set
    c.execute("SELECT id FROM foundation")
    for row in c.fetchall():
        librarian._foundation.add(row[0])
        node = librarian.get_node(row[0])
        if node:
            node.flags.add(NodeFlag.FOUNDATION)

    conn.close()
