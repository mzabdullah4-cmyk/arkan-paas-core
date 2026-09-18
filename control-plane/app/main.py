from fastapi import FastAPI

app = FastAPI(title="Arkan Control Plane", version="1.0.0")

@app.get("/")
def read_root():
    return {"status": "online", "service": "Arkan API Gateway", "security": "air-gapped"}
