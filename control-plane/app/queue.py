import os
import json
from typing import Any, Dict

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class JobQueue:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._fallback = []
        self._client = None
        if redis is not None:
            try:
                self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def enqueue(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        item = {"job_id": job_id, **payload}
        if self._client is not None:
            self._client.lpush("arkan:jobs", json.dumps(item))
            return {"queued": True, "backend": "redis"}
        self._fallback.append(item)
        return {"queued": True, "backend": "memory"}


queue = JobQueue()


def queue_job(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return queue.enqueue(job_id, payload)
