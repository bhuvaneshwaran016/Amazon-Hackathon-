import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv("TASKPILOT_DB", "taskpilot.db")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True) if Path(DB_PATH).parent != Path(".") else None
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            )
        """)

def create_task(title: str, description: str = "", due_date: str = "", priority: str = "medium"):
    title = (title or "").strip()
    if not title:
        return {"ok": False, "error": "Task title cannot be empty."}
    if len(title) > 180:
        return {"ok": False, "error": "Task title must be 180 characters or fewer."}
    priority = priority.lower().strip()
    if priority not in {"low", "medium", "high"}:
        priority = "medium"
    with connect() as con:
        cur = con.execute(
            "INSERT INTO tasks(title,description,due_date,priority,status,created_at) VALUES(?,?,?,?,?,?)",
            (title, (description or "")[:2000], (due_date or "")[:40], priority, "open",
             datetime.now(timezone.utc).isoformat())
        )
        row = con.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone()
        return {"ok": True, "task": dict(row)}

def list_tasks(status: str = "all"):
    status = (status or "all").lower()
    if status not in {"all", "open", "done"}:
        status = "all"
    with connect() as con:
        if status == "all":
            rows = con.execute("SELECT * FROM tasks ORDER BY status='done', id DESC").fetchall()
        else:
            rows = con.execute("SELECT * FROM tasks WHERE status=? ORDER BY id DESC",(status,)).fetchall()
        return {"ok": True, "tasks": [dict(r) for r in rows], "count": len(rows)}

def complete_task(task_id: int):
    with connect() as con:
        cur = con.execute("UPDATE tasks SET status='done' WHERE id=?", (int(task_id),))
        if cur.rowcount == 0:
            return {"ok": False, "error": f"No task found with id {task_id}."}
        row = con.execute("SELECT * FROM tasks WHERE id=?", (int(task_id),)).fetchone()
        return {"ok": True, "task": dict(row)}

def delete_task(task_id: int):
    with connect() as con:
        row = con.execute("SELECT * FROM tasks WHERE id=?", (int(task_id),)).fetchone()
        if row is None:
            return {"ok": False, "error": f"No task found with id {task_id}."}
        con.execute("DELETE FROM tasks WHERE id=?", (int(task_id),))
        return {"ok": True, "deleted_id": int(task_id), "title": row["title"]}
