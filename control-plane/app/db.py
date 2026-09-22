import hashlib
import json
import os
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("ARKAN_DB_PATH", "/data/arkan.db")
ARTIFACT_ROOT = os.getenv("ARKAN_ARTIFACT_ROOT", "/artifacts")


def connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, language TEXT NOT NULL, content TEXT NOT NULL, sha256 TEXT, size INTEGER, storage_path TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, artifact_id TEXT NOT NULL, engine TEXT NOT NULL, status TEXT DEFAULT 'queued', attempts INTEGER DEFAULT 0, max_attempts INTEGER DEFAULT 3, result TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        for table, column, definition in [("artifacts", "sha256", "TEXT"), ("artifacts", "size", "INTEGER"), ("artifacts", "storage_path", "TEXT"), ("jobs", "attempts", "INTEGER DEFAULT 0"), ("jobs", "max_attempts", "INTEGER DEFAULT 3")]:
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def decode(row):
    if not row:
        return None
    value = dict(row)
    if value.get("result"):
        value["result"] = json.loads(value["result"])
    return value


def rows(result): return [decode(row) for row in result]
def fetch(query, params=()):
    with connect() as conn: return conn.execute(query, params).fetchone()

def create_project(name, description=None):
    ident = str(uuid.uuid4())
    with connect() as conn: conn.execute("INSERT INTO projects(id,name,description) VALUES(?,?,?)", (ident, name, description))
    return decode(fetch("SELECT * FROM projects WHERE id=?", (ident,)))

def projects():
    with connect() as conn: return rows(conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall())
def project(ident): return decode(fetch("SELECT * FROM projects WHERE id=?", (ident,)))
def artifact(ident): return decode(fetch("SELECT * FROM artifacts WHERE id=?", (ident,)))
def artifacts(project_id):
    with connect() as conn: return rows(conn.execute("SELECT * FROM artifacts WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall())
def jobs():
    with connect() as conn: return rows(conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall())
def job(ident): return decode(fetch("SELECT * FROM jobs WHERE id=?", (ident,)))

def create_artifact(project_id, name, language, content):
    ident = str(uuid.uuid4())
    raw = content.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    directory = os.path.join(ARTIFACT_ROOT, ident[:2]); os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, ident)
    with open(path, "wb") as stream: stream.write(raw)
    with connect() as conn:
        conn.execute("INSERT INTO artifacts(id,project_id,name,language,content,sha256,size,storage_path) VALUES(?,?,?,?,?,?,?,?)", (ident, project_id, name, language.lower(), content, digest, len(raw), path))
    return artifact(ident)

def create_job(project_id, artifact_id, engine, max_attempts=3):
    ident = str(uuid.uuid4())
    with connect() as conn: conn.execute("INSERT INTO jobs(id,project_id,artifact_id,engine,max_attempts) VALUES(?,?,?,?,?)", (ident, project_id, artifact_id, engine.lower(), max_attempts))
    return job(ident)

def payload(ident):
    return dict(fetch("SELECT j.*,a.name,a.language,a.content,a.sha256,a.size FROM jobs j JOIN artifacts a ON a.id=j.artifact_id WHERE j.id=?", (ident,)) or {}) or None

def update_job(ident, status, result=None, error=None, increment=False):
    with connect() as conn:
        if increment: conn.execute("UPDATE jobs SET attempts=attempts+1,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, ident))
        else: conn.execute("UPDATE jobs SET status=?,result=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, json.dumps(result) if result is not None else None, error, ident))
    return job(ident)
