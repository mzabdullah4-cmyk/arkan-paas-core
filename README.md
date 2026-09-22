# Arkan PaaS Core

Arkan is a console-style application platform for legacy modernization. The portal presents projects, jobs, and registered analysis tools through one platform API; isolated adapters perform specialized work.

## Current vertical flow

`Portal → Control Plane API → Redis queue → Job Runner → registered engine adapter → normalized result → job status`

The current catalog includes SQLGlot and a ProLeap COBOL adapter boundary. Additional OSS engines must be added as isolated adapters after license review and Trivy/SBOM scanning.

## Run locally

```bash
docker compose -f docker-compose.prod.yml up --build
```

Open `http://localhost:8080`. The portal proxies `/api/*` to the control plane. The API exposes `/engines`, `/projects`, `/jobs`, and artifact upload endpoints.

## IBM VM baseline

See `deploy/IBM-VM.md`. Keep only the portal/reverse proxy public; Redis, the control plane, job runner, and workers should remain on the private Compose network. Mount `/opt/arkan/data` and `/opt/arkan/artifacts` for persistence and back them up before upgrades.

Before deployment, scan every built image with Trivy, generate an SBOM, review licenses separately, configure TLS, and add authentication/service authorization. This repository is a development/deployment baseline, not a production security certification.
