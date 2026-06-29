import urllib.parse

class URLCanonicalizer:
    @staticmethod
    def canonicalize(url: str) -> str:
        """Standardize a URL by cleaning queries, schemes, domains, and paths."""
        if not url:
            return ""

        try:
            parsed = urllib.parse.urlparse(url)
            
            # 1. Scheme to lowercase
            scheme = parsed.scheme.lower()
            
            # 2. Netloc (domain) to lowercase and strip default ports
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                domain, port = netloc.split(":", 1)
                if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                    netloc = domain
            
            # 3. Path cleaning: remove duplicate slashes, strip trailing slashes (except root path '/')
            path = parsed.path
            if path and len(path) > 1 and path.endswith("/"):
                path = path.rstrip("/")
                
            # 4. Clean query parameters (strip UTMs and tracking tags)
            query_params = urllib.parse.parse_qsl(parsed.query)
            clean_params = []
            strip_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "ref", "fbclid", "gclid", "client", "s", "si", "rss", "origin"
            }
            
            for k, v in query_params:
                if k.lower() not in strip_params:
                    clean_params.append((k, v))
                    
            query = ""
            if clean_params:
                clean_params.sort(key=lambda x: x[0])
                query = urllib.parse.urlencode(clean_params)
                
            # 5. Remove fragments
            fragment = ""
            
            # Rebuild URL
            canonical = urllib.parse.urlunparse((scheme, netloc, path, parsed.params, query, fragment))
            return canonical
        except Exception:
            return url
