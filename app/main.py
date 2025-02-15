import os
import sys
import subprocess
import pytesseract
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
import sqlite3 

app = FastAPI()
load_dotenv()  

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

#Call LLM
def call_llm(prompt: str) -> str:
    """
    Sends 'prompt' to GPT-4o-Mini via AI Proxy and returns the model's text response.
    """
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

#A7
def extract_sender_email():
    input_path = "data/email.txt"
    output_path = "data/email-sender.txt"

    # 1. Read the email content
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"{input_path} not found.")

    with open(input_path, "r", encoding="utf-8") as f:
        email_content = f.read()

    # 2. Call LLM with a short prompt
    # Keep it simple and explicit so the LLM only responds with the email address
    prompt = f"""Extract the sender's email address from this email content. 
Output only the email address, nothing else:

{email_content}
"""
    try:
        llm_response = call_llm(prompt)
    except RuntimeError as e:
        raise RuntimeError(f"Error calling LLM: {e}")

    # 3. Write the LLM response (assumed to be the email address) to output
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(llm_response)

    print(f"Sender email extracted to {output_path}: {llm_response}")

#A8
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
    image_path = "data/credit_card.png"
    output_path = "data/credit-card.txt"

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    with open(image_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    # Call the revised function with a clearer system prompt
    llm_response = call_llm_for_card(b64_data)

    print(f"LLM response: {llm_response}")

    # Keep only digits
    card_number = re.sub(r"[^0-9]", "", llm_response)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(card_number)

    print(f"Extracted card number: {card_number}")

#A9
def find_similar_comments():
    input_file = "data/comments.txt"
    output_file = "data/comments-similar.txt"
    
    if not os.path.exists(input_file):
        return {"error": f"{input_file} does not exist"}

    # 3. Read lines (strip empty ones)
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        return {"error": "Not enough comments to compare."}

    # 4. Set up your GPT-4o-Mini credentials
    token = os.environ.get("AIPROXY_TOKEN")

    if not token:
        return {"error": "AIPROXY_TOKEN environment variable not set."}

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    # 5. Build a prompt enumerating all lines
    #    Ask GPT-4o-Mini to return a JSON object with "best_pair": [line1, line2]
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
        # 6. Call GPT-4o-Mini with the prompt
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        # 7. Parse the raw response to extract JSON
        raw_message = response["choices"][0]["message"]["content"]
        # Remove potential markdown fences
        raw_message = re.sub(r"^```json\s*", "", raw_message.strip())
        raw_message = re.sub(r"\s*```$", "", raw_message)
        if not raw_message.strip():
            return {"error": f"LLM returned empty or invalid response: {response}"}

        data = json.loads(raw_message)
        best_pair = data.get("best_pair", [])
        if len(best_pair) != 2:
            return {"error": f"Could not find exactly 2 lines. Received: {best_pair}"}
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(best_pair[0] + "\n")
            f.write(best_pair[1] + "\n")

        return {
            "status": "success",
            "best_pair": best_pair,
            "written_file": output_file
        }

    except Exception as e:
        return {"error": str(e)}

def find_most_similar_comments_local():
    input_path = "data/comments.txt"
    output_path = "data/comments-similar.txt"

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        comments = [line.strip() for line in f if line.strip()]

    if len(comments) < 2:
        with open(output_path, "w", encoding="utf-8") as out:
            out.write("")
        print("Not enough comments to compare.")
        return

    # Load a local embeddings model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Encode all comments
    embeddings = model.encode(comments)

    # Pairwise comparison
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

    # Write result
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(best_pair[0] + "\n" + best_pair[1])

    print(f"Most similar pair found (local embeddings) with score={best_score}")
    print(f"Wrote them to {output_path}")
   
#A10 
def calculate_gold_sales():
    """
    Connects to data/ticket-sales.db, queries SUM(units * price) where type='Gold',
    writes the result to data/ticket-sales-gold.txt.
    """
    db_path = "data/ticket-sales.db"
    output_path = "data/ticket-sales-gold.txt"

    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # 1. Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. Run the SUM query
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = ?", ("Gold",))
    result = cursor.fetchone()
    conn.close()

    # 3. Extract the sum (handle None if no rows)
    gold_sum = result[0] if result[0] is not None else 0

    # 4. Write the sum to data/ticket-sales-gold.txt
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(gold_sum))

    print(f"Total Gold sales = {gold_sum}. Wrote to {output_path}.")
    
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
    if "A1" in task.lower() or "datagen" in task:
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
    
    if "A7" in task.upper() or "email-sender" in task.lower() or "sender’s email" in task.lower():
        try:
            extract_sender_email()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A7 completed: email-sender.txt has been created."}
    
    if "A8" in task.upper() or "credit card" in task.lower():
        try:
            extract_credit_card_number()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A8 completed: credit-card.txt has been created"}
    
    if "A9" in task.upper() or "comments-similar" in task.lower():
        try:
            find_similar_comments()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A9 completed: most similar comments in comments-similar.txt"}
    
    if "A10" in task.upper() or "ticket-sales-gold" in task.lower():
        try:
            calculate_gold_sales()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"message": "A10 completed: ticket-sales-gold.txt has been created"}
    

    # Default response
    return JSONResponse({"message": f"Received task: {task}"})