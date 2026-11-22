import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "data.db"))
FIELDS = ("phrase", "translation", "note", "example")
TABLES = ("phrases", "suggestions")


def q(sql, args=()):
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        with c:
            return c.execute(sql, args).fetchall()
    finally:
        c.close()


def init():
    for t in TABLES:
        q(f"""CREATE TABLE IF NOT EXISTS {t} (
            id INTEGER PRIMARY KEY,
            phrase TEXT NOT NULL,
            translation TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            example TEXT NOT NULL DEFAULT '')""")
    q("CREATE TABLE IF NOT EXISTS imports (token TEXT PRIMARY KEY, data TEXT NOT NULL)")


def add(table, data):
    add_many(table, [data])


def add_many(table, rows):
    c = sqlite3.connect(DB_PATH)
    try:
        with c:  # one transaction: all rows or none
            c.executemany(f"INSERT INTO {table} (phrase, translation, note, example) VALUES (?, ?, ?, ?)",
                          [[d[f] for f in FIELDS] for d in rows])
    finally:
        c.close()


def update(table, id, data):
    q(f"UPDATE {table} SET phrase = ?, translation = ?, note = ?, example = ? WHERE id = ?",
      [data[f] for f in FIELDS] + [id])


def get(table, id):
    rows = q(f"SELECT * FROM {table} WHERE id = ?", (id,))
    return rows[0] if rows else None


def delete(table, id):
    q(f"DELETE FROM {table} WHERE id = ?", (id,))


def all_rows(table):
    return q(f"SELECT * FROM {table} ORDER BY phrase COLLATE NOCASE")


def random_phrase(exclude):
    marks = ",".join("?" * len(exclude))
    rows = q(f"SELECT * FROM phrases WHERE id NOT IN ({marks}) ORDER BY RANDOM() LIMIT 1", list(exclude))
    return rows[0] if rows else None


def random_others(id, limit=50):
    return q("SELECT * FROM phrases WHERE id != ? ORDER BY RANDOM() LIMIT ?", (id, limit))


def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similar(text, rows, max_ratio=0.4, limit=5):
    """Rows whose phrase is within max_ratio normalized edit distance of text."""
    text = text.casefold().strip()
    out = []
    for r in rows:
        other = r["phrase"].casefold().strip()
        d = levenshtein(text, other)
        if d / max(len(text), len(other), 1) <= max_ratio:
            out.append((d, r))
    out.sort(key=lambda x: x[0])
    return out[:limit]
