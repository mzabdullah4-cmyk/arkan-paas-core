from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Arkan SQLGlot Worker", version="0.1.0")


class AnalyzeRequest(BaseModel):
    sql: str


@app.get("/")
def root():
    return {"status": "online", "engine": "sqlglot-worker"}


@app.post("/analyze")
def analyze_sql(payload: AnalyzeRequest):
    try:
        from sqlglot import parse_one
        parsed = parse_one(payload.sql)
        return {
            "engine": "sqlglot",
            "status": "ok",
            "summary": "SQL parsed successfully",
            "ast": {
                "sql": payload.sql,
                "expression_type": type(parsed).__name__,
                "dump": parsed.sql(pretty=True),
            },
        }
    except Exception as exc:  # pragma: no cover
        return {
            "engine": "sqlglot",
            "status": "error",
            "summary": "SQL parsing failed",
            "error": str(exc),
        }
