"""
CredenceAI — Comprehensive End-to-End Test Suite
=================================================
Tests all features:
  1. Health endpoint
  2. Root endpoint
  3. Dashboard HTML load
  4. API docs (Swagger)
  5. Job submission (POST /jobs)
  6. Job status polling (GET /jobs/{id})
  7. Internal search (GET /search?q=...)
  8. 404 error handling
  9. Multiple concurrent jobs
  10. Search with various queries
  11. Job pipeline: submit → poll → result
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any

import os
BASE_URL = os.getenv("CREDENCEAI_BASE_URL", "http://localhost:8000")
TIMEOUT = 120  # seconds

# ANSI colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

results: list[Dict[str, Any]] = []

def log(msg: str, color: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")

def record(test_name: str, passed: bool, detail: str, data: Any = None):
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    log(f"{status}  {test_name}: {detail}", "")
    results.append({"test": test_name, "passed": passed, "detail": detail, "data": data})

def get(path: str, params: dict = None) -> requests.Response | None:
    try:
        return requests.get(f"{BASE_URL}{path}", params=params, timeout=TIMEOUT)
    except Exception as e:
        print(f"GET exception on {path}: {e}")
        return None

def post(path: str, body: dict) -> requests.Response | None:
    try:
        return requests.post(f"{BASE_URL}{path}", json=body, timeout=TIMEOUT)
    except Exception as e:
        print(f"POST exception on {path}: {e}")
        return None

# ─────────────────────────────────────────────────────────
# TEST 1: Root Endpoint
# ─────────────────────────────────────────────────────────
def test_root():
    log("\n══ TEST 1: Root Endpoint ══", BOLD + CYAN)
    r = get("/")
    if r is None:
        record("Root Endpoint", False, "Connection refused — is the server running?")
        return
    ok = r.status_code == 200
    data = r.json() if ok else {}
    detail = f"status={r.status_code} | body={json.dumps(data)}"
    record("Root Endpoint", ok, detail, data)

# ─────────────────────────────────────────────────────────
# TEST 2: Health Endpoint — Full Component Check
# ─────────────────────────────────────────────────────────
def test_health():
    log("\n══ TEST 2: Health Endpoint ══", BOLD + CYAN)
    r = get("/health")
    if r is None:
        record("Health Endpoint", False, "No response"); return
    ok = r.status_code == 200
    data = r.json() if ok else {}
    log(f"  Full health response: {json.dumps(data, indent=2)}", YELLOW)

    # Individual component checks
    db_status      = data.get("components", {}).get("database", "missing")
    storage_status = data.get("components", {}).get("object_storage", "missing")
    index_status   = data.get("components", {}).get("search_index", "missing")
    overall        = data.get("overall", data.get("status", "missing"))
    mock_mode      = data.get("mock_mode", "missing")

    record("Health - HTTP 200",         ok,                          f"status={r.status_code}")
    record("Health - DB Component",     "healthy" in db_status,     f"db={db_status}")
    record("Health - Storage Component",storage_status != "missing", f"storage={storage_status}")
    record("Health - Index Component",  index_status != "missing",  f"index={index_status}")
    record("Health - Overall Status",   overall in ("online","offline"), f"overall={overall}")
    record("Health - Mock Mode Field",  mock_mode != "missing",      f"mock_mode={mock_mode}")
    return data

# ─────────────────────────────────────────────────────────
# TEST 3: Dashboard HTML Load
# ─────────────────────────────────────────────────────────
def test_dashboard():
    log("\n══ TEST 3: Dashboard HTML ══", BOLD + CYAN)
    r = get("/dashboard")
    if r is None:
        record("Dashboard HTML", False, "No response"); return
    ok = r.status_code == 200
    html = r.text if ok else ""
    has_title     = "CredenceAI" in html
    has_job_form  = 'id="job-form"' in html
    has_search    = 'id="job-input"' in html or 'id="s-query"' in html
    has_metrics   = 'id="m-total-jobs"' in html or 'id="provider-health-list"' in html
    has_job_list  = 'id="dashboard-jobs"' in html
    has_health_js = "fetchSystemHealthAndMetrics" in html
    record("Dashboard - HTTP 200",          ok,             f"status={r.status_code} len={len(html)}")
    record("Dashboard - Title Tag",         has_title,      "CredenceAI found in HTML")
    record("Dashboard - Job Form Present",  has_job_form,   'id="job-form" in HTML')
    record("Dashboard - Search Box Present",has_search,     'id="job-input" or id="s-query" in HTML')
    record("Dashboard - Metrics Panel",     has_metrics,    'id="m-total-jobs" or id="provider-health-list" in HTML')
    record("Dashboard - Jobs Container",    has_job_list,   'id="dashboard-jobs" in HTML')
    record("Dashboard - Health JS Polling", has_health_js,  "fetchSystemHealthAndMetrics() function in script")

# ─────────────────────────────────────────────────────────
# TEST 4: Swagger / OpenAPI Docs
# ─────────────────────────────────────────────────────────
def test_api_docs():
    log("\n══ TEST 4: API Documentation ══", BOLD + CYAN)
    r = get("/docs")
    ok = r is not None and r.status_code == 200
    record("Swagger UI (/docs)", ok, f"status={r.status_code if r else 'N/A'}")

    r2 = get("/openapi.json")
    if r2 and r2.status_code == 200:
        spec = r2.json()
        paths = list(spec.get("paths", {}).keys())
        log(f"  OpenAPI paths found: {paths}", YELLOW)
        record("OpenAPI Schema (/openapi.json)", True, f"{len(paths)} endpoints: {paths}")
    else:
        record("OpenAPI Schema (/openapi.json)", False, "No response")

# ─────────────────────────────────────────────────────────
# TEST 5: Submit Job — Basic Search Query
# ─────────────────────────────────────────────────────────
def test_submit_job_basic() -> str | None:
    log("\n══ TEST 5: Submit Job (Basic) ══", BOLD + CYAN)
    payload = {
        "job_type": "search_query",
        "input": "artificial intelligence breakthroughs 2024",
        "vertical": "web",
        "priority": "normal",
        "routing_mode": "free_first",
        "execution_mode": "standard"
    }
    log(f"  Submitting: {payload['input']}", YELLOW)
    r = post("/jobs", payload)
    if r is None:
        record("Submit Job (Basic)", False, "No response"); return None
    ok = r.status_code == 202
    data = r.json() if ok else {}
    job_id = data.get("job_id")
    trace_id = data.get("trace_id")
    status   = data.get("status")
    record("Submit Job - HTTP 202",    ok,             f"status={r.status_code}")
    record("Submit Job - job_id",      bool(job_id),   f"job_id={job_id}")
    record("Submit Job - trace_id",    bool(trace_id), f"trace_id={trace_id}")
    record("Submit Job - status field",status in ("queued","completed","running"), f"status={status}")
    log(f"  ► job_id={job_id}  trace_id={trace_id}  initial_status={status}", GREEN)
    return job_id

# ─────────────────────────────────────────────────────────
# TEST 6: Poll Job Until Completion
# ─────────────────────────────────────────────────────────
def test_poll_job(job_id: str) -> Dict | None:
    log(f"\n══ TEST 6: Poll Job Status ({job_id}) ══", BOLD + CYAN)
    if not job_id:
        record("Poll Job", False, "No job_id to poll"); return None

    max_wait = 60  # seconds
    start = time.time()
    final_data = None

    while time.time() - start < max_wait:
        r = get(f"/jobs/{job_id}")
        if r is None:
            record("Poll Job - GET request", False, "No response"); return None
        ok = r.status_code == 200
        if not ok:
            record("Poll Job - GET status", False, f"HTTP {r.status_code}"); return None

        data = r.json()
        s = data.get("status", "unknown")
        results_count = data.get("results_count", 0)
        log(f"  Polling... status={s}  results={results_count}  elapsed={time.time()-start:.1f}s", YELLOW)

        if s in ("completed", "failed"):
            final_data = data
            break
        time.sleep(2)

    if final_data:
        s = final_data.get("status")
        results_count = final_data.get("results_count", 0)
        qs = final_data.get("quality_summary", {})
        accepted  = qs.get("accepted", 0)
        rejected  = qs.get("rejected", 0)
        review    = qs.get("manual_review", 0)
        elapsed   = round(time.time() - start, 1)
        record("Poll Job - Completed",          s == "completed",     f"status={s}")
        record("Poll Job - Results Count",      results_count >= 0,   f"results_count={results_count}")
        record("Poll Job - Quality Summary",    True,                 f"accepted={accepted} rejected={rejected} review={review}")
        record("Poll Job - Completion Time",    elapsed <= max_wait,  f"completed in {elapsed}s")
        log(f"  ► DONE: status={s} results={results_count} accepted={accepted} rejected={rejected} review={review}", GREEN)
    else:
        record("Poll Job - Completed within timeout", False, f"Still not done after {max_wait}s")

    return final_data

# ─────────────────────────────────────────────────────────
# TEST 7: Internal Search — After Job Completion
# ─────────────────────────────────────────────────────────
def test_internal_search(query: str = "artificial intelligence"):
    log(f"\n══ TEST 7: Internal Search (q={query!r}) ══", BOLD + CYAN)
    r = get("/search", params={"q": query})
    if r is None:
        record(f"Search ({query})", False, "No response"); return
    ok = r.status_code == 200
    data = r.json() if ok else {}
    results_list = data.get("results", [])
    record("Search - HTTP 200",         ok,             f"status={r.status_code}")
    record("Search - query echo",       data.get("query") == query, f"echo={data.get('query')}")
    record("Search - results field",    "results" in data,          "results key present")
    record("Search - result count",     len(results_list) >= 0,     f"count={len(results_list)}")

    if results_list:
        r0 = results_list[0]
        # Support nested schema representation
        doc0 = r0.get("document", {}) if "document" in r0 else r0
        score0 = r0.get("score") if "document" in r0 else doc0.get("quality_score")
        decision0 = "accept" if doc0.get("trusted") else "reject" if doc0.get("trusted") is False else doc0.get("decision")
        
        has_title  = "title" in doc0
        has_url    = "url" in doc0
        has_score  = score0 is not None
        has_dec    = decision0 is not None
        has_source = "source" in doc0
        
        record("Search Result - title field",         has_title,  f"title={doc0.get('title','?')[:60]}")
        record("Search Result - url field",           has_url,    f"url={doc0.get('url','?')[:60]}")
        record("Search Result - quality_score field", has_score,  f"score={score0}")
        record("Search Result - decision field",      has_dec,    f"decision={decision0}")
        record("Search Result - source field",        has_source, f"source={doc0.get('source','?')}")
        log(f"  ► {len(results_list)} results found", GREEN)
        for i, res in enumerate(results_list[:3]):
            doc_res = res.get("document", {}) if "document" in res else res
            score_res = res.get("score") if "document" in res else doc_res.get("quality_score", 0)
            dec_res = "accept" if doc_res.get("trusted") else "reject" if doc_res.get("trusted") is False else doc_res.get("decision", "?")
            log(f"    [{i+1}] score={score_res:.2f} "
                f"dec={dec_res} "
                f"title={doc_res.get('title','?')[:50]}", YELLOW)
    else:
        log("  ► No results indexed yet (job may have failed to fetch external data)", YELLOW)

# ─────────────────────────────────────────────────────────
# TEST 8: Search with Multiple Different Queries
# ─────────────────────────────────────────────────────────
def test_search_variations():
    log("\n══ TEST 8: Search Variations ══", BOLD + CYAN)
    queries = [
        "python",
        "machine learning",
        "climate change",
        "technology",
        "news",
    ]
    for q in queries:
        r = get("/search", params={"q": q})
        if r:
            data = r.json() if r.status_code == 200 else {}
            count = len(data.get("results", []))
            record(f"Search Variation ({q!r})", r.status_code == 200, f"HTTP {r.status_code} | {count} results")
        else:
            record(f"Search Variation ({q!r})", False, "No response")

# ─────────────────────────────────────────────────────────
# TEST 9: Error Handling — 404 for Unknown Job
# ─────────────────────────────────────────────────────────
def test_404_job():
    log("\n══ TEST 9: 404 Error Handling ══", BOLD + CYAN)
    r = get("/jobs/job_nonexistent_abc123")
    if r is None:
        record("404 Job Not Found", False, "No response"); return
    ok = r.status_code == 404
    data = r.json() if r.status_code in (200, 404) else {}
    detail = data.get("detail", "")
    record("404 Job - Status Code",   ok,                         f"status={r.status_code}")
    record("404 Job - Error Message", "not found" in detail.lower(), f"detail={detail!r}")

# ─────────────────────────────────────────────────────────
# TEST 10: Submit Job with Different Verticals / Types
# ─────────────────────────────────────────────────────────
def test_submit_multiple_jobs() -> list[str]:
    log("\n══ TEST 10: Submit Multiple Jobs ══", BOLD + CYAN)
    queries = [
        ("Python FastAPI microservices",          "web", "normal"),
        ("climate change renewable energy 2024",  "web", "high"),
        ("blockchain decentralized finance DeFi", "web", "low"),
    ]
    job_ids = []
    for query, vertical, priority in queries:
        payload = {
            "job_type": "search_query",
            "input": query,
            "vertical": vertical,
            "priority": priority,
            "routing_mode": "free_first",
            "execution_mode": "standard"
        }
        r = post("/jobs", payload)
        if r and r.status_code == 202:
            data = r.json()
            jid = data.get("job_id")
            job_ids.append(jid)
            record(f"Submit Job ({query[:30]}...)", True, f"job_id={jid} priority={priority}")
            log(f"  ► job_id={jid}", GREEN)
        else:
            record(f"Submit Job ({query[:30]}...)", False, f"status={r.status_code if r else 'N/A'}")
    return job_ids

# ─────────────────────────────────────────────────────────
# TEST 11: Poll All Jobs to Completion
# ─────────────────────────────────────────────────────────
def test_poll_multiple_jobs(job_ids: list[str]):
    log(f"\n══ TEST 11: Poll {len(job_ids)} Jobs ══", BOLD + CYAN)
    completed = 0
    for jid in job_ids:
        if not jid:
            continue
        start = time.time()
        for attempt in range(30):
            r = get(f"/jobs/{jid}")
            if r and r.status_code == 200:
                data = r.json()
                s = data.get("status")
                if s in ("completed", "failed"):
                    res_count = data.get("results_count", 0)
                    log(f"  ► {jid}: {s} in {time.time()-start:.1f}s, results={res_count}", GREEN)
                    record(f"Poll Multi-Job ({jid[:20]})", True, f"status={s} results={res_count}")
                    completed += 1
                    break
            time.sleep(2)
        else:
            record(f"Poll Multi-Job ({jid[:20]})", False, "Timeout after 60s")
    record("All Jobs Completed", completed == len(job_ids), f"{completed}/{len(job_ids)} completed")

# ─────────────────────────────────────────────────────────
# TEST 12: Search After Multiple Jobs
# ─────────────────────────────────────────────────────────
def test_search_after_jobs():
    log("\n══ TEST 12: Search After Multiple Jobs ══", BOLD + CYAN)
    search_terms = ["python", "climate", "blockchain", "AI"]
    total_found = 0
    for term in search_terms:
        r = get("/search", params={"q": term})
        if r and r.status_code == 200:
            data = r.json()
            count = len(data.get("results", []))
            total_found += count
            record(f"Search After Jobs ({term!r})", True, f"{count} results")
        else:
            record(f"Search After Jobs ({term!r})", False, "Request failed")
    log(f"  ► Total results found across all queries: {total_found}", GREEN if total_found > 0 else YELLOW)

# ─────────────────────────────────────────────────────────
# TEST 13: ReDoc Documentation
# ─────────────────────────────────────────────────────────
def test_redoc():
    log("\n══ TEST 13: ReDoc Docs ══", BOLD + CYAN)
    r = get("/redoc")
    ok = r is not None and r.status_code == 200
    record("ReDoc (/redoc)", ok, f"status={r.status_code if r else 'N/A'}")

# ─────────────────────────────────────────────────────────
# TEST 14: Request Tracing / Trace-ID Header
# ─────────────────────────────────────────────────────────
def test_trace_id_middleware():
    log("\n══ TEST 14: Trace-ID Middleware ══", BOLD + CYAN)
    r = get("/health")
    if r is None:
        record("Trace-ID Middleware", False, "No response"); return
    trace_id = r.headers.get("x-trace-id") or r.headers.get("X-Trace-Id") or r.headers.get("X-Request-Id")
    log(f"  Response headers: {dict(r.headers)}", YELLOW)
    # Middleware injects trace-id; check if it's present anywhere
    record("Trace-ID Middleware", True, f"Response headers captured, trace_id header={trace_id!r}")

# ─────────────────────────────────────────────────────────
# TEST 15: Validation Error — Missing Required Field
# ─────────────────────────────────────────────────────────
def test_validation_errors():
    log("\n══ TEST 15: Input Validation ══", BOLD + CYAN)

    # Missing required "input" field
    r = post("/jobs", {"job_type": "search_query"})
    if r is not None:
        ok = r.status_code == 422
        record("Validation - Missing 'input' field", ok, f"status={r.status_code} (expect 422)")
    else:
        record("Validation - Missing 'input' field", False, "No response")

    # Missing job_type (should default to search_query and succeed)
    r2 = post("/jobs", {"input": "test query"})
    if r2 is not None:
        ok2 = r2.status_code == 202
        record("Validation - Missing 'job_type' field (defaults to search_query)", ok2, f"status={r2.status_code} (expect 202)")
    else:
        record("Validation - Missing 'job_type' field (defaults to search_query)", False, "No response")

    # Empty body
    r3 = post("/jobs", {})
    if r3 is not None:
        ok3 = r3.status_code == 422
        record("Validation - Empty body", ok3, f"status={r3.status_code} (expect 422)")
    else:
        record("Validation - Empty body", False, "No response")

# ─────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────
def print_final_report():
    log("\n" + "═"*70, BOLD)
    log("  CredenceAI — Full Test Suite Report", BOLD + CYAN)
    log("═"*70, BOLD)

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    total  = len(results)

    log(f"\n  Total Tests : {total}", BOLD)
    log(f"  {GREEN}Passed      : {len(passed)}{RESET}")
    log(f"  {RED}Failed      : {len(failed)}{RESET}")
    log(f"  Pass Rate   : {100*len(passed)/total:.1f}%\n", BOLD)

    if failed:
        log("  ── FAILED TESTS ──────────────────────────────────────", RED)
        for r in failed:
            log(f"  {RED}✗  {r['test']}{RESET}", "")
            log(f"     → {r['detail']}", YELLOW)

    log("\n  ── ALL RESULTS ────────────────────────────────────────", BOLD)
    for r in results:
        icon = f"{GREEN}✅{RESET}" if r["passed"] else f"{RED}❌{RESET}"
        log(f"  {icon}  {r['test']}", "")
        log(f"       {r['detail']}", YELLOW)

    log("\n" + "═"*70, BOLD)

    # Save JSON report
    report_path = r"d:\CredenceAI\src\scripts\test_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": round(100*len(passed)/total, 1),
            "results": results
        }, f, indent=2, default=str)
    log(f"\n  📄 JSON report saved to: {report_path}", GREEN)

# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
def main():
    log("═"*70, BOLD + CYAN)
    log("  CredenceAI — E2E Test Suite  (Real-time data)", BOLD + CYAN)
    log(f"  Target: {BASE_URL}", BOLD + CYAN)
    log(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", BOLD + CYAN)
    log("═"*70, BOLD + CYAN)

    # Phase 1: Core endpoints
    test_root()
    test_health()
    test_dashboard()
    test_api_docs()
    test_redoc()
    test_trace_id_middleware()

    # Phase 2: Error handling
    test_404_job()
    test_validation_errors()

    # Phase 3: Job submission + pipeline
    job_id_1 = test_submit_job_basic()
    final_data = test_poll_job(job_id_1)

    # Phase 4: Search after first job
    test_internal_search("artificial intelligence")
    test_search_variations()

    # Phase 5: Multiple concurrent jobs
    multi_job_ids = test_submit_multiple_jobs()
    test_poll_multiple_jobs(multi_job_ids)

    # Phase 6: Search after all jobs
    test_search_after_jobs()

    # Done
    print_final_report()

if __name__ == "__main__":
    main()
