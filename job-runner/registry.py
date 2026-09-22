import os

ENGINE_REGISTRY = {
    "sqlglot": {
        "input_field": "sql",
        "url": os.getenv("SQLGLOT_URL", "http://sqlglot-worker:8000/analyze"),
        "timeout": 300,
        "status": "available",
        "execution_supported": True,
    },
    "proleap": {
        "input_field": "source",
        "url": os.getenv("PROLEAP_URL", "http://cobol-worker:8000/analyze"),
        "timeout": 300,
        "status": "scaffold",
        "execution_supported": True,
    },
    "pgloader": {
        "input_field": "source",
        "url": os.getenv("PGLOADER_URL", "http://pgloader-worker:8000/analyze"),
        "timeout": 1800,
        "status": "planned",
        "execution_supported": False,
    },
    "fortran-src": {
        "input_field": "source",
        "url": os.getenv("FORTRAN_SRC_URL", "http://fortran-src-worker:8000/analyze"),
        "timeout": 600,
        "status": "planned",
        "execution_supported": False,
    },
    "clang-tidy": {
        "input_field": "source",
        "url": os.getenv("CLANG_TIDY_URL", "http://clang-tidy-worker:8000/analyze"),
        "timeout": 600,
        "status": "planned",
        "execution_supported": False,
    },
    "openhands": {
        "input_field": "source",
        "url": os.getenv("OPENHANDS_URL", "http://openhands-worker:8000/analyze"),
        "timeout": 1800,
        "status": "planned",
        "execution_supported": False,
    },
}
