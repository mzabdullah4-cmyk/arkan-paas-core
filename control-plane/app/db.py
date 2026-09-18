import json
import os
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("ARKAN_DB_PATH", "/data/arkan.db")


def _connect() -> sqlite3.Connection:
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, language TEXT NOT NULL, content TEXT NOT NULL, storage_path TEXT, sha256 TEXT, size INTEGER, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id));
        CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, artifact_id TEXT NOT NULL, engine TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3, result TEXT, error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id), FOREIGN KEY(artifact_id) REFERENCES artifacts(id));
        """)
        for table, column, definition in [("artifacts", "storage_path", "TEXT"), ("artifacts", "sha256", "TEXT"), ("artifacts", "size", "INTEGER"), ("jobs", "attempts", "INTEGER NOT NULL DEFAULT 0"), ("jobs", "max_attempts", "INTEGER NOT NULL DEFAULT 3")]:
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _decode(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    value = dict(row)
    if value.get("result"):
        try:
            value["result"] = json.loads(value["result"])
        except json.JSONDecodeError:
            pass
    return value


def _rows(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [_decode(row) for row in rows]


def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    project_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute("INSERT INTO projects (id, name, description) VALUES (?, ?, ?)", (project_id, name, description))
    return fetch_project(project_id)


def list_projects() -> List[Dict[str, Any]]:
    with _connect() as conn:
        return _rows(conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall())


def fetch_project(project_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        return _decode(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())


def create_artifact(project_id: str, name: str, language: str, content: str, storage_path: Optional[str] = None, sha256: Optional[str] = None, size: Optional[int] = None) -> Dict[str, Any]:
    artifact_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute("INSERT INTO artifacts (id, project_id, name, language, content, storage_path, sha256, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (artifact_id, project_id, name, language, content, storage_path, sha256, size))
    return fetch_artifact(artifact_id)


def fetch_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        return _decode(conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone())


def list_artifacts(project_id: str) -> List[Dict[str, Any]]:
    with _connect() as conn:
        return _rows(conn.execute("SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall())


def create_job(project_id: str, artifact_id: str, engine: str, max_attempts: int = 3) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute("INSERT INTO jobs (id, project_id, artifact_id, engine, max_attempts) VALUES (?, ?, ?, ?, ?)", (job_id, project_id, artifact_id, engine, max_attempts))
    return fetch_job(job_id)


def fetch_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        return _decode(_connect_row("SELECT * FROM jobs WHERE id = ?", (job_id,)))


def _connect_row(query: str, params: tuple) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(query, params).fetchone()


def list_jobs() -> List[Dict[str, Any]]:
    with _connect() as conn:
        return _rows(conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall())


def job_payload(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT j.id, j.project_id, j.artifact_id, j.engine, j.status, j.attempts, j.max_attempts, a.name, a.language, a.content, a.storage_path FROM jobs j JOIN artifacts a ON a.id = j.artifact_id WHERE j.id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def update_job(job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None, increment_attempt: bool = False) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        if increment_attempt:
            conn.execute("UPDATE jobs SET attempts = attempts + 1, status = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, error, job_id))
        else:
            conn.execute("UPDATE jobs SET status = ?, result = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, json.dumps(result) if result is not None else None, error, job_id))
    return fetch_job(job_id)
