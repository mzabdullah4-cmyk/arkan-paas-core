import hashlib
import os
import uuid
from typing import Any, Dict, List

ARTIFACT_ROOT = os.getenv("ARKAN_ARTIFACT_ROOT", "/data/artifacts")

ENGINE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sqlglot": {
        "version": "latest",
        "description": "SQL parsing, AST generation, and dialect analysis.",
        "url_env": "SQLGLOT_URL",
        "default_url": "http://sqlglot-worker:8000",
        "input_field": "sql",
        "languages": ["sql", "embedded-sql"],
        "license": "MIT",
        "timeout_seconds": 300,
        "status": "available",
        "execution_supported": True,
    },
    "proleap": {
        "version": "adapter-scaffold",
        "description": "COBOL analysis adapter boundary for ProLeap.",
        "url_env": "PROLEAP_URL",
        "default_url": "http://cobol-worker:8000",
        "input_field": "source",
        "languages": ["cobol"],
        "license": "review-required",
        "timeout_seconds": 300,
        "status": "scaffold",
        "execution_supported": True,
    },
    "pgloader": {
        "version": "adapter-planned",
        "description": "Database migration and schema/data loading workflows.",
        "url_env": "PGLOADER_URL",
        "default_url": "http://pgloader-worker:8000",
        "input_field": "source",
        "languages": ["sql", "database-config"],
        "license": "PostgreSQL",
        "timeout_seconds": 1800,
        "status": "planned",
        "execution_supported": False,
    },
    "fortran-src": {
        "version": "adapter-planned",
        "description": "Fortran source extraction and structural analysis.",
        "url_env": "FORTRAN_SRC_URL",
        "default_url": "http://fortran-src-worker:8000",
        "input_field": "source",
        "languages": ["fortran"],
        "license": "review-required",
        "timeout_seconds": 600,
        "status": "planned",
        "execution_supported": False,
    },
    "clang-tidy": {
        "version": "adapter-planned",
        "description": "C and C++ static analysis and linting.",
        "url_env": "CLANG_TIDY_URL",
        "default_url": "http://clang-tidy-worker:8000",
        "input_field": "source",
        "languages": ["c", "c++"],
        "license": "Apache-2.0",
        "timeout_seconds": 600,
        "status": "planned",
        "execution_supported": False,
    },
    "openhands": {
        "version": "adapter-planned",
        "description": "AI-assisted code understanding, refactoring, and modernization.",
        "url_env": "OPENHANDS_URL",
        "default_url": "http://openhands-worker:8000",
        "input_field": "source",
        "languages": ["multi-language"],
        "license": "review-required",
        "timeout_seconds": 1800,
        "status": "planned",
        "execution_supported": False,
    },
}


def get_engine(name: str) -> Dict[str, Any]:
    key = name.strip().lower()
    if key not in ENGINE_REGISTRY:
        raise KeyError(name)
    return {"name": key, **ENGINE_REGISTRY[key]}


def list_engines() -> List[Dict[str, Any]]:
    return [get_engine(name) for name in ENGINE_REGISTRY]


def store_artifact(content: bytes) -> Dict[str, Any]:
    artifact_id = str(uuid.uuid4())
    digest = hashlib.sha256(content).hexdigest()
    directory = os.path.join(ARTIFACT_ROOT, artifact_id[:2])
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, artifact_id)
    with open(path, "wb") as artifact_file:
        artifact_file.write(content)
    return {"id": artifact_id, "path": path, "sha256": digest, "size": len(content)}
