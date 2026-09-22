import os
import redis
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import Optional
from . import db

app = FastAPI(title="Arkan Control Plane", version="0.5.0")
ENGINES = {
 "sqlglot": {"version":"latest","description":"SQL AST analysis","languages":["sql","embedded-sql"],"license":"MIT"},
 "proleap": {"version":"adapter-scaffold","description":"COBOL analysis adapter boundary","languages":["cobol"],"license":"review-required"},
}

class ProjectCreate(BaseModel): name: str = Field(min_length=1, max_length=200); description: Optional[str] = Field(default=None, max_length=2000)
class JobCreate(BaseModel): project_id: str; artifact_id: str; engine: str; max_attempts: int = Field(default=3, ge=1, le=10)
class Result(BaseModel): result: Optional[dict] = None; error: Optional[str] = None

def authorize(token: Optional[str], internal=False):
    expected = os.getenv("ARKAN_INTERNAL_TOKEN" if internal else "ARKAN_API_TOKEN")
    if expected and token != f"Bearer {expected}": raise HTTPException(401, "Unauthorized")

@app.on_event("startup")
def startup(): db.init_db()
@app.get("/")
def root(): return {"status":"online","service":"Arkan API Gateway","version":"0.5.0"}
@app.get("/health")
def health(): return {"status":"ok","service":"control-plane"}
@app.get("/engines")
def engines(): return {"engines":[{"name":n,**v,"timeout_seconds":300} for n,v in ENGINES.items()]}
@app.post("/projects")
def create_project(payload: ProjectCreate, authorization: Optional[str]=Header(None)):
    authorize(authorization); return db.create_project(payload.name,payload.description)
@app.get("/projects")
def list_projects(authorization: Optional[str]=Header(None)):
    authorize(authorization); return {"projects":db.projects()}
@app.post("/projects/{project_id}/artifacts/upload")
async def upload(project_id: str, language: str, file: UploadFile=File(...), authorization: Optional[str]=Header(None)):
    authorize(authorization)
    if not db.project(project_id): raise HTTPException(404,"Project not found")
    raw = await file.read()
    if not raw or len(raw) > int(os.getenv("ARKAN_MAX_ARTIFACT_BYTES", str(50*1024*1024))): raise HTTPException(400,"Invalid or oversized artifact")
    return db.create_artifact(project_id, file.filename or "artifact", language, raw.decode("utf-8",errors="replace"))
@app.get("/projects/{project_id}/artifacts")
def list_artifacts(project_id: str, authorization: Optional[str]=Header(None)):
    authorize(authorization); return {"artifacts":db.artifacts(project_id)}
@app.post("/jobs")
def create_job(payload: JobCreate, authorization: Optional[str]=Header(None)):
    authorize(authorization)
    if payload.engine.lower() not in ENGINES: raise HTTPException(400,"Unsupported engine")
    art=db.artifact(payload.artifact_id)
    if not art or art["project_id"] != payload.project_id: raise HTTPException(404,"Artifact not found in project")
    job=db.create_job(payload.project_id,payload.artifact_id,payload.engine,payload.max_attempts)
    redis.Redis.from_url(os.getenv("REDIS_URL","redis://redis-broker:6379/0")).lpush("arkan:jobs", __import__("json").dumps({"job_id":job["id"],"attempt":0}))
    return job
@app.get("/jobs")
def list_jobs(authorization: Optional[str]=Header(None)):
    authorize(authorization); return {"jobs":db.jobs()}
@app.get("/jobs/{job_id}")
def get_job(job_id: str, authorization: Optional[str]=Header(None)):
    authorize(authorization); value=db.job(job_id)
    if not value: raise HTTPException(404,"Job not found")
    return value
@app.get("/internal/jobs/{job_id}/payload")
def internal_payload(job_id: str, authorization: Optional[str]=Header(None)):
    authorize(authorization,True); value=db.payload(job_id)
    if not value: raise HTTPException(404,"Job not found")
    return value
@app.post("/internal/jobs/{job_id}/running")
def running(job_id: str, authorization: Optional[str]=Header(None)):
    authorize(authorization,True); return db.update_job(job_id,"running",increment=True)
@app.post("/internal/jobs/{job_id}/complete")
def complete(job_id: str, result: Result, authorization: Optional[str]=Header(None)):
    authorize(authorization,True); return db.update_job(job_id,"failed" if result.error else "completed",result.result,error=result.error)
