import os
import sys
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn

app = FastAPI()

def install_uv_if_needed():
    """
    Check if 'uv' is installed; if not, install it via pip.
    """
    try:
        # 'pip show uv' returns 0 if installed
        subprocess.run(
            [sys.executable, "-m", "pip", "show", "uv"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("Package 'uv' is already installed.")
    except subprocess.CalledProcessError:
        print("Package 'uv' not found. Installing now...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "uv"],
            check=True
        )

def run_datagen(user_email: str):
    """
    Download and run datagen.py with the user_email as the only argument.
    """
    # 1. (Optional) install 'uv'
    install_uv_if_needed()

    # 2. Download the script
    url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    # 3. Write the script to a temporary location
    script_path = "./temp/datagen.py"
    with open(script_path, "wb") as f:
        f.write(response.content)

    # 4. Execute datagen.py with the user's email
    print(f"Running datagen.py with email: {user_email}")
    subprocess.run(
        [sys.executable, script_path, user_email],
        check=True
    )
    
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
    return PlainTextResponse(f"Requesting file at path: {path}")

@app.post("/run")
def run_task(task: str, email: str = ""):
    """
    - If the task references A1 or 'datagen', run the A1 procedure.
    - Otherwise, just echo for now.
    """
    if "A1" in task or "datagen" in task:
        if not email:
            raise HTTPException(status_code=400, detail="Email is required to run datagen.py")

        try:
            run_datagen(email)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return JSONResponse({"message": f"A1 completed successfully for {email}"})

    return JSONResponse({"message": f"Received task: {task}"})