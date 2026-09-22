from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import Optional

from .db import create_artifact, create_job, create_project, fetch_artifact, fetch_job, fetch_project, init_db, job_payload, list_artifacts, list_jobs, list_projects, update_job
from .queue import queue_job
from .services import get_engine, list_engines, store_artifact

app = FastAPI(title="Arkan Control Plane", version="0.4.0")

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)

class ArtifactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    language: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)

class JobCreate(BaseModel):
    project_id: str
    artifact_id: str
    engine: str = "sqlglot"
    max_attempts: int = Field(default=3, ge=1, le=10)

class JobResult(BaseModel):
    result: Optional[dict] = None
    error: Optional[str] = None

@app.on_event("startup")
def startup_event() -> None:
    init_db()

@app.get("/")
def root() -> dict:
    return {"status": "online", "service": "Arkan API Gateway", "version": "0.4.0"}

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "control-plane"}

@app.get("/engines")
def engines() -> dict:
    return {"engines": list_engines()}

@app.get("/engines/{engine_name}")
def engine(engine_name: str) -> dict:
    try:
        return get_engine(engine_name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Engine not found")

@app.post("/projects")
def create_project_endpoint(payload: ProjectCreate) -> dict:
    return create_project(payload.name, payload.description)

@app.get("/projects")
def get_projects() -> dict:
    return {"projects": list_projects()}

@app.get("/projects/{project_id}")
def get_project(project_id: str) -> dict:
    project = fetch_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/projects/{project_id}/artifacts")
def add_artifact(project_id: str, payload: ArtifactCreate) -> dict:
    if not fetch_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    raw = payload.content.encode("utf-8")
    stored = store_artifact(raw)
    return create_artifact(project_id, payload.name, payload.language, payload.content, stored["path"], stored["sha256"], stored["size"])

@app.post("/projects/{project_id}/artifacts/upload")
async def upload_artifact(project_id: str, language: str, file: UploadFile = File(...)) -> dict:
    if not fetch_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded artifact is empty")
    stored = store_artifact(raw)
    content = raw.decode("utf-8", errors="replace")
    return create_artifact(project_id, file.filename or "artifact", language, content, stored["path"], stored["sha256"], stored["size"])

@app.get("/projects/{project_id}/artifacts")
def get_artifacts(project_id: str) -> dict:
    if not fetch_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"artifacts": list_artifacts(project_id)}

@app.post("/jobs")
def create_job_endpoint(payload: JobCreate) -> dict:
    if not fetch_project(payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    artifact = fetch_artifact(payload.artifact_id)
    if not artifact or artifact["project_id"] != payload.project_id:
        raise HTTPException(status_code=404, detail="Artifact not found in project")
    try:
        get_engine(payload.engine)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unsupported engine: {payload.engine}")
    job = create_job(payload.project_id, payload.artifact_id, payload.engine, payload.max_attempts)
    queue_job(job["id"], {"engine": payload.engine, "attempt": 0})
    return fetch_job(job["id"])

@app.get("/jobs")
def get_jobs() -> dict:
    return {"jobs": list_jobs()}

@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/internal/jobs/{job_id}/payload")
def get_job_payload(job_id: str) -> dict:
    payload = job_payload(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Job not found")
    return payload

@app.post("/internal/jobs/{job_id}/running")
def mark_running(job_id: str) -> dict:
    if not fetch_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return update_job(job_id, "running", increment_attempt=True)

@app.post("/internal/jobs/{job_id}/complete")
def complete_job(job_id: str, payload: JobResult) -> dict:
    if not fetch_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    if payload.error:
        return update_job(job_id, "failed", error=payload.error)
    return update_job(job_id, "completed", result=payload.result or {})
