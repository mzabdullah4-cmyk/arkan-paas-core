# Arkan PaaS Core

This repo is a minimal but working MVP for a job-driven legacy modernization PaaS.

## What is included

- FastAPI control plane
- SQLite-backed project, artifact, and job storage
- Redis-backed job queue with service callback flow
- Job runner that polls Redis and dispatches work to engine adapters
- SQLGlot worker scaffold
- COBOL parser adapter scaffold
- Docker Compose orchestration

## Runtime flow

1. Create project
2. Upload artifact
3. Queue a job
4. job-runner consumes the Redis queue
5. Engine adapter executes analysis
6. Control plane records completed/failed status

## Run

```bash
docker compose up --build
```

Services:
- Control plane: http://localhost:8000
- SQLGlot worker: http://localhost:8001
- COBOL worker: http://localhost:8002

## Example usage

```bash
PROJECT=$(curl -s http://localhost:8000/projects -X POST -H 'Content-Type: application/json' -d '{"name":"Legacy Billing"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ARTIFACT=$(curl -s http://localhost:8000/projects/$PROJECT/artifacts -X POST -H 'Content-Type: application/json' -d '{"name":"billing.sql","language":"sql","content":"SELECT customer_id, customer_name FROM customer;"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -s http://localhost:8000/jobs -X POST -H 'Content-Type: application/json' -d "{\"project_id\":\"$PROJECT\",\"artifact_id\":\"$ARTIFACT\",\"engine\":\"sqlglot\"}"
```

Poll status:

```bash
curl http://localhost:8000/jobs/<job_id>
```

## Security note

This repo is intended for local orchestration and testing. The Dockerfiles run as a non-root user, and the stack avoids exposing database credentials in source. For production, add service auth, private networking, secrets management, and stricter sandboxing around the worker environment.

## Licensing note

This repo does not include the full complement of engines from the full vision architecture. It currently includes SQLGlot and a COBOL adapter scaffold. FORTRAN, LLVM/clang-tidy, Cobrix, pgloader, Graphviz, and the actual ProLeap parser runtime remain separate integration steps with their own license review.
