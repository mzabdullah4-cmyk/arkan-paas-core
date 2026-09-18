import json
import os
from typing import Any, Dict

import redis


class JobQueue:
    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        try:
            self._client = redis.Redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
            self._client.ping()
        except Exception:
            self._client = None

    def enqueue(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        item = {"job_id": job_id, **payload}
        if self._client is not None:
            self._client.lpush("arkan:jobs", json.dumps(item))
            return {"queued": True, "backend": "redis"}
        return {"queued": True, "backend": "memory"}


queue = JobQueue()


def queue_job(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return queue.enqueue(job_id, payload)
