import os
import sys
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from dateutil import parser as date_parser
import json
import glob

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

#A1
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

#A2
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

#A3        
def count_wednesdays_in_dates():
    input_path = "data/dates.txt"
    output_path = "data/dates-wednesdays.txt"

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    wednesday_count = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue 
            try:
                dt = date_parser.parse(line)
                if dt.weekday() == 2:
                    wednesday_count += 1
            except Exception as e:
                print(f"Warning: Could not parse date '{line}': {e}")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(str(wednesday_count))

    print(f"Found {wednesday_count} Wednesdays. Wrote result to {output_path}")

#A4
def sort_contacts():
    """
    Reads data/contacts.json (a list of objects),
    sorts by last_name then first_name,
    writes the result to data/contacts-sorted.json.
    """
    input_path = "data/contacts.json"
    output_path = "data/contacts-sorted.json"

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        contacts = json.load(f) 

    sorted_contacts = sorted(contacts, key=lambda c: (c["last_name"], c["first_name"]))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_contacts, f, indent=2)

    print(f"Sorted contacts written to {output_path}.")

#A5
def get_recent_logs():
    """
    Finds the 10 most recently modified .log files in data/logs/ (descending order).
    Extracts the first line of each, writes them to data/logs-recent.txt.
    """
    logs_dir = "data/logs"
    output_file = "data/logs-recent.txt"

    if not os.path.isdir(logs_dir):
        raise FileNotFoundError(f"The directory '{logs_dir}' does not exist.")

    pattern = os.path.join(logs_dir, "*.log")
    log_files = glob.glob(pattern)
    if not log_files:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("")
        return 

    log_files_sorted = sorted(log_files, key=os.path.getmtime, reverse=True)

    top_10 = log_files_sorted[:10]

    lines = []
    for log_path in top_10:
        with open(log_path, "r", encoding="utf-8") as f:
            first_line = f.readline().rstrip("\n")
            lines.append(first_line)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))

    print(f"Wrote first lines of 10 most recent logs to {output_file}")

#A6
def build_docs_index():
    """
    - Finds all .md files in data/docs/
    - Extracts the first line starting with '# ' as the title
    - Saves a JSON mapping { "some-file.md": "Title", "folder/another-file.md": "Another Title" }
      to data/docs/index.json
    """
    docs_dir = "data/docs"
    output_path = os.path.join(docs_dir, "index.json")

    # Dictionary for storing filename->title
    index_map = {}

    # Walk through docs_dir recursively
    for root, dirs, files in os.walk(docs_dir):
        for fname in files:
            # Check if this is a .md file
            if fname.lower().endswith(".md"):
                full_path = os.path.join(root, fname)

                # Compute the relative path, e.g. "subfolder/file.md"
                rel_path = os.path.relpath(full_path, docs_dir).replace("\\", "/")

                # Read the file and find the first line that starts with '# '
                title = ""
                with open(full_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("# "):
                            title = line[2:].strip()  # remove '# ' and strip whitespace
                            break

                # Store the result in our index map
                index_map[rel_path] = title

    # Write the index map to data/docs/index.json
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(index_map, out, indent=2)

    print(f"Documentation index written to {output_path}")

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

    requested_path = os.path.abspath(path)

    data_dir = os.path.abspath("data")

    if not requested_path.startswith(data_dir):
        raise HTTPException(status_code=404, detail="File not found or not accessible.")

    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=404, detail="File not found.")

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
    
    if "A3" in task.lower() or "wednesday" in task.lower() or "dates-wednesdays.txt" in task.lower():
        try:
            count_wednesdays_in_dates()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A3 completed: dates-wednesdays.txt has been updated"}
    
    if "A4" in task.upper() or "contacts-sorted" in task.lower():
        try:
            sort_contacts()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return {"message": "A4 completed: contacts-sorted.json has been created"}
    
    if "A5" in task.upper() or "logs-recent" in task.lower():
        try:
            get_recent_logs()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return {"message": "A5 completed: logs-recent.txt has been written."}
    
    if "A6" in task.upper() or "index.json" in task.lower() or "docs" in task.lower():
        try:
            build_docs_index()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A6 completed: docs/index.json has been created"}

    # Default response
    return JSONResponse({"message": f"Received task: {task}"})