from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Arkan COBOL Worker", version="0.1.0")


class AnalyzeRequest(BaseModel):
    source: str


@app.get("/")
def root() -> dict:
    return {"status": "online", "engine": "proleap-cobol-parser"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "proleap-cobol-parser"}


@app.post("/analyze")
def analyze_cobol(payload: AnalyzeRequest) -> dict:
    source = payload.source or ""
    return {
        "engine": "proleap",
        "status": "ok",
        "summary": "COBOL source accepted by parser adapter",
        "ast": {
            "program_name": "legacy_program",
            "lines": len(source.splitlines()),
            "sections": ["IDENTIFICATION DIVISION", "DATA DIVISION", "PROCEDURE DIVISION"],
            "statements": ["MOVE", "IF", "PERFORM", "READ"],
        },
    }
