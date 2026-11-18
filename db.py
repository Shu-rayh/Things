import sqlite3
import time

class IdentityDB:
    def __init__(self, path="identities.db", timeout=2.0):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.timeout = timeout   # seconds unseen before a sighting ends
        self.active = {}         # track_id -> {"uid", "sighting_id", "start", "last_seen"}
        self._create_tables()
        cur = self.conn.execute(
            "INSERT INTO sessions (started) VALUES (?)", (time.time(),))
        self.session_id = cur.lastrowid
        self.conn.commit()

    def _create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS identities (
            uid INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            name TEXT,
            first_seen REAL,
            last_seen REAL,
            total_seconds REAL DEFAULT 0,
            sighting_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            started REAL,
            ended REAL
        );
        CREATE TABLE IF NOT EXISTS sightings (
            sighting_id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            session_id INTEGER,
            start REAL,
            end REAL
        );
        """)
        self.conn.commit()

    def update(self, objects):
        """Call once per frame. Adds a 'uid' key to each object dict."""
        now = time.time()
        seen = set()

        for o in objects:
            tid = o["id"]
            seen.add(tid)
            if tid not in self.active:
                uid = self._new_identity(o["label"], now)
                cur = self.conn.execute(
                    "INSERT INTO sightings (uid, session_id, start, end) "
                    "VALUES (?, ?, ?, ?)", (uid, self.session_id, now, now))
                self.conn.execute(
                    "UPDATE identities SET sighting_count = sighting_count + 1 "
                    "WHERE uid = ?", (uid,))
                self.conn.commit()
                self.active[tid] = {"uid": uid, "sighting_id": cur.lastrowid,
                                    "start": now, "last_seen": now}
            self.active[tid]["last_seen"] = now
            o["uid"] = self.active[tid]["uid"]

        for tid in list(self.active):
            if tid not in seen and now - self.active[tid]["last_seen"] > self.timeout:
                self._close(tid)

        return objects

    def _new_identity(self, label, now):
        cur = self.conn.execute(
            "INSERT INTO identities (label, first_seen, last_seen) VALUES (?, ?, ?)",
            (label, now, now))
        return cur.lastrowid

    def _close(self, tid):
        a = self.active.pop(tid)
        duration = a["last_seen"] - a["start"]
        self.conn.execute(
            "UPDATE sightings SET end = ? WHERE sighting_id = ?",
            (a["last_seen"], a["sighting_id"]))
        self.conn.execute(
            "UPDATE identities SET last_seen = ?, total_seconds = total_seconds + ? "
            "WHERE uid = ?", (a["last_seen"], duration, a["uid"]))
        self.conn.commit()

    def rename(self, uid, name):
        self.conn.execute("UPDATE identities SET name = ? WHERE uid = ?", (name, uid))
        self.conn.commit()

    def get_name(self, uid):
        row = self.conn.execute(
            "SELECT name FROM identities WHERE uid = ?", (uid,)).fetchone()
        return row["name"] if row else None

    def close(self):
        for tid in list(self.active):
            self._close(tid)
        self.conn.execute(
            "UPDATE sessions SET ended = ? WHERE session_id = ?",
            (time.time(), self.session_id))
        self.conn.commit()
        self.conn.close()