"""Local SQLite store — the offline mirror of the Meko datapack.

Every memory / conversation / decision trace written to Meko is mirrored
here, so the agent works end-to-end without a Meko API key (local demo
mode) and keeps a durable local copy when Meko is configured. The local
store never holds a private key — see wallet.py.
"""
import json
import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'local',   -- 'local' | 'meko'
    meko_id TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS quests (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    chain TEXT NOT NULL,
    description TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    reward_points INTEGER NOT NULL DEFAULT 0,
    risk_note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS progress (
    quest_id TEXT PRIMARY KEY REFERENCES quests(id),
    status TEXT NOT NULL DEFAULT 'todo',    -- todo | in_progress | done
    steps_done INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    meko_conversation_id TEXT,
    user_input TEXT NOT NULL,
    assistant_output TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS decision_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    memory_used_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(db_path=None):
    path = Path(db_path) if db_path else config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def add_memory(conn, text, source="local", meko_id=None, metadata=None):
    cur = conn.execute(
        "INSERT INTO memories (text, source, meko_id, metadata_json) VALUES (?, ?, ?, ?)",
        (text, source, meko_id, json.dumps(metadata or {})),
    )
    conn.commit()
    return cur.lastrowid


def search_memories_local(conn, query, limit=5):
    """Keyword fallback search over the local mirror (Meko does semantic)."""
    words = [w for w in query.lower().split() if len(w) > 2]
    rows = conn.execute(
        "SELECT id, text, source, created_at FROM memories ORDER BY id DESC LIMIT 200"
    ).fetchall()
    scored = []
    for row in rows:
        hay = row["text"].lower()
        score = sum(2 if w in hay else 0 for w in words)
        if words and query.lower() in hay:
            score += 3
        if score > 0 or not words:
            scored.append((score, dict(row)))
    scored.sort(key=lambda item: (-item[0], -item[1]["id"]))
    return [row for _, row in scored[:limit]]


def list_memories(conn, limit=20):
    rows = conn.execute(
        "SELECT id, text, source, created_at FROM memories ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_quest(conn, quest):
    conn.execute(
        """INSERT INTO quests (id, title, category, chain, description, steps_json,
               reward_points, risk_note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET title=excluded.title,
               category=excluded.category, chain=excluded.chain,
               description=excluded.description, steps_json=excluded.steps_json,
               reward_points=excluded.reward_points, risk_note=excluded.risk_note""",
        (quest["id"], quest["title"], quest["category"], quest["chain"],
         quest["description"], json.dumps(quest["steps"]),
         quest.get("reward_points", 0), quest.get("risk_note", "")),
    )
    conn.execute(
        "INSERT OR IGNORE INTO progress (quest_id) VALUES (?)", (quest["id"],)
    )
    conn.commit()


def list_quests(conn):
    rows = conn.execute(
        """SELECT q.*, p.status, p.steps_done FROM quests q
           LEFT JOIN progress p ON p.quest_id = q.id ORDER BY q.id"""
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["steps"] = json.loads(d["steps_json"])
        out.append(d)
    return out


def get_quest(conn, quest_id):
    row = conn.execute(
        """SELECT q.*, p.status, p.steps_done FROM quests q
           LEFT JOIN progress p ON p.quest_id = q.id WHERE q.id = ?""",
        (quest_id,),
    ).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["steps"] = json.loads(d["steps_json"])
    return d


def set_progress(conn, quest_id, status, steps_done):
    conn.execute(
        """INSERT INTO progress (quest_id, status, steps_done, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(quest_id) DO UPDATE SET status=excluded.status,
           steps_done=excluded.steps_done, updated_at=datetime('now')""",
        (quest_id, status, steps_done),
    )
    conn.commit()


def add_conversation(conn, session_id, user_input, assistant_output, meko_conversation_id=None):
    cur = conn.execute(
        """INSERT INTO conversations (session_id, meko_conversation_id,
           user_input, assistant_output) VALUES (?, ?, ?, ?)""",
        (session_id, meko_conversation_id, user_input, assistant_output),
    )
    conn.commit()
    return cur.lastrowid


def add_decision_trace(conn, decision, reasoning, memory_used=None):
    cur = conn.execute(
        "INSERT INTO decision_traces (decision, reasoning, memory_used_json) VALUES (?, ?, ?)",
        (decision, reasoning, json.dumps(memory_used or [])),
    )
    conn.commit()
    return cur.lastrowid


def list_decision_traces(conn, limit=20):
    rows = conn.execute(
        "SELECT id, decision, reasoning, created_at FROM decision_traces "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
