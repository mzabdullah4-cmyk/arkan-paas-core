import json
import os
from typing import Any, Dict

import redis


class JobQueue:
    def __init__(self):
        self.client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

    def enqueue(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        item = {"job_id": job_id, **payload}
        self.client.lpush("arkan:jobs", json.dumps(item))
        return {"queued": True, "backend": "redis"}


queue = JobQueue()


def queue_job(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return queue.enqueue(job_id, payload)
