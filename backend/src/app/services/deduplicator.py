import uuid
import logging
from typing import List, Dict, Any, Tuple
from app.services.url_canonicalizer import URLCanonicalizer

logger = logging.getLogger(__name__)

class DeduplicationService:
    def __init__(self, jaccard_threshold: float = 0.75):
        self.jaccard_threshold = jaccard_threshold

    def calculate_string_similarity(self, text1: str, text2: str) -> float:
        """Calculate word-level Jaccard similarity between two texts after stripping punctuation and plurals."""
        if not text1 or not text2:
            return 0.0
            
        import re
        # Strip punctuation
        t1 = re.sub(r'[^\w\s]', '', text1.lower())
        t2 = re.sub(r'[^\w\s]', '', text2.lower())
        
        # Normalize simple plurals to improve match accuracy (e.g. recalls -> recall, systems -> system)
        words1 = {w.rstrip('s') if len(w) > 3 and w.endswith('s') else w for w in t1.split()}
        words2 = {w.rstrip('s') if len(w) > 3 and w.endswith('s') else w for w in t2.split()}
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def group_duplicates(self, scored_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes list of normalized scored results.
        Returns:
            - unique_results: results that represent canonical entries.
            - db_groups: list of dicts describing the groups and members for database storage.
        """
        # First: Canonicalize all URLs in place
        for item in scored_results:
            item["canonical_url"] = URLCanonicalizer.canonicalize(item.get("url", ""))

        # To decide which item is the canonical one: sort by composite trust score descending
        sorted_items = sorted(scored_results, key=lambda x: x.get("quality_scores", {}).get("final_trust_score", 0.0), reverse=True)
        
        groups: Dict[str, List[Dict[str, Any]]] = {}
        unique_results: List[Dict[str, Any]] = []
        
        for item in sorted_items:
            item_id = item["id"]
            item_url = item["canonical_url"]
            item_text = (item.get("title", "") + " " + item.get("snippet", "")).strip()
            
            matched_canonical_id = None
            match_type = None
            match_confidence = 1.0
            
            for u_res in unique_results:
                u_id = u_res["id"]
                u_url = u_res["canonical_url"]
                u_text = (u_res.get("title", "") + " " + u_res.get("snippet", "")).strip()
                
                # 1. Exact URL match
                if item_url == u_url:
                    matched_canonical_id = u_id
                    match_type = "exact_url"
                    match_confidence = 1.0
                    break
                
                # 2. Near-duplicate content match (Jaccard similarity on Title + Snippet)
                sim = self.calculate_string_similarity(item_text, u_text)
                if sim >= self.jaccard_threshold:
                    matched_canonical_id = u_id
                    match_type = "near_duplicate"
                    match_confidence = round(sim, 2)
                    break
            
            if matched_canonical_id:
                if matched_canonical_id not in groups:
                    groups[matched_canonical_id] = []
                groups[matched_canonical_id].append({
                    "id": item_id,
                    "match_type": match_type,
                    "confidence": match_confidence
                })
                item["duplicate_of"] = matched_canonical_id
            else:
                unique_results.append(item)
                item["duplicate_of"] = None

        db_groups = []
        for canonical_id, members in groups.items():
            canonical_item = next(x for x in unique_results if x["id"] == canonical_id)
            group_id = f"group_{uuid.uuid4().hex[:12]}"
            
            db_groups.append({
                "group_id": group_id,
                "canonical_result_id": canonical_id,
                "canonical_url": canonical_item["canonical_url"],
                "group_type": "url_or_content",
                "members": [
                    {
                        "result_id": m["id"],
                        "match_type": m["match_type"],
                        "confidence": m["confidence"]
                    } for m in members
                ]
            })
            
            canonical_item["dedup_group_id"] = group_id
            for m in members:
                m_item = next(x for x in sorted_items if x["id"] == m["id"])
                m_item["dedup_group_id"] = group_id
                
        for item in scored_results:
            if "dedup_group_id" not in item:
                item["dedup_group_id"] = None
            if item.get("duplicate_of") is None:
                item["quality_scores"]["dedup_confidence"] = 1.0
            else:
                member_details = next((m for g in db_groups for m in g["members"] if m["result_id"] == item["id"]), None)
                conf = member_details["confidence"] if member_details else 0.5
                item["quality_scores"]["dedup_confidence"] = conf

        logger.info(
            f"DEDUP  input_results={len(scored_results)}  "
            f"unique={len(unique_results)}  "
            f"groups={len(db_groups)}"
        )
        
        return unique_results, db_groups
