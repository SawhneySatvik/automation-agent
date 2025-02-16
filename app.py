from fastapi import FastAPI, Response, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests, json, os, openai
from openai import OpenAI

import combined, llm_parser_lite as llm_parser
from Business.taskB1 import is_valid_path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'message': 'Hello World from docker container'}

@app.post("/run")
def run_task(task: str = Query(..., description="Task description")):
    try:
        #task_code = parse_task(task)
        task_classification = llm_parser.classify_task(task)
        result = combined.execute_task(task_classification, task)
        #return {"status": "success", "result": result}
        return result
    except ValueError as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

BASE_DIR = os.getcwd()  # Get the current working directory

@app.get("/read")
def read_file(path: str = Query(..., description="Relative file path")):
    
    if is_valid_path(path):
        # Convert to a relative path (prevent accessing files outside BASE_DIR)
        print(f"Checking file: {path}, {BASE_DIR}, {os.path.join(BASE_DIR, path)}")
        safe_path = os.path.abspath(os.path.join(BASE_DIR, path))
        safe_path = f'.{safe_path}'
        
        if not os.path.exists(safe_path):
            raise HTTPException(status_code=404, detail=f"File not found: {safe_path}")
        try:
            with open(safe_path, "r", encoding="utf-8") as file:
                content = file.read()
            return StreamingResponse(content, media_type="text/plain")
        except Exception as e:
            file_stream = open(safe_path, "rb")  # Open in binary mode
            return StreamingResponse(file_stream, media_type="application/octet-stream")
    
    
