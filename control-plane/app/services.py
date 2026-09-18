import hashlib
import os
import uuid
from typing import Any, Dict, List

ARTIFACT_ROOT = os.getenv("ARKAN_ARTIFACT_ROOT", "/data/artifacts")

ENGINE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sqlglot": {
        "url_env": "SQLGLOT_URL",
        "default_url": "http://sqlglot-worker:8000",
        "input_field": "sql",
        "languages": ["sql", "embedded-sql"],
    },
    "proleap": {
        "url_env": "PROLEAP_URL",
        "default_url": "http://cobol-worker:8000",
        "input_field": "source",
        "languages": ["cobol"],
    },
}


def get_engine(name: str) -> Dict[str, Any]:
    if name not in ENGINE_REGISTRY:
        raise KeyError(name)
    return ENGINE_REGISTRY[name]


def list_engines() -> List[Dict[str, Any]]:
    return [{"name": name, **config} for name, config in ENGINE_REGISTRY.items()]


def store_artifact(content: bytes) -> Dict[str, Any]:
    artifact_id = str(uuid.uuid4())
    digest = hashlib.sha256(content).hexdigest()
    directory = os.path.join(ARTIFACT_ROOT, artifact_id[:2])
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, artifact_id)
    with open(path, "wb") as artifact_file:
        artifact_file.write(content)
    return {"id": artifact_id, "path": path, "sha256": digest, "size": len(content)}
