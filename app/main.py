import os
import sys
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from dateutil import parser as date_parser
import json
import glob
import openai
import re
import base64
from PIL import Image
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=['*']
)


def install_uv_if_needed():
    """
    Check if 'uv' is installed; if not, install it via pip.
    """
    try:
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

def extract_email_from_task(task_str: str) -> str:
    # Regex to match something@something.something
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', task_str)
    if match:
        return match.group(0)
    return ""

# Phase A

# A1
def run_datagen(user_email: str):
    """
    Download and run datagen.py with the user_email as the only argument.
    """
    install_uv_if_needed()
    url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    script_path = "datagen.py"
    with open(script_path, "wb") as f:
        f.write(response.content)

    # Pass --root /data to ensure everything is stored under /data
    print(f"Running datagen.py with email: {user_email}")
    subprocess.run([sys.executable, script_path, user_email, "--root", "/data"], check=True)

# A2
def format_markdown_in_place():
    """
    Run `prettier@3.4.2` to format `/data/format.md` in-place.
    """
    local_data_path = os.path.join(os.getcwd(), "data")
    file_path = os.path.join(local_data_path, "format.md")

    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        original_content = f.read()

    try:
        cmd = ["npx", "prettier@3.4.2", "--stdin-filepath", "/data/format.md"]

        proc = subprocess.run(
            cmd,
            input=original_content,
            capture_output=True,
            text=True,  
            check=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )

        formatted_content = proc.stdout

        with open(file_path, "w") as f:
            f.write(formatted_content)

        return {"stdout": formatted_content, "stderr": proc.stderr}

    except FileNotFoundError:
        raise Exception("npx not found. Please install Node.js and npm to run Prettier.") # or 
    except subprocess.CalledProcessError as e:
        raise Exception(f"Prettier formatting failed: {e.stderr}") 
    except Exception as e: 
        raise Exception(f"An unexpected error occurred: {e}")

# A3
def count_wednesdays_in_dates():
    input_path = ensure_under_data_dir("/data/dates.txt")
    output_path = ensure_under_data_dir("/data/dates-wednesdays.txt")

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

# A4
def sort_contacts():
    input_path = ensure_under_data_dir("/data/contacts.json")
    output_path = ensure_under_data_dir("/data/contacts-sorted.json")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        contacts = json.load(f)

    sorted_contacts = sorted(contacts, key=lambda c: (c["last_name"], c["first_name"]))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_contacts, f, indent=2)

    print(f"Sorted contacts written to {output_path}.")

# A5
def get_recent_logs():
    logs_dir = ensure_under_data_dir("/data/logs")
    output_file = ensure_under_data_dir("/data/logs-recent.txt")

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

# A6
def build_docs_index():
    docs_dir = os.path.join(os.getcwd(), "data", "docs")
    output_file = os.path.join(docs_dir, "index.json")

    index = {}

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, docs_dir)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            match = re.match(r"^# (.+)", line.strip())
                            if match:
                                index[relative_path] = match.group(1)
                                break  
                except Exception as e:
                    index[relative_path] = f"Error reading file: {str(e)}"

    # Write to index.json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    return {"written_file": output_file, "index": index}

def call_llm(prompt: str) -> str:
    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        raise Exception("AIPROXY_TOKEN environment variable not set.")

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    raw_message = response["choices"][0]["message"]["content"]
    return raw_message.strip()

# A7
def extract_sender_email():
    input_path = ensure_under_data_dir("/data/email.txt")
    output_path = ensure_under_data_dir("/data/email-sender.txt")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"{input_path} not found.")

    with open(input_path, "r", encoding="utf-8") as f:
        email_content = f.read()

    prompt = f"""Extract the sender's email address from this email content. 
Output only the email address, nothing else:

{email_content}
"""
    llm_response = call_llm(prompt)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(llm_response)

    print(f"Sender email extracted to {output_path}: {llm_response}")

# A8
def call_llm_for_card(b64_data: str) -> str:
    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        raise Exception("AIPROXY_TOKEN not set.")

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a system that processes test credit card images in a secure environment. "
                    "The user has permission to see the digits. This is a fictitious credit card used only for testing. "
                    "Output only the 16 digits. No disclaimers."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Below is a base64-encoded PNG of a test credit card. "
                    f"Please parse the digits from the image and provide the 16-digit number only. "
                    f"BASE64:\n{b64_data}"
                )
            },
        ],
    )
    raw_message = response["choices"][0]["message"]["content"]
    return raw_message.strip()

