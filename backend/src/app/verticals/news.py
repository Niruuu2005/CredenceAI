import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.verticals.base import BaseVerticalPack
from app.services.search_index import SearchIndexClient
from app.services.evidence_graph import EvidenceGraph, Claim
from app.services.intelligence_card import IntelligenceCardGenerator

logger = logging.getLogger(__name__)

class NewsMonitoringPack(BaseVerticalPack):
    """
    Vertical pack for News Monitoring, Event Detection, and Timeline Evolution.
    """

    async def execute(self, query: str, db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Executing NewsMonitoringPack for query: '{query}'")
        
        # 1. Fetch relevant results from search index
        search_client = SearchIndexClient()
        results = search_client.search(query, db=db)
        
        # 2. Extract news sources, events, timeline
        timeline = []
        sources = set()
        domains = []
        events = []
        graph = EvidenceGraph()
        
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet") or ""
            url = r.get("url", "")
            
            # Extract domain
            domain = urlparse(url).netloc if url else "unknown"
            if domain:
                domains.append(domain)
                sources.add(domain)
                
            # Heuristically parse date or timeline marker
            date_str = None
            date_match = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s+\d{4})?\b", snippet + " " + title)
            if date_match:
                date_str = date_match.group(0)
            else:
                date_match_alt = re.search(r"\b\d{4}-\d{2}-\d{2}\b", snippet)
                if date_match_alt:
                    date_str = date_match_alt.group(0)
            
            # Event detection (heuristically extract key claims/announcements)
            event_text = None
            if any(term in snippet.lower() for term in ["announce", "launch", "release", "declare", "resign", "acquired", "merge"]):
                event_text = snippet[:80] + "..." if len(snippet) > 80 else snippet
                events.append({
                    "event": event_text,
                    "source": domain,
                    "url": url
                })
                
            timeline_item = {
                "date": date_str or "Recent",
                "title": title,
                "domain": domain,
                "url": url,
                "event_highlight": event_text
            }
            timeline.append(timeline_item)
            
            # Register in evidence graph
            claim_text = f"News update from {domain}: {title}"
            claim = Claim(
                claim_id=f"news_{r.get('id', 'gen')[:8]}",
                text=claim_text,
                entity="Current Event",
                source_url=url,
                source_reliability=0.75
            )
            graph.add_claim(claim)

        # Generate Intelligence Card for the News vertical
        generator = IntelligenceCardGenerator()
        entity_meta = {
            "type": "event_stream",
            "canonical": query,
            "description": f"Real-time news feed monitoring and timeline compilation for: '{query}'."
        }
        
        card = generator.generate_from_graph(
            entity_name=query,
            entity_meta=entity_meta,
            evidence_graph=graph,
            vertical="news"
        )
        
        # Calculate source diversity score
        diversity_score = len(sources) / len(results) if results else 0.0
        
        return {
            "query": query,
            "timeline": timeline,
            "diversity_score": round(diversity_score, 4),
            "unique_sources": list(sources),
            "detected_events": events,
            "card": card.to_dict(),
            "graph": graph.export()
        }

    def generate_report(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        query = run_data.get("query", "News Query")
        card = run_data.get("card", {})
        
        return {
            "pack_name": "News Monitoring Pack",
            "summary": f"News timeline and analysis report for '{query}' tracking {len(run_data.get('unique_sources', []))} unique sources.",
            "metrics": {
                "total_articles": len(run_data.get("timeline", [])),
                "source_diversity_index": run_data.get("diversity_score", 0.0),
                "unique_domains": run_data.get("unique_sources", [])
            },
            "timeline": run_data.get("timeline", []),
            "detected_key_events": run_data.get("detected_events", []),
            "intelligence_card": card,
            "evidence_graph": run_data.get("graph", {})
        }
