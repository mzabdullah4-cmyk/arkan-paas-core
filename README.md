# Arkan PaaS Core

This repo is a minimal MVP for an AI-assisted legacy modernization platform.

## What is built

- FastAPI control plane
- SQLite-backed project, artifact, and job storage
- Redis-ready job queue with in-memory fallback
- SQLGlot worker scaffold
- COBOL parser worker scaffold
- Docker Compose orchestration

## Current flow

1. Create a project
2. Add source artifacts
3. Create a modernization job
4. Run the job to produce a normalized analysis result

## Quick start

```bash
docker compose up --build
```

Then use the API at:

- http://localhost:8000
- http://localhost:8001 for sqlglot-worker
- http://localhost:8002 for cobol-worker

## Example endpoints

```bash
curl http://localhost:8000/projects -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Legacy Billing"}'

curl http://localhost:8000/projects/{project_id}/artifacts -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"billing.sql","language":"sql","content":"SELECT customer_id, customer_name FROM customer;"}'

curl http://localhost:8000/jobs -X POST \
  -H "Content-Type: application/json" \
  -d '{"project_id":"{project_id}","artifact_id":"{artifact_id}","engine":"sqlglot"}'

curl http://localhost:8000/jobs/{job_id}/run
```

## Next milestones

- project upload with object storage
- real job workers and async consumption
- dependency graph extraction
- AI-driven modernization planning
- build/test verification pipeline