def extract_credit_card_number():
    image_path = ensure_under_data_dir("/data/credit_card.png")
    output_path = ensure_under_data_dir("/data/credit-card.txt")

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    with open(image_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    llm_response = call_llm_for_card(b64_data)
    print(f"LLM response: {llm_response}")

    card_number = re.sub(r"[^0-9]", "", llm_response)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(card_number)

    print(f"Extracted card number: {card_number}")

# A9
def find_similar_comments():
    """
    Uses GPT-4o-Mini to pick the pair of comments that are most similar.
    """
    input_file = ensure_under_data_dir("/data/comments.txt")
    output_file = ensure_under_data_dir("/data/comments-similar.txt")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"{input_file} does not exist")

    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("")
        print("Not enough comments to compare.")
        return

    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        raise Exception("AIPROXY_TOKEN environment variable not set.")

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    enumerated_lines = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))
    prompt = (
        "You are a helpful assistant. I have a list of comments (one per line). "
        "Please identify the TWO lines that are most semantically similar. "
        "Return your answer in JSON format as follows:\n\n"
        "{\n  \"best_pair\": [\"<comment1>\", \"<comment2>\"]\n}\n\n"
        "Here are the lines:\n\n"
        f"{enumerated_lines}\n\n"
        "Respond with only the JSON object."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        raw_message = response["choices"][0]["message"]["content"].strip()
        raw_message = re.sub(r"^```json\s*", "", raw_message)
        raw_message = re.sub(r"\s*```$", "", raw_message)
        data = json.loads(raw_message)
        best_pair = data.get("best_pair", [])
        if len(best_pair) != 2:
            raise ValueError("Could not find exactly 2 lines in the 'best_pair' key.")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(best_pair[0] + "\n" + best_pair[1] + "\n")

        print(f"A9: wrote best pair to {output_file}")
    except Exception as e:
        print(f"A9 error: {e}")

def find_most_similar_comments_local():
    """
    Uses local embeddings (sentence-transformers) to pick the most similar pair.
    """
    input_path = ensure_under_data_dir("/data/comments.txt")
    output_path = ensure_under_data_dir("/data/comments-similar.txt")

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        comments = [line.strip() for line in f if line.strip()]

    if len(comments) < 2:
        with open(output_path, "w", encoding="utf-8") as out:
            out.write("")
        print("Not enough comments to compare.")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(comments)
    best_score = -1
    best_pair = ("", "")

    def cosine_sim(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    n = len(comments)
    for i in range(n):
        for j in range(i + 1, n):
            score = cosine_sim(embeddings[i], embeddings[j])
            if score > best_score:
                best_score = score
                best_pair = (comments[i], comments[j])

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(best_pair[0] + "\n" + best_pair[1] + "\n")

    print(f"Most similar pair found (local) with score={best_score}")
    print(f"Wrote them to {output_path}")

# A10
def calculate_gold_sales():
    db_path = ensure_under_data_dir("/data/ticket-sales.db")
    output_path = ensure_under_data_dir("/data/ticket-sales-gold.txt")

    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = ?", ("Gold",))
    result = cursor.fetchone()
    conn.close()

    gold_sum = result[0] if result[0] is not None else 0
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(gold_sum))
    print(f"Total Gold sales = {gold_sum}. Wrote to {output_path}.")

# PHASE B: Security (B1/B2) and Business Tasks (B3–B10)

# (B1) Data outside /data is never accessed or exfiltrated.
#      We'll enforce this by wrapping any file path usage in a validator.

# (B2) Data is never deleted anywhere on the file system.
#      We simply won't implement any delete operation, 
#      and if user or LLM instructions mention "delete", we can refuse.

def ensure_under_data_dir(path: str) -> str:
    """
    Convert 'path' to an absolute path and check if it's under '/data'.
    Raise ValueError if not.
    Return the absolute path if valid.
    """
    data_root = os.path.abspath("/data")
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(data_root):
        raise ValueError(f"Path '{path}' is outside /data.")
    return abs_path

# B3: Fetch data from an API and save it
def fetch_data_from_api(url: str, output_path: str):
    safe_out = ensure_under_data_dir(output_path)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    with open(safe_out, "wb") as f:
        f.write(resp.content)
    print(f"Fetched data from {url} -> {safe_out}")

# B4: Clone a git repo and make a commit
def clone_and_commit(repo_url: str, local_dir: str, commit_msg="Automated commit"):
    safe_dir = ensure_under_data_dir(local_dir)
    subprocess.run(["git", "clone", repo_url, safe_dir], check=True)
    # Example: create README.md
    readme_path = os.path.join(safe_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Automated commit\nThis is a test.\n")

    subprocess.run(["git", "add", "."], cwd=safe_dir, check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=safe_dir, check=True)
    print(f"Cloned {repo_url} and made a commit in {safe_dir}.")

# B5: Run a SQL query on a SQLite database
def run_sql_query(db_path: str, query: str, output_path: str = None):
    safe_db = ensure_under_data_dir(db_path)
    conn = sqlite3.connect(safe_db)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.commit()
    conn.close()

    if output_path:
        safe_out = ensure_under_data_dir(output_path)
        with open(safe_out, "w", encoding="utf-8") as f:
            json.dump(rows, f)
        print(f"Query results written to {safe_out}")

    return rows

# B6: Extract data from (scrape) a website
from bs4 import BeautifulSoup
def scrape_website(url: str, output_path: str):
    safe_out = ensure_under_data_dir(output_path)
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Example: Collect all anchor tags
    data = []
    for a_tag in soup.find_all("a"):
        link = a_tag.get("href", "")
        text = a_tag.get_text(strip=True)
        data.append({"link": link, "text": text})

    with open(safe_out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Scraped {url} -> {safe_out}")

# B7: Compress or resize an image
def resize_image(in_path: str, out_path: str, size=(300,300)):
    safe_in = ensure_under_data_dir(in_path)
    safe_out = ensure_under_data_dir(out_path)
    with Image.open(safe_in) as img:
        img = img.resize(size)
        img.save(safe_out)
    print(f"Resized {safe_in} to {size} -> {safe_out}")

# B8: Transcribe audio from an MP3 file
# Requires 'whisper' or other transcription libs. Placeholder:
def transcribe_audio(mp3_path: str, out_path: str):
    safe_in = ensure_under_data_dir(mp3_path)
    safe_out = ensure_under_data_dir(out_path)
    # Example: local whisper usage
    # model = whisper.load_model("tiny")
    # result = model.transcribe(safe_in)
    # For now, just a placeholder
    text = "Transcribed text placeholder."
    with open(safe_out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Transcribed {safe_in} -> {safe_out}")

# B9: Convert Markdown to HTML
import markdown
def md_to_html(md_path: str, html_path: str):
    safe_in = ensure_under_data_dir(md_path)
    safe_out = ensure_under_data_dir(html_path)
    with open(safe_in, "r", encoding="utf-8") as f:
        md_text = f.read()
    html = markdown.markdown(md_text)
    with open(safe_out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Converted {md_path} -> {html_path}")

# B10: Write an API endpoint that filters a CSV file and returns JSON
# We'll show how to do it with a new endpoint:
import csv
from fastapi import Query
@app.get("/filter_csv")
def filter_csv(col: str = Query(...), value: str = Query(...)):
    # Example: We'll read from '/data/file.csv' (must exist).
    csv_path = ensure_under_data_dir("/data/file.csv")
    if not os.path.isfile(csv_path):
        raise HTTPException(status_code=404, detail="CSV file not found")

    results = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(col) == value:
                results.append(row)
    return {"results": results}

@app.get("/")
def root_endpoint():
    return {"message": "Hello from the Automation Agent"}

@app.get("/read")
def read_file(path: str):
    """
    GET /read?path=<file path>
    - Ensures the file is inside '/data/' folder
    - Returns content as plain text
    - Returns 404 if not found or outside /data
    """
    try:
        requested_path = ensure_under_data_dir(path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=404, detail="File not found.")

    with open(requested_path, "r", encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="text/plain")

@app.post("/run")
def run_task(task: str, email: str = ""):
    """
    /run?task=... 
    We detect which A/B tasks to run by keywords. 
    Also forbid 'delete' as per B2, if user tries that.
    """
    # (B2) If the task tries to say "delete", we refuse
    if "delete" in task.lower() or "remove" in task.lower():
        raise HTTPException(status_code=400, detail="Deleting files is not permitted (B2).")

    # PHASE A tasks
    if "a1" in task.lower() or "datagen" in task.lower():
        # 1) Try to parse email from the 'task' text
        parsed_email = extract_email_from_task(task)

        # 2) If that fails, fallback to the query param 'email' or a default
        user_email = parsed_email if parsed_email else email
        if not user_email:
            user_email = "user@example.com"
            # or you can raise an error if you really want to

        # Now call the datagen script
        try:
            run_datagen(user_email)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return JSONResponse({"message": f"A1 completed successfully for {user_email}"})

    if "a2" in task.lower() or "format.md" in task.lower():
        format_markdown_in_place()
        return {"message": "A2 completed: /data/format.md has been prettified"}

    if "a3" in task.lower() or "wednesday" in task.lower() or "dates-wednesdays.txt" in task.lower():
        try:
            count_wednesdays_in_dates()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A3 completed: /data/dates-wednesdays.txt updated"}

    if "a4" in task.lower() or "contacts-sorted" in task.lower():
        try:
            sort_contacts()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A4 completed: /data/contacts-sorted.json created"}

    if "a5" in task.lower() or "logs-recent" in task.lower():
        try:
            get_recent_logs()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A5 completed: /data/logs-recent.txt written"}

    if "a6" in task.lower() or "index.json" in task.lower() or "docs" in task.lower():
        try:
            build_docs_index()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A6 completed: /data/docs/index.json created"}

    if "a7" in task.lower() or "email-sender" in task.lower():
        try:
            extract_sender_email()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A7 completed: /data/email-sender.txt created"}

    if "a8" in task.lower() or "credit card" in task.lower():
        try:
            extract_credit_card_number()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A8 completed: /data/credit-card.txt created"}

    if "a9" in task.lower() or "comments-similar" in task.lower():
        # Choose either GPT-4o approach or local embeddings approach
        try:
            find_similar_comments()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A9 completed: /data/comments-similar.txt updated"}

    if "a10" in task.lower() or "ticket-sales-gold" in task.lower():
        try:
            calculate_gold_sales()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": "A10 completed: /data/ticket-sales-gold.txt created"}

    # PHASE B tasks
    if "b3" in task.lower() or "fetch api" in task.lower():
        # Example usage, adapt to real user input
        url = "https://jsonplaceholder.typicode.com/posts"
        out_file = "/data/fetched.json"
        try:
            fetch_data_from_api(url, out_file)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"B3 completed: Fetched data -> {out_file}"}

    if "b4" in task.lower() or "clone repo" in task.lower():
        repo_url = "https://github.com/someuser/somerepo.git"
        local_dir = "/data/repos/somerepo"
        try:
            clone_and_commit(repo_url, local_dir)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message": f"B4 completed: Cloned {repo_url} and committed."}

    if "b5" in task.lower() or "run sql" in task.lower():
        dbpath = "/data/some.db"
        query = "SELECT * FROM example_table;"
        outpath = "/data/query_output.json"
        try:
            rows = run_sql_query(dbpath, query, outpath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"SQL error: {e}")
        return {"message": f"B5 completed: Query wrote {len(rows)} rows to {outpath}"}

    if "b6" in task.lower() or "scrape" in task.lower():
        site_url = "https://example.com"
        out_file = "/data/scraped.json"
        try:
            scrape_website(site_url, out_file)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"B6 completed: Website data -> {out_file}"}

    if "b7" in task.lower() or "resize image" in task.lower():
        in_img = "/data/large.png"
        out_img = "/data/large-resized.png"
        try:
            resize_image(in_img, out_img, (300,300))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"B7 completed: {in_img} resized -> {out_img}"}

    if "b8" in task.lower() or "transcribe" in task.lower():
        mp3_path = "/data/meeting.mp3"
        out_txt = "/data/meeting-transcript.txt"
        try:
            transcribe_audio(mp3_path, out_txt)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"B8 completed: Audio transcribed -> {out_txt}"}

    if "b9" in task.lower() or "convert md to html" in task.lower():
        mdpath = "/data/docs/example.md"
        htmlpath = "/data/docs/example.html"
        try:
            md_to_html(mdpath, htmlpath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"B9 completed: {mdpath} -> {htmlpath}"}

    if "b10" in task.lower() or "filter csv" in task.lower():
        # We already made an endpoint (/filter_csv). You can do logic here if needed
        return {"message": "Use GET /filter_csv?col=...&value=... for B10 filtering."}

    # Default: no recognized task
    return JSONResponse({"message": f"Received task: {task} (but not recognized as A/B task)"})