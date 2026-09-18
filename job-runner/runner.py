import json
import os
import time
from typing import Any, Dict

import redis
import requests

from registry import ENGINE_REGISTRY

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://control-plane:8000")
MAX_RETRY_DELAY = int(os.getenv("MAX_RETRY_DELAY", "30"))


def callback(job_id: str, path: str, payload: Dict[str, Any] | None = None) -> None:
    response = requests.post(f"{CONTROL_PLANE_URL}/internal/jobs/{job_id}/{path}", json=payload or {}, timeout=30)
    response.raise_for_status()


def process(item: Dict[str, Any], client: redis.Redis) -> None:
    job_id = item["job_id"]
    try:
        callback(job_id, "running")
        payload = requests.get(f"{CONTROL_PLANE_URL}/internal/jobs/{job_id}/payload", timeout=30).json()
        engine = payload["engine"]
        config = ENGINE_REGISTRY.get(engine)
        if not config:
            raise ValueError(f"Unsupported engine: {engine}")
        body = {config["input_field"]: payload["content"]}
        response = requests.post(config["url"], json=body, timeout=config.get("timeout", 300))
        response.raise_for_status()
        analysis = response.json()
        if analysis.get("status") == "error":
            raise ValueError(analysis.get("error", "Engine analysis failed"))
        normalized = {
            "schema_version": "1.0",
            "job_id": job_id,
            "engine": engine,
            "source": {"artifact_id": payload["artifact_id"], "name": payload["name"], "language": payload["language"]},
            "entities": analysis.get("ast", {}).get("tables", []),
            "dependencies": analysis.get("dependencies", []),
            "findings": analysis.get("findings", []),
            "raw": analysis,
        }
        callback(job_id, "complete", {"result": normalized})
    except Exception as exc:
        attempt = int(item.get("attempt", 0)) + 1
        max_attempts = int(payload.get("max_attempts", 3)) if "payload" in locals() else 3
        if attempt < max_attempts:
            time.sleep(min(2 ** attempt, MAX_RETRY_DELAY))
            client.lpush("arkan:jobs", json.dumps({**item, "attempt": attempt}))
            return
        client.lpush("arkan:jobs:dead", json.dumps({**item, "attempt": attempt, "error": str(exc)}))
        callback(job_id, "complete", {"error": f"permanent failure after {attempt} attempts: {exc}"})


def main() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    while True:
        _, raw = client.brpop("arkan:jobs", timeout=5) or (None, None)
        if raw:
            process(json.loads(raw), client)


if __name__ == "__main__":
    main()
