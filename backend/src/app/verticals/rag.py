import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.verticals.base import BaseVerticalPack
from app.services.search_index import SearchIndexClient
from app.services.synthesis import SynthesisService
from app.services.evidence_graph import EvidenceGraph, Claim
from app.services.intelligence_card import IntelligenceCardGenerator

logger = logging.getLogger(__name__)

class RAGDatasetBuilderPack(BaseVerticalPack):
    """
    Vertical pack for Curated RAG Dataset Generation.
    """

    async def execute(self, query: str, db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Executing RAGDatasetBuilderPack for query: '{query}'")
        
        # 1. Fetch relevant results from search index
        search_client = SearchIndexClient()
        results = search_client.search(query, db=db)
        
        # 2. Quality Filtering & Deduplication
        filtered_docs = []
        rejected_count = 0
        accepted_count = 0
        
        for r in results:
            quality_score = r.get("quality_score", 1.0)
            decision = r.get("decision", "accept")
            
            # Filter threshold: decision must not be reject, quality_score >= 0.4
            if decision == "reject" or quality_score < 0.4:
                rejected_count += 1
                continue
                
            # Deduplicate by URL
            if any(doc["url"] == r.get("url") for doc in filtered_docs):
                continue
                
            accepted_count += 1
            
            # Optional Embeddings (Generate a lightweight mock embedding representation)
            # Create a deterministic mock vector based on the document ID hash
            mock_embedding = [
                round(float((hash(r.get("id", "")) + i * 37) % 1000) / 1000.0, 4)
                for i in range(16)
            ]
            
            filtered_docs.append({
                "id": r.get("id"),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "quality_score": quality_score,
                "embedding": mock_embedding
            })

        # 3. Generate a synthesized summary to serve as the reference response
        synthesis_docs = [
            {
                "title": doc["title"],
                "url": doc["url"],
                "snippet": doc["snippet"],
                "source": "rag_curator"
            }
            for doc in filtered_docs
        ]
        
        synthesis_service = SynthesisService()
        synthesis_out = await synthesis_service.synthesize(
            query=query,
            documents=synthesis_docs,
            vertical="rag"
        )
        reference_response = synthesis_out.summary

        # 4. Generate JSONL Export format
        jsonl_lines = []
        for idx, doc in enumerate(filtered_docs):
            line = {
                "id": doc["id"],
                "query": query,
                "document_title": doc["title"],
                "document_url": doc["url"],
                "document_text": doc["snippet"],
                "quality_score": doc["quality_score"],
                "embedding": doc["embedding"],
                "reference_response": reference_response
            }
            jsonl_lines.append(json.dumps(line))
            
        jsonl_content = "\n".join(jsonl_lines)

        # Generate Evidence Graph for structural completeness
        graph = EvidenceGraph()
        for doc in filtered_docs:
            claim = Claim(
                claim_id=f"rag_{doc['id'][:8]}",
                text=f"RAG Dataset curated document: {doc['title']}",
                entity="Dataset Entry",
                source_url=doc["url"],
                source_reliability=doc["quality_score"]
            )
            graph.add_claim(claim)
            
        generator = IntelligenceCardGenerator()
        entity_meta = {
            "type": "dataset_collection",
            "canonical": query,
            "description": f"Curated vector-ready context dataset for: '{query}'."
        }
        card = generator.generate_from_graph(
            entity_name=query,
            entity_meta=entity_meta,
            evidence_graph=graph,
            vertical="rag"
        )

        return {
            "query": query,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "filtered_documents": filtered_docs,
            "reference_response": reference_response,
            "jsonl_content": jsonl_content,
            "card": card.to_dict(),
            "graph": graph.export()
        }

    def generate_report(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        query = run_data.get("query", "Dataset Build")
        card = run_data.get("card", {})
        
        return {
            "pack_name": "RAG Dataset Builder Pack",
            "summary": f"Curated training dataset built for instruction '{query}'.",
            "metrics": {
                "accepted_documents": run_data.get("accepted_count", 0),
                "rejected_low_quality": run_data.get("rejected_count", 0)
            },
            "jsonl_export": run_data.get("jsonl_content", ""),
            "curated_documents": run_data.get("filtered_documents", []),
            "reference_response": run_data.get("reference_response", ""),
            "intelligence_card": card,
            "evidence_graph": run_data.get("graph", {})
        }
