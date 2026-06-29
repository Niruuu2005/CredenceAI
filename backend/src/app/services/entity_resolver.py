import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.wikipedia_client import WikipediaClient
from app.services.wikidata_client import WikidataClient
import app.services.repository as repo

logger = logging.getLogger(__name__)

# Words to ignore when extracting proper noun entity candidates
IGNORE_WORDS = {
    "The", "A", "An", "In", "On", "At", "By", "For", "With", "About", "Against",
    "Between", "Into", "Through", "During", "Before", "After", "Above", "Below",
    "To", "Of", "From", "And", "Or", "But", "This", "That", "These", "Those",
    "He", "She", "It", "They", "We", "I", "You", "Who", "What", "When", "Where",
    "Why", "How", "Is", "Are", "Was", "Were", "Be", "Been", "Being", "Have",
    "Has", "Had", "Do", "Does", "Did", "Will", "Would", "Shall", "Should",
    "Can", "Could", "May", "Might", "Must", "Not", "If", "Then", "Else", "Here"
}

# Time words or sentence starters to strip from the beginning of proper noun sequences
IGNORE_STARTER_WORDS = {
    "Yesterday", "Today", "Tomorrow", "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday", "January", "February", "March", "April", "May",
    "June", "July", "August", "September", "October", "November", "December",
    "Last", "Next", "This", "These", "Those", "Every", "Many", "Some", "All",
    "Here", "There", "Now", "Then", "When", "Where", "Why", "How", "Also", "Thus",
    "Therefore"
}

class EntityResolver:
    def __init__(self, db: Session):
        self.db = db
        self.wiki_client = WikipediaClient()
        self.wikidata_client = WikidataClient()

    def extract_candidates(self, text: str) -> List[str]:
        """Extract capitalized proper nouns from text and clean leading sentence starters."""
        if not text:
            return []

        # Matches sequences of 1-4 capitalized words
        pattern = r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b'
        matches = re.findall(pattern, text)
        
        candidates = []
        for m in matches:
            m = m.strip()
            words = m.split()
            
            # Clean leading ignored/starter words (e.g. "Yesterday Elon Musk" -> "Elon Musk")
            while words and (words[0] in IGNORE_WORDS or words[0] in IGNORE_STARTER_WORDS):
                words.pop(0)
                
            if not words:
                continue
                
            m_cleaned = " ".join(words)
            if len(m_cleaned) <= 2:
                continue
                
            # Skip if any of the remaining words are standard ignore words
            if any(w in IGNORE_WORDS for w in words):
                continue
                
            candidates.append(m_cleaned)
            
        unique_candidates = []
        for c in candidates:
            if c not in unique_candidates:
                unique_candidates.append(c)
                
        return unique_candidates[:4]

    def calculate_match_confidence(self, candidate: str, label: str, description: str, snippet: str) -> float:
        """Calculate similarity confidence score between mention and entity label/metadata."""
        if not candidate or not label:
            return 0.0

        c_lower = candidate.lower()
        l_lower = label.lower()

        if c_lower == l_lower:
            confidence = 0.95
        elif c_lower in l_lower or l_lower in c_lower:
            confidence = 0.85
        else:
            c_words = set(c_lower.split())
            l_words = set(l_lower.split())
            intersection = c_words.intersection(l_words)
            union = c_words.union(l_words)
            confidence = len(intersection) / len(union) if union else 0.0

        if confidence > 0.0 and description and snippet:
            desc_words = set(re.sub(r'[^\w\s]', '', description.lower()).split())
            snip_words = set(re.sub(r'[^\w\s]', '', snippet.lower()).split())
            desc_words = {w for w in desc_words if len(w) > 3}
            snip_words = {w for w in snip_words if len(w) > 3}
            overlap = desc_words.intersection(snip_words)
            if overlap:
                boost = min(0.05, len(overlap) * 0.01)
                confidence = min(1.0, confidence + boost)

        return round(confidence, 2)

    def resolve_and_link_entities(self, result_id: str, title: str, snippet: str) -> List[Dict[str, Any]]:
        """Link search result mentions to Wikidata/Wikipedia canonical profiles."""
        full_text = f"{title} {snippet}"
        candidates = self.extract_candidates(full_text)
        
        resolved_links = []
        
        for mention in candidates:
            search_results = self.wikidata_client.search_entities(mention, limit=3)
            if not search_results:
                continue

            top_match = search_results[0]
            label = top_match["canonical_name"]
            wikidata_id = top_match["wikidata_id"]
            description = top_match.get("description", "")
            
            confidence = self.calculate_match_confidence(mention, label, description, snippet)
            
            if confidence >= 0.85:
                entity = repo.get_entity_by_wikidata_id(self.db, wikidata_id)
                if not entity:
                    wiki_url = None
                    if self.wiki_client.enabled:
                        wiki_summary = self.wiki_client.get_page_summary(label)
                        if wiki_summary:
                            wiki_url = wiki_summary.get("wikipedia_url")

                    details = self.wikidata_client.get_entity_details(wikidata_id)
                    aliases = details.get("aliases", []) if details else []

                    entity_id = f"ent_{uuid.uuid4().hex[:12]}"
                    entity = repo.create_entity(
                        db=self.db,
                        entity_id=entity_id,
                        canonical_name=label,
                        entity_type=top_match.get("entity_type"),
                        description=description or (details.get("description") if details else None),
                        wikidata_id=wikidata_id,
                        wikipedia_url=wiki_url or top_match.get("wikidata_url")
                    )
                    
                    for alias in aliases:
                        repo.create_entity_alias(
                            db=self.db,
                            alias_id=f"alias_{uuid.uuid4().hex[:12]}",
                            entity_id=entity.id,
                            alias=alias,
                            source="wikidata",
                            confidence=0.90
                        )
                
                link_id = f"link_{uuid.uuid4().hex[:12]}"
                repo.create_entity_link(
                    db=self.db,
                    link_id=link_id,
                    entity_id=entity.id,
                    result_id=result_id,
                    mention=mention,
                    confidence=confidence,
                    decision="accept"
                )
                
                resolved_links.append({
                    "entity_id": entity.id,
                    "canonical_name": entity.canonical_name,
                    "wikidata_id": entity.wikidata_id,
                    "confidence": confidence,
                    "mention": mention
                })
                
                logger.info(
                    f"ENTITY_RESOLVER  resolved_mention='{mention}'  "
                    f"-> entity='{entity.canonical_name}'  "
                    f"confidence={confidence:.2f}"
                )
                
        return resolved_links
