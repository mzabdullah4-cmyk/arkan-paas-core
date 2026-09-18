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
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                language TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                engine TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
            );
            """
        )

        columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
        if "error" not in columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN error TEXT")


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


def _rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [_decode(row) for row in rows]


def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    project_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, description) VALUES (?, ?, ?)",
            (project_id, name, description),
        )
    return fetch_project(project_id)


def list_projects() -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return _rows_to_list(rows)


def fetch_project(project_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _decode(row)


def create_artifact(project_id: str, name: str, language: str, content: str) -> Dict[str, Any]:
    artifact_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO artifacts (id, project_id, name, language, content) VALUES (?, ?, ?, ?, ?)",
            (artifact_id, project_id, name, language, content),
        )
    return fetch_artifact(artifact_id)


def fetch_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    return _decode(row)


def list_artifacts(project_id: str) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
    return _rows_to_list(rows)


def create_job(project_id: str, artifact_id: str, engine: str) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, project_id, artifact_id, engine, status) VALUES (?, ?, ?, ?, 'queued')",
            (job_id, project_id, artifact_id, engine),
        )
    return fetch_job(job_id)


def fetch_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _decode(row)


def list_jobs() -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return _rows_to_list(rows)


def job_payload(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT j.id, j.project_id, j.artifact_id, j.engine, a.name, a.language, a.content, j.status
            FROM jobs j
            JOIN artifacts a ON a.id = j.artifact_id
            WHERE j.id = ?
            """,
            (job_id,),
        ).fetchone()
    return dict(row) if row else None


def update_job(job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, result = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, json.dumps(result) if result is not None else None, error, job_id),
        )
    return fetch_job(job_id)
