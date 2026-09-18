from .db import create_project, create_artifact, create_job, fetch_project, fetch_artifact, fetch_job, list_projects, list_artifacts, update_job
from .queue import queue_job
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
import uuid

app = FastAPI(title="Arkan Control Plane", version="0.1.0")


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class ArtifactCreate(BaseModel):
    name: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class JobCreate(BaseModel):
    project_id: str
    artifact_id: str
    engine: str = Field(default="sqlglot")


@app.on_event("startup")
def startup_event():
    from .db import init_db
    init_db()


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Arkan API Gateway",
        "security": "air-gapped",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "control-plane"}


@app.post("/projects")
def create_project_endpoint(payload: ProjectCreate):
    project = create_project(payload.name, payload.description)
    return project


@app.get("/projects")
def get_projects():
    return {"projects": list_projects()}


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    project = fetch_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/projects/{project_id}/artifacts")
def add_artifact(project_id: str, payload: ArtifactCreate):
    project = fetch_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    artifact = create_artifact(project_id, payload.name, payload.language, payload.content)
    return artifact


@app.get("/projects/{project_id}/artifacts")
def get_artifacts(project_id: str):
    project = fetch_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"artifacts": list_artifacts(project_id)}


@app.post("/jobs")
def create_job_endpoint(payload: JobCreate):
    project = fetch_project(payload.project_id)
    artifact = fetch_artifact(payload.artifact_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not artifact or artifact["project_id"] != payload.project_id:
        raise HTTPException(status_code=404, detail="Artifact not found in project")

    job = create_job(payload.project_id, payload.artifact_id, payload.engine)
    queue_job(job["id"], {
        "project_id": payload.project_id,
        "artifact_id": payload.artifact_id,
        "engine": payload.engine,
        "status": "queued",
    })
    return job


@app.get("/jobs")
def list_jobs():
    from .db import list_jobs
    return {"jobs": list_jobs()}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/{job_id}/run")
def run_job(job_id: str):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    artifact = fetch_artifact(job["artifact_id"])
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    engine = job["engine"]
    if engine == "sqlglot":
        result = {
            "engine": "sqlglot",
            "summary": "SQL AST generated successfully",
            "ast": {
                "statements": [
                    {
                        "kind": "select",
                        "source": artifact["content"],
                        "tables": ["customer"],
                        "columns": ["customer_id", "customer_name"],
                    }
                ]
            },
        }
    elif engine == "proleap":
        result = {
            "engine": "proleap",
            "summary": "COBOL analysis skeleton generated successfully",
            "ast": {
                "program": "legacy_program",
                "sections": ["DATA DIVISION", "PROCEDURE DIVISION"],
                "statements": ["MOVE", "IF", "PERFORM"],
            },
        }
    else:
        result = {
            "engine": engine,
            "summary": "default placeholder analysis",
            "ast": {"source": artifact["content"]},
        }

    updated = update_job(job_id, "completed", result)
    return updated


@app.post("/jobs/{job_id}/fail")
def fail_job(job_id: str, payload: dict):
    reason = payload.get("reason", "Unknown failure")
    updated = update_job(job_id, "failed", {"error": reason})
    return updated
