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

def format_markdown_in_place():
    """
    Run `prettier@3.4.2` to format `data/format.md` in-place.
    """
    try:
        # Example using npx:
        subprocess.run(
            ["npx", "prettier@3.4.2", "--write", "data/format.md"],
            check=True
        )
    except FileNotFoundError:
        # This likely means npx or node is not installed / not in PATH
        raise HTTPException(
            status_code=500,
            detail="npx not found. Please install Node.js and npm to run Prettier."
        )
    except subprocess.CalledProcessError as e:
        # Prettier command failed
        raise HTTPException(
            status_code=500,
            detail=f"Prettier formatting failed: {e}"
        )
        
@app.get("/")
def root_endpoint():
    """A quick test endpoint at GET /"""
    return {"message": "Hello from the Automation Agent"}

@app.get("/read")
def read_file(path: str):
    """
    GET /read?path=<file path>
    - Ensures the file is inside the 'data/' folder
    - Returns its content as plain text
    - If the file doesn't exist or is outside 'data/', returns 404
    """

    # 1. Convert relative path to an absolute path
    requested_path = os.path.abspath(path)

    # 2. Convert the data directory to an absolute path
    data_dir = os.path.abspath("data")

    # 3. Check if requested_path is within the data folder
    if not requested_path.startswith(data_dir):
        raise HTTPException(status_code=404, detail="File not found or not accessible.")

    # 4. Check if the file exists
    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=404, detail="File not found.")

    # 5. Read and return the content
    with open(requested_path, "r", encoding="utf-8") as f:
        content = f.read()

    return PlainTextResponse(content, media_type="text/plain")

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

    if "A2" in task.lower() or "format.md" in task.lower():
        # Call the function to do the formatting
        format_markdown_in_place()
        return {"message": "A2 completed: format.md has been prettified"}

    return JSONResponse({"message": f"Received task: {task}"})