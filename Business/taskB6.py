import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import os, pandas as pd
from urllib.parse import urljoin
from fastapi import HTTPException

def scrape_website(filename: str, targetfile: str, selectors: list = None, paginate: bool = False):
    print(f"Scraping website: {filename}, targetfile: {targetfile}, selectors: {selectors}, paginate: {paginate}")
    if not filename or not targetfile:
        raise HTTPException(status_code=400, detail="Invalid input parameters: filename and targetfile are required.")
    
    scraped_data = []
    url = filename[1:] if filename.startswith('.') else filename
    headers = {"User-Agent": "Mozilla/5.0"}

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        page_data = {}
        
        if selectors:
            for selector in selectors:
                elements = soup.select(selector)
                page_data[selector] = [elem.get_text(strip=True) for elem in elements]
        else:
            page_data["full_text"] = soup.get_text(strip=True)
        
        scraped_data.append(page_data)
        
        # Handle pagination if enabled
        if paginate:
            next_page = soup.select_one("a.next, a[rel='next']")
            url = urljoin(url, next_page["href"]) if next_page and "href" in next_page.attrs else None
            time.sleep(1)  # Avoid overloading the server
        else:
            break
    
    # Save data to the target file
    save_data(targetfile, scraped_data)
    print(f"Scraped data saved to {targetfile}")
    return f"Scraped data saved to {targetfile}"

def save_data(targetfile, data):
    _, ext = os.path.splitext(targetfile)
    # Overwrite or create a new file
    if ext == ".json":
        with open(targetfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    elif ext == ".csv":
        df = pd.DataFrame(data)
        df.to_csv(targetfile, index=False)
    elif ext == ".txt":
        with open(targetfile, "w", encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, indent=2) + "\n")
    else:
        return Exception(f"Unsupported file format: {ext}")
