"""
Celery Crawler Task for CredenceAI Iteration 0.3

Coordinates crawl safety policies before fetching, performs HTTP requests (or mocks),
uploads payloads to raw storage, and persists Document records.
"""

import uuid
import datetime
import logging
import hashlib
import time
import requests
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from app.worker import celery_app
import app.worker as worker_module
from app.services.crawl_policy import CrawlPolicyService
from app.services.storage import StorageClient
from app.models import Document, CrawlPolicyDecision
from app.config import settings

logger = logging.getLogger(__name__)

def compute_hash(text: str) -> str:
    """Helper to calculate SHA-256 hash of text."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

@celery_app.task(name="app.worker.crawl_url")
def crawl_url(job_id: Optional[str], url: str) -> dict:
    """
    Celery task that evaluates policy constraints, crawls the URL,
    persists crawled Document or Policy Decisions, and uploads raw html.
    """
    t0 = time.perf_counter()
    logger.info(f"CRAWLER_TASK  job_id={job_id}  url={url}")
    
    db: Session = worker_module.get_db_session()
    policy_service = CrawlPolicyService()
    storage_client = StorageClient()
    
    decision_id = f"cp_dec_{uuid.uuid4().hex[:12]}"
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    try:
        # 1. Evaluate policy
        eval_result = policy_service.evaluate(url)
        allowed = eval_result["allowed"]
        reason = eval_result["reason"]
        
        # Enforce rate limiting if needed
        if allowed and not eval_result["rate_limit_ok"]:
            wait_time = eval_result["wait_time"]
            logger.info(f"CRAWLER_TASK  rate_limited  sleeping={wait_time:.2f}s  url={url}")
            time.sleep(wait_time)
            
        # Log policy decision in database
        db_decision = CrawlPolicyDecision(
            id=decision_id,
            job_id=job_id,
            url=url,
            allowed=allowed,
            reason=reason,
            checked_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(db_decision)
        db.commit()
        
        if not allowed:
            logger.warning(f"CRAWLER_TASK  BLOCKED  url={url}  reason={reason}")
            return {
                "success": False,
                "status": "blocked",
                "reason": reason,
                "document_id": None
            }
            
        # Record request time for rate limits
        policy_service.record_crawl(url)
        
        # 2. Execute Crawl
        title = ""
        body_text = ""
        raw_html = ""
        mime_type = "text/html"
        
        if settings.MOCK_SERVICES:
            # Mock crawl response
            title = f"Mocked Page for {urlparse(url).hostname}"
            body_text = f"This is a mocked crawl content of {url}. It contains various paragraphs, keywords, and details about research."
            raw_html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><p>{body_text}</p></body></html>"
            logger.info(f"CRAWLER_TASK  MOCK_CRAWL  url={url}")
        else:
            # Make a real HTTP request
            headers = {"User-Agent": "CredenceAICrawler/1.0"}
            
            # Pre-flight check headers to prevent large downloads before reading body
            head_resp = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            content_type = head_resp.headers.get("content-type", "text/html")
            mime_type = content_type.split(";")[0].strip()
            
            # File size limit check
            content_length = head_resp.headers.get("content-length")
            if content_length and int(content_length) > settings.CRAWL_MAX_FILE_SIZE:
                error_msg = f"File size exceeds safety limit: {content_length} > {settings.CRAWL_MAX_FILE_SIZE}"
                logger.error(f"CRAWLER_TASK  ERROR  url={url}  error='{error_msg}'")
                return {
                    "success": False,
                    "status": "failed",
                    "reason": error_msg,
                    "document_id": None
                }
            
            # Perform GET request
            resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            resp.raise_for_status()
            
            raw_html = resp.text
            mime_type = resp.headers.get("content-type", "text/html").split(";")[0].strip()
            
            # Parse html
            soup = BeautifulSoup(raw_html, "html.parser")
            title = soup.title.string.strip() if soup.title else ""
            
            # Extract main readable text
            # Kill script/style elements
            for script in soup(["script", "style"]):
                script.decompose()
            body_text = soup.get_text(separator=" ").strip()
            
        # 3. Store raw html payload in MinIO
        bucket = "raw"
        key = f"crawls/{datetime.datetime.now(datetime.timezone.utc).strftime('%Y/%m/%d')}/{document_id}.json"
        raw_payload = {
            "url": url,
            "html": raw_html,
            "crawled_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        raw_payload_ref = storage_client.upload_raw_payload(bucket, key, raw_payload)
        
        # 4. Save crawled Document record
        content_hash = compute_hash(body_text)
        db_doc = Document(
            id=document_id,
            job_id=job_id,
            url=url,
            title=title,
            body_text=body_text,
            content_hash=content_hash,
            raw_payload_ref=raw_payload_ref,
            mime_type=mime_type,
            crawled_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(db_doc)
        db.commit()
        
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(f"CRAWLER_TASK  COMPLETED  url={url}  doc_id={document_id}  elapsed={elapsed_ms:.2f}ms")
        
        return {
            "success": True,
            "status": "crawled",
            "document_id": document_id,
            "title": title,
            "content_hash": content_hash
        }
        
    except Exception as exc:
        db.rollback()
        logger.error(f"CRAWLER_TASK  ERROR  url={url}  error='{exc}'", exc_info=True)
        return {
            "success": False,
            "status": "failed",
            "reason": str(exc),
            "document_id": None
        }
    finally:
        db.close()
