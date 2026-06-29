import re
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Vertical keywords map
SCHOLARLY_KEYWORDS = [
    "paper", "scholarly", "journal", "arxiv", "preprint",
    "pmid", "doi", "research article", "citation", "author"
]
NEWS_KEYWORDS = [
    "news", "latest", "recent", "headlines", "breaking",
    "monitoring", "alert", "today", "update"
]
ENTITY_PREFIXES = ["who is", "what is", "where is", "profile of", "lookup"]

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)


def classify_intent(query_text: str) -> Dict[str, Any]:
    """Classifies query intent and vertical. Logs every classification decision."""
    t0 = time.perf_counter()
    query_lower = query_text.lower().strip()

    intent = "search_query"
    vertical = "web"
    requires_freshness = False
    requires_crawling = False
    requires_entity_resolution = False
    entities: List[str] = []
    matched_rule = "default -> general web search"

    # ── Rule 1: Scholarly ────────────────────────────────────────────────
    if DOI_PATTERN.search(query_text) or any(k in query_lower for k in SCHOLARLY_KEYWORDS):
        intent = "scholarly_search"
        vertical = "research"
        requires_crawling = True
        kw = next((k for k in SCHOLARLY_KEYWORDS if k in query_lower), "doi-pattern")
        matched_rule = f"scholarly keyword='{kw}'"

    # ── Rule 2: News ─────────────────────────────────────────────────────
    elif any(k in query_lower for k in NEWS_KEYWORDS):
        intent = "news_monitoring"
        vertical = "news"
        requires_freshness = True
        kw = next(k for k in NEWS_KEYWORDS if k in query_lower)
        matched_rule = f"news keyword='{kw}'"

    # ── Rule 3: Entity prefix ────────────────────────────────────────────
    elif any(query_lower.startswith(prefix) for prefix in ENTITY_PREFIXES):
        intent = "entity_lookup"
        vertical = "entity"
        requires_entity_resolution = True
        prefix = next(p for p in ENTITY_PREFIXES if query_lower.startswith(p))
        words = query_text.split()
        if len(words) > 2:
            entities = [" ".join(words[2:])]
        matched_rule = f"entity prefix='{prefix}'"

    # ── Rule 4: Short Capitalised Title Case ─────────────────────────────
    elif len(query_text) > 3 and query_text[0].isupper():
        words = query_text.split()
        if 1 <= len(words) <= 3 and all(w[0].isupper() for w in words if w.isalpha()):
            intent = "entity_lookup"
            vertical = "entity"
            requires_entity_resolution = True
            entities = [query_text]
            matched_rule = f"title-case entity='{query_text}'"

    elapsed_ms = (time.perf_counter() - t0) * 1000

    logger.info(
        f"INTENT_CLASSIFY  query='{query_text[:60]}'  "
        f"-> intent={intent}  vertical={vertical}  "
        f"rule=[{matched_rule}]  "
        f"freshness={requires_freshness}  crawl={requires_crawling}  "
        f"entities={entities}  elapsed={elapsed_ms:.2f}ms"
    )

    return {
        "intent": intent,
        "vertical": vertical,
        "entities": entities,
        "requires_freshness": requires_freshness,
        "requires_crawling": requires_crawling,
        "requires_entity_resolution": requires_entity_resolution,
        "risk_level": "low",
        "language": "en",
    }
