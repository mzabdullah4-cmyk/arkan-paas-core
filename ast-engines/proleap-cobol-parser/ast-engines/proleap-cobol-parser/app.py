from fastapi import FastAPI

app = FastAPI(title="Arkan COBOL AST Engine", version="1.0")

@app.get("/")
def read_root():
    return {"status": "ready", "parser": "ProLeap COBOL Parser (MIT)", "mode": "AST Extraction"}
