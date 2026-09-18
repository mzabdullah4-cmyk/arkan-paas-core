import sqlglot
from fastapi import FastAPI

app = FastAPI(title="Arkan SQL AST Engine", version="1.0")

@app.get("/")
def read_root():
    return {"status": "ready", "parser": "SQLGlot", "mode": "AST Extraction"}
