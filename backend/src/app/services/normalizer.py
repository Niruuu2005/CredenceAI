import datetime
import logging
import time
from typing import Dict, Any, List
import uuid

logger = logging.getLogger(__name__)


def normalize_searxng_payload(
    raw_payload: Dict[str, Any],
    job_id: str,
    raw_payload_ref: str = None,
) -> List[Dict[str, Any]]:
    """Map raw SearXNG results to common normalised schema. Logs each item outcome."""
    t0 = time.perf_counter()
    results = raw_payload.get("results", [])
    n_input = len(results)
    normalized = []
    dropped = 0

    for i, r in enumerate(results):
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()

        if not title or not url:
            dropped += 1
            logger.warning(
                f"NORMALISER  STATUS=DROPPED  "
                f"job_id={job_id}  "
                f"index={i}  "
                f"reason={'missing_title' if not title else 'missing_url'}  "
                f"raw_keys={list(r.keys())}"
            )
            continue

        snippet = r.get("content", r.get("snippet", "")).strip()
        source = r.get("engine", "searxng")

        item = {
            "id": f"res_{uuid.uuid4().hex[:12]}",
            "job_id": job_id,
            "title": title,
            "url": url,
            "canonical_url": url,
            "snippet": snippet,
            "source": source,
            "language": "en",
            "published_at": None,
            "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "raw_payload_ref": raw_payload_ref,
        }
        normalized.append(item)

        logger.debug(
            f"NORMALISER  STATUS=MAPPED  "
            f"job_id={job_id}  "
            f"result_id={item['id']}  "
            f"source={source}  "
            f"title='{title[:50]}'  "
            f"url='{url[:80]}'"
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_fn = logger.info if dropped == 0 else logger.warning
    log_fn(
        f"NORMALISER  STATUS=DONE  "
        f"job_id={job_id}  "
        f"input={n_input}  "
        f"normalised={len(normalized)}  "
        f"dropped={dropped}  "
        f"elapsed={elapsed_ms:.2f}ms"
    )
    return normalized
