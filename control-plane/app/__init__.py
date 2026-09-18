import os
import sqlite3
import json
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("ARKAN_DB_PATH", os.path.join(os.getcwd(), "data", "arkan.db"))


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                language TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                engine TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                result TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(artifact_id) REFERENCES artifacts(id)
            )
            """
        )
        conn.commit()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    value = dict(row)
    if value.get("result"):
        value["result"] = json.loads(value["result"])
    return value


def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    import uuid
    project_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, description) VALUES (?, ?, ?)",
            (project_id, name, description),
        )
        conn.commit()
    return fetch_project(project_id)


def list_projects() -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def fetch_project(project_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _row_to_dict(row)


def create_artifact(project_id: str, name: str, language: str, content: str) -> Dict[str, Any]:
    import uuid
    artifact_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO artifacts (id, project_id, name, language, content) VALUES (?, ?, ?, ?, ?)",
            (artifact_id, project_id, name, language, content),
        )
        conn.commit()
    return fetch_artifact(artifact_id)


def fetch_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    return _row_to_dict(row)


def list_artifacts(project_id: str) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def create_job(project_id: str, artifact_id: str, engine: str) -> Dict[str, Any]:
    import uuid
    job_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO jobs (id, project_id, artifact_id, engine, status, result) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, project_id, artifact_id, engine, "queued", None),
        )
        conn.commit()
    return fetch_job(job_id)


def fetch_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row)


def list_jobs() -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def update_job(job_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    encoded = json.dumps(result) if result is not None else None
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, encoded, job_id),
        )
        conn.commit()
    return fetch_job(job_id)
