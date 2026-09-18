import os

ENGINE_REGISTRY = {
    "sqlglot": {"input_field": "sql", "url": os.getenv("SQLGLOT_URL", "http://sqlglot-worker:8000/analyze"), "timeout": 300},
    "proleap": {"input_field": "source", "url": os.getenv("PROLEAP_URL", "http://cobol-worker:8000/analyze"), "timeout": 300},
}
