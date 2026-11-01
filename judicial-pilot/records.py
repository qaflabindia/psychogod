"""Single-host SQLite review archive. Each response and review has its own durable state."""
import fcntl
import json
import sqlite3
import threading
from contextlib import contextmanager
from uuid import UUID

import frontier

STATES = ("unreviewed","queued","running","complete","failed")


class Archive:
    def __init__(self, directory):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = directory / "responses.sqlite3"
        self.path.touch(mode=0o600, exist_ok=True)
        self.file_lock = (directory / "review-worker.lock").open("a")
        fcntl.flock(self.file_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.signal = threading.Event()
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY, created TEXT NOT NULL, form_id TEXT NOT NULL, version TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS items (
                    submission TEXT NOT NULL REFERENCES submissions(id), position INTEGER NOT NULL,
                    question TEXT NOT NULL, criteria TEXT NOT NULL, answer TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'unreviewed', review TEXT, error TEXT,
                    PRIMARY KEY(submission,position)
                );
            """)
            db.execute("UPDATE items SET state='failed',error=? WHERE state='running'",
                       ("Server restarted during review. Check provider usage before retrying.",))
        self.signal.set()

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, attempt, form, answers, bank):
        if not isinstance(attempt, str) or str(UUID(attempt)) != attempt:
            raise ValueError("Invalid attempt ID")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT form_id FROM submissions WHERE id=?", (attempt,)).fetchone()
            if prior:
                stored = [r[0] for r in db.execute("SELECT answer FROM items WHERE submission=? ORDER BY position",(attempt,))]
                if prior[0] != form["id"] or stored != [answers[q["id"]] for q in form["questions"]]:
                    raise FileExistsError("Receipt already exists for different content")
                return attempt
            db.execute("INSERT INTO submissions VALUES(?,?,?,?)", (attempt, frontier.now(), form["id"], form["version"]))
            db.executemany("INSERT INTO items(submission,position,question,criteria,answer) VALUES(?,?,?,?,?)",
                           [(attempt, i, json.dumps(q,ensure_ascii=False), json.dumps(bank.rubric(q),ensure_ascii=False),
                             answers[q["id"]]) for i,q in enumerate(form["questions"])])
        return attempt

    def list(self):
        with self.db() as db:
            rows = db.execute("""SELECT s.*,i.state,count(*) AS n FROM submissions s JOIN items i ON i.submission=s.id
                              GROUP BY s.id,i.state ORDER BY s.created DESC,s.rowid DESC""")
            result = {}
            for row in rows:
                entry = result.setdefault(row["id"],{"id":row["id"],"created":row["created"],"formId":row["form_id"],
                                  "version":row["version"],"counts":dict.fromkeys(STATES,0)})
                entry["counts"][row["state"]] = row["n"]
        return {"submissions":list(result.values()),"reviewer":{"model":frontier.MODEL,"configured":frontier.configured()}}

    def get(self, key):
        with self.db() as db:
            row = db.execute("SELECT * FROM submissions WHERE id=?", (key,)).fetchone()
            if row is None:
                raise KeyError(key)
            items = [{"question":json.loads(r["question"]), "criteria":json.loads(r["criteria"]), "answer":r["answer"],
                      "state":r["state"],"review":json.loads(r["review"]) if r["review"] else None,"error":r["error"]}
                     for r in db.execute("SELECT * FROM items WHERE submission=? ORDER BY position",(key,))]
        return {"id":key,"created":row["created"],"version":row["version"],"formId":row["form_id"],
                "model":frontier.MODEL,"items":items}

    def enqueue(self, key):
        with self.db() as db:
            if not db.execute("SELECT 1 FROM submissions WHERE id=?", (key,)).fetchone():
                raise KeyError(key)
            count = db.execute("UPDATE items SET state='queued',error=NULL WHERE submission=? AND state IN ('unreviewed','failed')",
                               (key,)).rowcount
        self.signal.set()
        return count

    def run_one(self, reviewer):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM items WHERE state='queued' ORDER BY rowid LIMIT 1").fetchone()
            if not row:
                return False
            key = (row["submission"],row["position"])
            db.execute("UPDATE items SET state='running' WHERE submission=? AND position=?",key)
        try:
            result = reviewer({"question":json.loads(row["question"]), "answer":row["answer"],
                               "criteria":json.loads(row["criteria"])})
            state, review, error = "complete", json.dumps(result,ensure_ascii=False), None
        except Exception as exc:
            # Only the HTTP adapter emits safe provider messages. Never store raw inputs/keys or stack traces.
            error = str(exc) if type(exc) is RuntimeError else "No verified review returned. Check connectivity and provider usage before retrying."
            state, review = "failed", None
        with self.db() as db:
            db.execute("UPDATE items SET state=?,review=?,error=? WHERE submission=? AND position=?",(state,review,error,*key))
            if state == "failed":
                db.execute("UPDATE items SET state='failed',error=? WHERE submission=? AND state='queued'",
                           ("Batch paused after an earlier failure. These items can be retried.",key[0]))
        return True

    def worker(self):
        while True:
            self.signal.wait()
            self.signal.clear()
            if frontier.configured():
                while self.run_one(frontier.review):
                    pass
