from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from .db import (
    create_artifact, create_job, create_project, fetch_artifact, fetch_job,
    fetch_project, init_db, job_payload, list_artifacts, list_jobs,
    list_projects, update_job,
)
from .queue import queue_job

app = FastAPI(title="Arkan Control Plane", version="0.2.0")


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


class JobResult(BaseModel):
    result: Optional[dict] = None
    error: Optional[str] = None


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"status": "online", "service": "Arkan API Gateway", "version": "0.2.0"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "control-plane"}


@app.post("/projects")
def create_project_endpoint(payload: ProjectCreate):
    return create_project(payload.name, payload.description)


@app.get("/projects")
def get_projects():
    return {"projects": list_projects()}


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    project = fetch_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.post("/projects/{project_id}/artifacts")
def add_artifact(project_id: str, payload: ArtifactCreate):
    if not fetch_project(project_id):
        raise HTTPException(404, "Project not found")
    return create_artifact(project_id, payload.name, payload.language, payload.content)


@app.get("/projects/{project_id}/artifacts")
def get_artifacts(project_id: str):
    if not fetch_project(project_id):
        raise HTTPException(404, "Project not found")
    return {"artifacts": list_artifacts(project_id)}


@app.post("/jobs")
def create_job_endpoint(payload: JobCreate):
    if not fetch_project(payload.project_id):
        raise HTTPException(404, "Project not found")
    artifact = fetch_artifact(payload.artifact_id)
    if not artifact or artifact["project_id"] != payload.project_id:
        raise HTTPException(404, "Artifact not found in project")
    job = create_job(payload.project_id, payload.artifact_id, payload.engine)
    queue_job(job["id"], {"engine": payload.engine})
    return fetch_job(job["id"])


@app.get("/jobs")
def get_jobs():
    return {"jobs": list_jobs()}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# Internal worker endpoints. In production, protect these with service authentication.
@app.get("/internal/jobs/{job_id}/payload")
def get_job_payload(job_id: str):
    payload = job_payload(job_id)
    if not payload:
        raise HTTPException(404, "Job not found")
    return payload


@app.post("/internal/jobs/{job_id}/running")
def mark_running(job_id: str):
    if not fetch_job(job_id):
        raise HTTPException(404, "Job not found")
    return update_job(job_id, "running")


@app.post("/internal/jobs/{job_id}/complete")
def complete_job(job_id: str, payload: JobResult):
    if not fetch_job(job_id):
        raise HTTPException(404, "Job not found")
    if payload.error:
        return update_job(job_id, "failed", error=payload.error)
    return update_job(job_id, "completed", result=payload.result or {})
