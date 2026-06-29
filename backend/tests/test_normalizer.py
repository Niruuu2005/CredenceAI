from app.services.normalizer import normalize_searxng_payload

def test_normalize_searxng_payload_success():
    raw_payload = {
        "query": "open source search",
        "results": [
            {
                "title": "SearXNG",
                "url": "https://searxng.github.io",
                "content": "A metasearch engine",
                "engine": "google"
            },
            {
                "title": "", # Invalid (missing title)
                "url": "https://empty-title.com",
                "content": "Description"
            },
            {
                "title": "No URL",
                "url": "", # Invalid (missing url)
                "content": "Description"
            }
        ]
    }
    
    normalized = normalize_searxng_payload(raw_payload, job_id="job_123", raw_payload_ref="s3://raw/job_123.json")
    
    assert len(normalized) == 1
    item = normalized[0]
    assert item["title"] == "SearXNG"
    assert item["url"] == "https://searxng.github.io"
    assert item["snippet"] == "A metasearch engine"
    assert item["source"] == "google"
    assert item["job_id"] == "job_123"
    assert item["raw_payload_ref"] == "s3://raw/job_123.json"
