import requests
import time
import sys

import os
BASE_URL = os.getenv("CREDENCEAI_BASE_URL", "http://localhost:8000")

def main():
    query = "Google DeepMind Gemini news"
    print(f"Submitting job: {query}")
    res = requests.post(f"{BASE_URL}/jobs", json={
        "job_type": "search_query",
        "input": query,
        "vertical": "web"
    })
    
    if res.status_code not in (200, 202):
        print(f"Failed to submit: {res.status_code} - {res.text}")
        sys.exit(1)
        
    data = res.json()
    job_id = data["job_id"]
    print(f"Submitted. Job ID: {job_id}")
    
    for i in range(15):
        time.sleep(2)
        status_res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if status_res.status_code != 200:
            print(f"Failed to poll: {status_res.status_code}")
            continue
        status_data = status_res.json()
        print(f"Poll {i+1}: status={status_data.get('status')}, results={status_data.get('results_count')}")
        if status_data.get("status") in ("completed", "failed"):
            results = status_data.get("result", {}).get("results", [])
            for idx, r in enumerate(results[:2]):
                print(f"Result {idx+1}: title={r.get('title')}, url={r.get('url')}, source={r.get('source')}")
            break

if __name__ == "__main__":
    main()
