# Arkan PaaS Core

MVP pipeline: create project → store source artifact → enqueue job → run an isolated engine → persist normalized result.

## Run

```bash
docker compose up --build
```

Services:
- Control plane: http://localhost:8000
- SQLGlot worker: http://localhost:8001
- COBOL worker adapter: http://localhost:8002

Create a project, artifact, and job:

```bash
PROJECT=$(curl -s localhost:8000/projects -X POST -H 'Content-Type: application/json' -d '{"name":"Legacy Billing"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
ARTIFACT=$(curl -s localhost:8000/projects/$PROJECT/artifacts -X POST -H 'Content-Type: application/json' -d '{"name":"billing.sql","language":"sql","content":"SELECT customer_id FROM customer;"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl localhost:8000/jobs -X POST -H 'Content-Type: application/json' -d "{\"project_id\":\"$PROJECT\",\"artifact_id\":\"$ARTIFACT\",\"engine\":\"sqlglot\"}"
```

The job is processed asynchronously by `job-runner`; poll `GET /jobs/{job_id}` until `completed` or `failed`.

## Important licensing note

This repository does **not** yet contain every OSS engine from the target architecture. It currently contains a SQLGlot worker and a COBOL parser adapter scaffold. FORTRAN, LLVM/clang-tidy, Cobrix, pgloader, Graphviz, and the actual ProLeap Java parser runtime still need separate adapters and license review before distribution.
