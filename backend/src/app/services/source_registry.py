import urllib.parse
from typing import Dict

# Dictionary mapping specific trusted domains to their reliability score (0.0 to 1.0)
TRUSTED_DOMAINS: Dict[str, float] = {
    # Scholarly / Scientific Databases
    "openalex.org": 0.95,
    "crossref.org": 0.95,
    "arxiv.org": 0.95,
    "ncbi.nlm.nih.gov": 0.95,
    "nature.com": 0.95,
    "science.org": 0.95,
    "scholar.google.com": 0.95,
    
    # Official / Governmental / Reference
    "wikipedia.org": 0.90,
    "wikidata.org": 0.90,
    "w3.org": 0.90,
    
    # Trusted News Outlets
    "reuters.com": 0.88,
    "apnews.com": 0.88,
    "bbc.co.uk": 0.85,
    "bbc.com": 0.85,
    "nytimes.com": 0.85,
    "theguardian.com": 0.85,
    "bloomberg.com": 0.85,
    "ft.com": 0.85,
    "wsj.com": 0.85,
    "economist.com": 0.85,
}

# Domains that are untrusted / low value
UNTRUSTED_DOMAINS = {
    "twitter.com", "x.com", "facebook.com", "instagram.com", "reddit.com", "quora.com",
    "medium.com", "blogspot.com", "wordpress.com", "tumblr.com"
}

class SourceReliabilityRegistry:
    @staticmethod
    def get_reliability_score(url: str, default_source: str = "web") -> float:
        """Evaluate the reliability score of a URL domain."""
        if not url:
            return 0.5

        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            
            # Strip www.
            if netloc.startswith("www."):
                netloc = netloc[4:]
                
            # Direct match
            if netloc in TRUSTED_DOMAINS:
                return TRUSTED_DOMAINS[netloc]
                
            # Suffix/Subdomain match (e.g. en.wikipedia.org -> wikipedia.org)
            for domain, score in TRUSTED_DOMAINS.items():
                if netloc.endswith("." + domain):
                    return score
                    
            # Check for generic government or educational suffixes
            if (netloc.endswith(".gov") or 
                netloc.endswith(".edu") or 
                netloc.endswith(".gov.uk") or 
                netloc.endswith(".ac.uk")):
                return 0.90
                
            # Untrusted check
            if netloc in UNTRUSTED_DOMAINS or any(netloc.endswith("." + d) for d in UNTRUSTED_DOMAINS):
                return 0.40
                
        except Exception:
            pass

        # Source-based default weights
        source_defaults = {
            "searxng": 0.70,
            "wikidata": 0.90,
            "wikipedia": 0.90,
            "gdelt": 0.80,
            "openalex": 0.95,
            "arxiv": 0.95,
        }
        
        return source_defaults.get(default_source.lower(), 0.60)
