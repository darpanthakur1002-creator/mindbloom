from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator

from .config import settings


def _database_file() -> Path:
    path = Path(settings.database_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS check_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mood TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            title TEXT NOT NULL,
            kind TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            contact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS heart_rate_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            heart_rate INTEGER NOT NULL,
            source TEXT NOT NULL DEFAULT 'manual',
            recorded_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_check_ins_user ON check_ins(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_completions(user_id, completed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_heart_rate_user ON heart_rate_readings(user_id, recorded_at DESC);
        """
    )
    try:
        connection.execute("ALTER TABLE activity_completions ADD COLUMN score INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    database = sqlite3.connect(_database_file())
    database.row_factory = sqlite3.Row
    _initialize(database)
    try:
        yield database
        database.commit()
    finally:
        database.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_check_in(user_id: str, mood: str, note: str) -> dict:
    created_at = now()
    with connection() as database:
        cursor = database.execute(
            "INSERT INTO check_ins (user_id, mood, note, created_at) VALUES (?, ?, ?, ?)",
            (user_id, mood, note, created_at),
        )
        return {"id": cursor.lastrowid, "mood": mood, "note": note, "created_at": created_at}


def latest_check_in(user_id: str) -> dict | None:
    with connection() as database:
        row = database.execute(
            "SELECT id, mood, note, created_at FROM check_ins WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def create_heart_rate(user_id: str, heart_rate: int, source: str) -> dict:
    recorded_at = now()
    with connection() as database:
        database.execute(
            "INSERT INTO heart_rate_readings (user_id, heart_rate, source, recorded_at) VALUES (?, ?, ?, ?)",
            (user_id, heart_rate, source, recorded_at),
        )
    return {"heart_rate": heart_rate, "source": source, "recorded_at": recorded_at}


def latest_heart_rate(user_id: str) -> dict | None:
    with connection() as database:
        row = database.execute(
            "SELECT heart_rate, source, recorded_at FROM heart_rate_readings WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def complete_activity(user_id: str, activity_id: str, title: str, kind: str, score: int) -> dict:
    completed_at = now()
    with connection() as database:
        database.execute(
            "INSERT INTO activity_completions (user_id, activity_id, title, kind, score, completed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, activity_id, title, kind, score, completed_at),
        )
        row = database.execute(
            "SELECT activity_id, title, kind, COUNT(*) AS completions, MAX(completed_at) AS last_completed_at, MAX(score) AS best_score "
            "FROM activity_completions WHERE user_id = ? AND activity_id = ? GROUP BY activity_id, title, kind",
            (user_id, activity_id),
        ).fetchone()
        last_score = database.execute(
            "SELECT score FROM activity_completions WHERE user_id = ? AND activity_id = ? ORDER BY completed_at DESC LIMIT 1",
            (user_id, activity_id),
        ).fetchone()["score"]
    result = dict(row)
    result["last_score"] = last_score
    return result


def activity_progress(user_id: str) -> list[dict]:
    with connection() as database:
        rows = database.execute(
            "SELECT activity_id, title, kind, COUNT(*) AS completions, MAX(completed_at) AS last_completed_at, "
            "(SELECT score FROM activity_completions latest WHERE latest.user_id = activity_completions.user_id "
            "AND latest.activity_id = activity_completions.activity_id ORDER BY latest.completed_at DESC LIMIT 1) AS last_score, "
            "MAX(score) AS best_score "
            "FROM activity_completions WHERE user_id = ? GROUP BY activity_id, title, kind ORDER BY last_completed_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_memory(user_id: str, title: str, detail: str) -> dict:
    created_at = now()
    with connection() as database:
        cursor = database.execute(
            "INSERT INTO memories (user_id, title, detail, created_at) VALUES (?, ?, ?, ?)",
            (user_id, title, detail, created_at),
        )
        return {"id": cursor.lastrowid, "title": title, "detail": detail, "created_at": created_at}


def list_memories(user_id: str) -> list[dict]:
    with connection() as database:
        rows = database.execute(
            "SELECT id, title, detail, created_at FROM memories WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_invite(user_id: str, contact: str) -> dict:
    created_at = now()
    with connection() as database:
        cursor = database.execute(
            "INSERT INTO invites (user_id, contact, status, created_at) VALUES (?, ?, 'pending', ?)",
            (user_id, contact, created_at),
        )
        return {"id": cursor.lastrowid, "contact": contact, "status": "pending", "created_at": created_at}
