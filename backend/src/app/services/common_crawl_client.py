"""
Common Crawl Client for CredenceAI Iteration 0.3

Queries Common Crawl CDX index servers to find historical archives of URLs,
fetching records via HTTP range queries to avoid live crawler fetches.
"""

import logging
import requests
import json
import gzip
import io
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class CommonCrawlClient:
    """
    Client interface for querying CDX indexes and fetching compressed WARC pages.
    """

    def __init__(self):
        # We target a stable public index partition
        self.cdx_index = "CC-MAIN-2023-50-index"
        self.cdx_base_url = f"https://index.commoncrawl.org/{self.cdx_index}"
        self.mock_mode = settings.MOCK_SERVICES

    def lookup_index(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Query the CDX server to see if a historical crawl record exists.
        """
        if self.mock_mode:
            logger.info(f"COMMON_CRAWL  MOCK_LOOKUP  url={url}")
            if "fail" in url.lower() or "error" in url.lower():
                return None
            return {
                "warc_filename": "crawl-data/CC-MAIN-2023-50/segments/1700/warc/CC-MAIN-2023.warc.gz",
                "offset": "5000",
                "length": "1200",
                "status": "200",
                "mime": "text/html"
            }

        query_url = f"{self.cdx_base_url}?url={url}&output=json&limit=1"
        try:
            resp = requests.get(query_url, timeout=10)
            if resp.status_code == 200:
                # CDX returns JSON lines. Read the first line
                lines = resp.text.strip().split("\n")
                if lines and lines[0]:
                    record = json.loads(lines[0])
                    logger.info(f"COMMON_CRAWL  RECORD_FOUND  url={url}  offset={record.get('offset')}")
                    return record
            return None
        except Exception as e:
            logger.error(f"COMMON_CRAWL  INDEX_LOOKUP_FAILED  url={url}  error='{e}'")
            return None

    def fetch_warc_record(self, warc_filename: str, offset: int, length: int) -> str:
        """
        Download the compressed WARC segment using HTTP Range headers,
        decompress the payload, and return raw html.
        """
        if self.mock_mode:
            return "<html><head><title>Common Crawl Mock Page</title></head><body><h1>CC Archive</h1><p>Mocked historical content fetched from Common Crawl archive</p></body></html>"

        target_url = f"https://data.commoncrawl.org/{warc_filename}"
        headers = {"Range": f"bytes={offset}-{offset + length - 1}"}
        
        try:
            resp = requests.get(target_url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            # Decompress Gzip data
            compressed_file = io.BytesIO(resp.content)
            decompressed_file = gzip.GzipFile(fileobj=compressed_file)
            warc_data = decompressed_file.read()
            
            # WARC records contain headers and then the HTTP payload.
            # We locate the double carriage-return that starts the HTML body.
            parts = warc_data.split(b"\r\n\r\n")
            
            # Find the html segment among split parts (usually the last index)
            for part in reversed(parts):
                if b"<html" in part.lower() or b"<!doctype" in part.lower():
                    return part.decode("utf-8", errors="ignore")
                    
            # Fallback to direct decoding of last segment
            if len(parts) >= 2:
                return parts[-1].decode("utf-8", errors="ignore")
                
            return warc_data.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"COMMON_CRAWL  WARC_FETCH_FAILED  file={warc_filename}  error='{e}'")
            raise RuntimeError(f"Failed to fetch Common Crawl WARC: {str(e)}") from e

    def fetch_historical_page(self, url: str) -> Optional[str]:
        """
        End-to-end wrapper: check index and retrieve archived HTML.
        Returns None if not archived.
        """
        record = self.lookup_index(url)
        if not record:
            logger.info(f"COMMON_CRAWL  NO_ARCHIVE  url={url}")
            return None
            
        try:
            warc_filename = record["warc_filename"]
            offset = int(record["offset"])
            length = int(record["length"])
            
            html = self.fetch_warc_record(warc_filename, offset, length)
            return html
        except Exception as e:
            logger.warning(f"COMMON_CRAWL  FETCH_FLOW_ERROR  url={url}  error='{e}'")
            return None
