import json
import os
import time
from typing import Any, Dict

import redis
import requests

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://control-plane:8000")
ENGINE_URLS = {
    "sqlglot": os.getenv("SQLGLOT_URL", "http://sqlglot-worker:8000"),
    "proleap": os.getenv("PROLEAP_URL", "http://cobol-worker:8000"),
}


def callback(job_id: str, path: str, payload: Dict[str, Any] | None = None) -> None:
    response = requests.post(f"{CONTROL_PLANE_URL}/internal/jobs/{job_id}/{path}", json=payload or {}, timeout=30)
    response.raise_for_status()


def process(item: Dict[str, Any]) -> None:
    job_id = item["job_id"]
    try:
        callback(job_id, "running")
        payload_response = requests.get(f"{CONTROL_PLANE_URL}/internal/jobs/{job_id}/payload", timeout=30)
        payload_response.raise_for_status()
        payload = payload_response.json()

        engine = payload["engine"]
        engine_url = ENGINE_URLS.get(engine)
        if not engine_url:
            raise ValueError(f"Unsupported engine: {engine}")

        request_body = {"sql": payload["content"]} if engine == "sqlglot" else {"source": payload["content"]}
        analysis_response = requests.post(f"{engine_url}/analyze", json=request_body, timeout=300)
        analysis_response.raise_for_status()
        analysis = analysis_response.json()

        if analysis.get("status") == "error":
            raise ValueError(analysis.get("error", "Engine analysis failed"))

        callback(
            job_id,
            "complete",
            {
                "result": {
                    "job_id": job_id,
                    "artifact_id": payload["artifact_id"],
                    "engine": engine,
                    "analysis": analysis,
                }
            },
        )
    except Exception as exc:
        callback(job_id, "complete", {"error": str(exc)})


def main() -> None:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    while True:
        _, raw = client.brpop("arkan:jobs", timeout=5) or (None, None)
        if raw:
            process(json.loads(raw))
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
