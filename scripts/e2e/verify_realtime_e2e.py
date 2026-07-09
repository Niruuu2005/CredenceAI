import time
import requests
import json
import sys

# Reconfigure stdout to use UTF-8 to prevent charmap encoding errors on Windows
sys.stdout.reconfigure(encoding='utf-8')

PORT = 8012
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_e2e_tests():
    print("=" * 70)
    print("[*] Waiting 15 seconds for server connection fallbacks (MinIO/OpenSearch timeouts) to settle...")
    time.sleep(15)
    
    print(f"[*] Checking health of pre-started FastAPI server on {BASE_URL}...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=15)
        if r.status_code == 200:
            print(f"[+] Server is UP and healthy: {r.json()}")
        else:
            print(f"[-] Server returned unhealthy status code {r.status_code}: {r.text}")
            sys.exit(1)
    except Exception as e:
        print(f"[-] Failed to connect to server: {e}")
        sys.exit(1)
        
    # 2. Define test scenarios
    scenarios = [
        {
            "name": "Real-time News/Freshness Query",
            "input": "SpaceX Starship latest launch news",
            "vertical": "news",
            "search_term": "SpaceX"
        },
        {
            "name": "Real-time General Web Query",
            "input": "Nvidia stock performance news 2026",
            "vertical": "web",
            "search_term": "Nvidia"
        },
        {
            "name": "Edge Case: Empty Query",
            "input": "",
            "vertical": "web",
            "search_term": ""
        },
        {
            "name": "Edge Case: Extremely Long Query",
            "input": "AI " * 200,
            "vertical": "web",
            "search_term": "AI"
        },
        {
            "name": "Edge Case: SQL Injection Pattern Query",
            "input": "'; DROP TABLE jobs; --",
            "vertical": "web",
            "search_term": "DROP"
        },
        {
            "name": "Edge Case: Unicode and Emojis Query",
            "input": "Testing 🚀 unicode 漢字 Search Engine",
            "vertical": "web",
            "search_term": "Testing"
        }
    ]
    
    results_summary = []
    
    for idx, sc in enumerate(scenarios, 1):
        print("\n" + "-" * 60)
        print(f"[{idx}] Scenario: {sc['name']}")
        print(f"    Input  : '{sc['input'][:60]}'" + ("..." if len(sc['input']) > 60 else ""))
        print(f"    Vertical: {sc['vertical']}")
        
        # Post job
        t0 = time.time()
        res = requests.post(
            f"{BASE_URL}/jobs",
            json={
                "job_type": "search_query",
                "input": sc["input"],
                "vertical": sc["vertical"]
            }
        )
        
        if res.status_code not in (200, 202):
            print(f"    [-] Job submission failed (HTTP {res.status_code}): {res.text}")
            results_summary.append({
                "scenario": sc["name"],
                "input": sc["input"][:30],
                "status": f"FAILED_SUBMISSION_{res.status_code}",
                "results_count": 0,
                "elapsed": round(time.time() - t0, 2)
            })
            continue
            
        job_data = res.json()
        job_id = job_data["job_id"]
        print(f"    [+] Submitted successfully. Job ID: {job_id}")
        
        # Poll status
        status = "queued"
        elapsed = 0
        results_count = 0
        while status in ("queued", "running") and elapsed < 45:
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/jobs/{job_id}")
            if status_res.status_code == 200:
                status_data = status_res.json()
                status = status_data["status"]
                results_count = status_data.get("results_count", 0)
            else:
                print(f"    [-] Failed to get status (HTTP {status_res.status_code})")
            elapsed = time.time() - t0
            print(f"    [*] Polling job status: {status} (elapsed: {elapsed:.1f}s)")
            
        print(f"    [+] Final Status: {status} | Results Count: {results_count} | Total Time: {elapsed:.2f}s")
        
        # If results exist, search internal index for them
        if results_count > 0 and sc["search_term"]:
            search_res = requests.get(f"{BASE_URL}/search", params={"q": sc["search_term"]})
            if search_res.status_code == 200:
                s_data = search_res.json()
                s_results = s_data.get("results", [])
                print(f"    [+] Internal Search for '{sc['search_term']}' returned {len(s_results)} entries.")
                if s_results:
                    first = s_results[0]
                    # Handle nested schema representation
                    doc = first.get("document", {}) if "document" in first else first
                    score = first.get("score") if "document" in first else doc.get("quality_score")
                    decision = "accept" if doc.get("trusted") else "reject" if doc.get("trusted") is False else doc.get("decision")
                    
                    print(f"        First Result Title: {doc.get('title')}")
                    print(f"        First Result Score: {score}")
                    print(f"        First Result Decision: {decision}")
                    print(f"        Entities: {[e['canonical_name'] for e in doc.get('entities', [])]}")
                    print(f"        Duplicates Grouped: {len(doc.get('duplicates', []))}")
            else:
                print(f"    [-] Search query failed (HTTP {search_res.status_code})")
                
        results_summary.append({
            "scenario": sc["name"],
            "input": sc["input"][:30] + ("..." if len(sc["input"]) > 30 else ""),
            "status": status,
            "results_count": results_count,
            "elapsed": round(elapsed, 2)
        })
        
    print("\n" + "=" * 70)
    print("                      E2E VERIFICATION REPORT")
    print("=" * 70)
    print(f"{'Scenario':<35} | {'Input':<25} | {'Status':<10} | {'Results':<8} | {'Elapsed':<8}")
    print("-" * 92)
    for r in results_summary:
        print(f"{r['scenario']:<35} | {r['input']:<25} | {r['status']:<10} | {r['results_count']:<8} | {r['elapsed']}s")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_tests()
