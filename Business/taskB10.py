from fastapi import HTTPException
import pandas as pd
import json, os

def filter_csv(filename: str, targetfile: str, filters: list[dict]):
    #print(f"CSV_FILE_PATH: {CSV_FILE_PATH}, targetfile: {targetfile}, column: {column}, value: {value}")
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Input file must be a CSV file")
    if not os.path.exists(filename):
        raise HTTPException(status_code=400, detail=f"File not found: {filename}")
    
    try:
        # Read CSV file into DataFrame
        df = pd.read_csv(filename)
        
        # Apply filters
        for f in filters:
            column = f.get("column")
            value = f.get("value")
            if column not in df.columns:
                raise HTTPException(status_code=400, detail=f"Column '{column}' not found in CSV. Available columns: {df.columns.tolist()}")

            df = df[df[column] == value]
        
        # Convert to JSON and save to target file
        df.to_json(targetfile, orient="records", indent=4)
        
        return f"Filtering completed, output: {targetfile}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
