import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Arkan SQLGlot Worker", version="0.1.0")

class AnalyzeRequest(BaseModel):
    sql: str

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "sqlglot-worker"}

@app.post("/analyze")
def analyze_sql(payload: AnalyzeRequest) -> dict:
    try:
        from sqlglot import parse_one
        parsed = parse_one(payload.sql)
        tables = [table.sql() for table in parsed.find_all(__import__("sqlglot").exp.Table)]
        return {"engine": "sqlglot", "status": "ok", "summary": "SQL parsed successfully", "ast": {"sql": payload.sql, "expression_type": type(parsed).__name__, "dump": parsed.sql(pretty=True), "tables": tables}}
    except Exception as exc:
        return {"engine": "sqlglot", "status": "error", "error": str(exc)}
