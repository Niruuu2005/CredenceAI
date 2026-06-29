import logging
from typing import Optional, List, Dict, Any
from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import NormalizedResult, DedupGroup, DedupMember

logger = logging.getLogger(__name__)

STOPWORDS = {
    "is", "are", "was", "were", "am", "be", "been", "being", "the", "a", "an", "and", 
    "or", "but", "if", "then", "of", "at", "by", "for", "with", "about", "to", "in", 
    "on", "it", "its", "this", "that", "these", "those", "they", "them", "their", 
    "he", "him", "his", "she", "her", "hers", "you", "your", "yours", "we", "us", "our", "ours"
}

_opensearch_available = None
_cached_opensearch_client = None

class SearchIndexClient:
    def __init__(self):
        global _opensearch_available, _cached_opensearch_client
        self.url = settings.OPENSEARCH_URL
        self.index_name = "credence-results"
        
        if _opensearch_available is None:
            if settings.MOCK_SERVICES:
                _opensearch_available = False
                _cached_opensearch_client = None
                logger.info("MOCK_SERVICES enabled. Search index client falling back to database index instantly.")
            else:
                try:
                    client = OpenSearch(
                        hosts=[self.url],
                        http_compress=True,
                        use_ssl=False,
                        verify_certs=False,
                        timeout=1.0,
                        max_retries=0
                    )
                    client.ping()
                    _cached_opensearch_client = client
                    _opensearch_available = True
                    logger.info("OpenSearch client connected successfully")
                    
                    if not client.indices.exists(index=self.index_name):
                        client.indices.create(
                            index=self.index_name,
                            body={
                                "settings": {
                                    "index": {
                                        "number_of_shards": 1,
                                        "number_of_replicas": 0
                                    }
                                },
                                "mappings": {
                                    "properties": {
                                        "title": {"type": "text"},
                                        "url": {"type": "keyword"},
                                        "snippet": {"type": "text"},
                                        "source": {"type": "keyword"},
                                        "job_id": {"type": "keyword"},
                                        "quality_score": {"type": "float"},
                                        "decision": {"type": "keyword"}
                                    }
                                }
                            }
                        )
                except Exception as e:
                    logger.warning(f"OpenSearch connection failed ({e}). Falling back to metadata database search index.")
                    _opensearch_available = False
                    _cached_opensearch_client = None
                
        self.use_opensearch = _opensearch_available
        self.client = _cached_opensearch_client
 
    def index_normalized_result(self, res: dict):
        """Indexes a normalized result item in OpenSearch or database fallback."""
        if self.use_opensearch and self.client:
            try:
                self.client.index(
                    index=self.index_name,
                    id=res["id"],
                    body={
                        "title": res["title"],
                        "url": res["url"],
                        "snippet": res["snippet"],
                        "source": res["source"],
                        "job_id": res["job_id"],
                        "quality_score": res.get("quality_score", 1.0),
                        "decision": res.get("decision", "accept")
                    },
                    refresh=True
                )
                logger.info(f"Indexed result {res['id']} in OpenSearch")
                return
            except OpenSearchException as e:
                logger.error(f"OpenSearch indexing failed: {e}")
        
        logger.info(f"Using database fallback indexing for result {res['id']}")

    def search(self, query: str, db: Optional[Session] = None, limit: Optional[int] = None) -> list:
        """Searches the index. Returns list of normalized results matching the query."""
        if self.use_opensearch and self.client:
            try:
                search_query = {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "snippet"]
                        }
                    }
                }
                response = self.client.search(
                    index=self.index_name,
                    body=search_query,
                    size=limit if limit is not None else 10
                )
                hits = response["hits"]["hits"]
                results = []
                for hit in hits:
                    source = hit["_source"]
                    q_score = source.get("quality_score", 1.0)
                    results.append({
                        "id": hit["_id"],
                        "title": source["title"],
                        "url": source["url"],
                        "snippet": source["snippet"],
                        "source": source["source"],
                        "quality_score": q_score,
                        "decision": source.get("decision", "accept"),
                        "ranking_details": {
                            "base_score": round(q_score, 4),
                            "jaccard_similarity": 0.0,
                            "phrase_boost": 0.0,
                            "final_score": round(q_score, 4),
                            "formula": "base_score (lexical quality)"
                        }
                    })
                return results
            except OpenSearchException as e:
                logger.error(f"OpenSearch search failed: {e}. Falling back to database lookup.")

        logger.info(f"Executing database query fallback for search term: '{query}'")
        session = db or SessionLocal()
        close_session = (db is None)
        try:
            from sqlalchemy import or_
            words = [w.strip().lower() for w in query.split() if len(w.strip()) > 1]
            filtered_words = [w for w in words if w not in STOPWORDS]
            search_words = filtered_words if filtered_words else words

            filters = []
            for w in search_words:
                filters.append(NormalizedResult.title.ilike(f"%{w}%"))
                filters.append(NormalizedResult.snippet.ilike(f"%{w}%"))
            
            if filters:
                db_results = session.query(NormalizedResult).filter(or_(*filters)).all()
                # Sort results by the number of matching keywords
                scored_results = []
                for r in db_results:
                    title_lower = (r.title or "").lower()
                    snippet_lower = (r.snippet or "").lower()
                    matches = sum(1 for w in search_words if w in title_lower or w in snippet_lower)
                    scored_results.append((matches, r))
                scored_results.sort(key=lambda x: x[0], reverse=True)
                db_results = [r for matches, r in scored_results]
            else:
                q_filter = f"%{query}%"
                db_results = session.query(NormalizedResult).filter(
                    (NormalizedResult.title.ilike(q_filter)) | 
                    (NormalizedResult.snippet.ilike(q_filter))
                ).all()
            
            results = []
            for r in db_results:
                is_duplicate = session.query(DedupMember).filter(DedupMember.result_id == r.id).first() is not None
                if is_duplicate:
                    continue

                q_score = 1.0
                decision = "accept"
                if r.quality_scores:
                    q_score = r.quality_scores.final_trust_score
                    decision = r.quality_scores.decision

                duplicates = []
                group = session.query(DedupGroup).filter(DedupGroup.canonical_result_id == r.id).first()
                if group:
                    for member in group.members:
                        m_res = session.query(NormalizedResult).filter(NormalizedResult.id == member.result_id).first()
                        if m_res:
                            duplicates.append({
                                "id": m_res.id,
                                "title": m_res.title,
                                "url": m_res.url,
                                "snippet": m_res.snippet,
                                "source": m_res.source,
                                "match_type": member.match_type,
                                "confidence": member.confidence
                            })

                entities = []
                for link in r.entity_links:
                    ent = link.entity
                    if ent:
                        entities.append({
                            "id": ent.id,
                            "canonical_name": ent.canonical_name,
                            "entity_type": ent.entity_type,
                            "description": ent.description,
                            "wikidata_id": ent.wikidata_id,
                            "wikipedia_url": ent.wikipedia_url,
                            "confidence": link.confidence,
                            "mention": link.mention
                        })

                results.append({
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source,
                    "quality_score": q_score,
                    "decision": decision,
                    "duplicates": duplicates,
                    "entities": entities,
                    "ranking_details": {
                        "base_score": round(q_score, 4),
                        "jaccard_similarity": 0.0,
                        "phrase_boost": 0.0,
                        "final_score": round(q_score, 4),
                        "formula": "base_score (lexical quality)"
                    }
                })
                if limit is not None and len(results) >= limit:
                    break
            return results
        finally:
            if close_session:
                session.close()

    def hybrid_search(
        self,
        query: str,
        db: Optional[Session] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a BM25 + Semantic/Vector hybrid search.
        Combines keyword matching with semantic similarity and filters.
        """
        # Step 1: Keyword search (BM25 fallback)
        candidate_limit = max(50, limit * 5) if limit is not None else None
        candidates = self.search(query, db, limit=candidate_limit)
        
        # Step 2: Apply semantic scores (fallback cosine) & metadata filters
        hybrid_results = []
        query_words = set(query.lower().split())

        for cand in candidates:
            # Metadata filters
            if filters:
                matched = True
                for key, val in filters.items():
                    if cand.get(key) != val:
                        matched = False
                        break
                if not matched:
                    continue

            # Semantic match scoring
            title = (cand.get("title") or "").lower()
            snippet = (cand.get("snippet") or "").lower()
            title_words = set(title.split())
            snippet_words = set(snippet.split())
            doc_words = title_words.union(snippet_words)
            
            jaccard = len(query_words.intersection(doc_words)) / len(query_words.union(doc_words)) if query_words else 0.0
            
            phrase_boost = 0.0
            if query.lower() in title or query.lower() in snippet:
                phrase_boost = 0.3
            
            # Combine scores (0.4 keyword BM25/trust score + 0.6 semantic score)
            base_score = cand.get("quality_score", 0.5)
            hybrid_score = round(0.4 * base_score + 0.6 * jaccard, 4)
            
            cand_copy = dict(cand)
            cand_copy["quality_score"] = hybrid_score
            cand_copy["hybrid_score"] = hybrid_score
            cand_copy["ranking_details"] = {
                "base_score": round(base_score, 4),
                "jaccard_similarity": round(jaccard, 4),
                "phrase_boost": round(phrase_boost, 4),
                "final_score": round(hybrid_score, 4),
                "formula": "0.4 * base_score + 0.6 * jaccard_similarity"
            }
            hybrid_results.append(cand_copy)

        # Sort by hybrid score descending
        hybrid_results.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
        if limit is not None:
            hybrid_results = hybrid_results[:limit]
        return hybrid_results
