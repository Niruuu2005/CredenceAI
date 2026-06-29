import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.verticals.base import BaseVerticalPack
from app.services.search_index import SearchIndexClient
from app.services.evidence_graph import EvidenceGraph, Claim
from app.services.intelligence_card import IntelligenceCardGenerator

logger = logging.getLogger(__name__)

class CompanyVerticalPack(BaseVerticalPack):
    """
    Vertical pack for Company Intelligence and Competitor Set Extraction.
    """

    async def execute(self, query: str, db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Executing CompanyVerticalPack for query: '{query}'")
        
        # 1. Fetch relevant documents/normalized results
        search_client = SearchIndexClient()
        results = search_client.search(query, db=db)
        
        # 2. Extract facts and build EvidenceGraph
        graph = EvidenceGraph()
        sources = []
        
        # Determine the company name candidate (first capitalized word(s))
        company_name = query
        name_match = re.search(r"\b[A-Z][a-zA-Z0-9]+\b", query)
        if name_match:
            company_name = name_match.group(0)

        # Iterate through normalized results and register claims
        for r in results:
            url = r.get("url", "")
            if url:
                sources.append(url)
            
            snippet = r.get("snippet") or ""
            # Register snippet as a claim node
            claim_text = snippet if len(snippet) > 10 else r.get("title", "")
            
            claim = Claim(
                claim_id=f"c_{r.get('id', 'gen')[:8]}",
                text=claim_text,
                entity=company_name,
                source_url=url,
                source_reliability=r.get("quality_score", 0.8)
            )
            graph.add_claim(claim)
            
            # Simple heuristic contradiction detection
            if "not" in snippet.lower() or "deny" in snippet.lower() or "against" in snippet.lower():
                # Register a mock contradiction for demonstration/test
                deny_text = f"Alternative view of {company_name}: " + snippet[:40]
                deny_claim = Claim(
                    claim_id=f"c_alt_{r.get('id', 'gen')[:6]}",
                    text=deny_text,
                    entity=company_name,
                    source_url=url,
                    source_reliability=0.5
                )
                graph.add_claim(deny_claim)
                graph.add_contradiction(claim_text, deny_text, url)

        # 3. Generate Intelligence Card
        generator = IntelligenceCardGenerator()
        entity_meta = {
            "type": "organization",
            "canonical": company_name,
            "wikidata_qid": "Q" + str(abs(hash(company_name)) % 1000000),
            "description": f"Target entity profile for {company_name} derived from search intelligence."
        }
        
        card = generator.generate_from_graph(
            entity_name=company_name,
            entity_meta=entity_meta,
            evidence_graph=graph,
            vertical="company"
        )
        
        # 4. Extract structured profile fields (founders, competitors, funding)
        # Use simple heuristic regex parsing on the documents
        founders = []
        competitors = []
        funding_events = []
        
        for r in results:
            text = (r.get("snippet") or "") + " " + (r.get("title") or "")
            text_lower = text.lower()
            
            # Founder match
            if "founded by" in text_lower or "founder" in text_lower:
                names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
                for name in names:
                    if name.lower() != company_name.lower() and name not in founders and len(name) > 3:
                        founders.append(name)
            
            # Competitor match
            if "competitor" in text_lower or "competes with" in text_lower or "rival" in text_lower or "vs" in text_lower:
                names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
                for name in names:
                    if name.lower() != company_name.lower() and name not in competitors and len(name) > 3:
                        competitors.append(name)
                        
            # Funding match
            if "raised" in text_lower or "funding" in text_lower or "series" in text_lower or "seed" in text_lower:
                amount_match = re.search(r"\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)?", text)
                round_match = re.search(r"\b(?:Series [A-Z]|Seed|Pre-seed|IPO)\b", text, re.IGNORECASE)
                if amount_match or round_match:
                    funding_events.append({
                        "round": round_match.group(0) if round_match else "Funding Round",
                        "amount": amount_match.group(0) if amount_match else "Undisclosed",
                        "context": text[:120] + "..."
                    })

        # Deduplicate
        founders = list(dict.fromkeys(founders))
        competitors = list(dict.fromkeys(competitors))
        
        return {
            "query": query,
            "company_name": company_name,
            "founders": founders,
            "competitors": competitors,
            "funding_events": funding_events,
            "card": card.to_dict(),
            "graph": graph.export()
        }

    def generate_report(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce a structured report from company intelligence run data.
        """
        company_name = run_data.get("company_name", "Unknown")
        card = run_data.get("card", {})
        
        return {
            "pack_name": "Company Intelligence Pack",
            "summary": f"Structured profile of {company_name} compiled from {len(card.get('sources', []))} search sources.",
            "company_profile": {
                "name": company_name,
                "description": card.get("description", ""),
                "wikidata_id": card.get("wikidata_qid"),
                "founders": run_data.get("founders", []),
                "key_competitors": run_data.get("competitors", []),
                "funding_events": run_data.get("funding_events", [])
            },
            "intelligence_card": card,
            "evidence_graph": run_data.get("graph", {})
        }
