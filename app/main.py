from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn

app = FastAPI()

@app.get("/")
def root_endpoint():
    """A quick test endpoint at GET /"""
    return {"message": "Hello from the Automation Agent"}

@app.get("/read")
def read_file(path: str):
    """
    Placeholder for GET /read?path=...
    We'll implement actual file reading soon.
    """
    # Just returning a placeholder response
    return PlainTextResponse(f"Requesting file at path: {path}")

@app.post("/run")
def run_task(task: str):
    """
    Placeholder for POST /run?task=...
    We'll implement the actual logic soon.
    """
    return JSONResponse({"message": f"Received task: {task}"})