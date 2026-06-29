"""
Extraction Processor for CredenceAI Iteration 0.3 (Sprint 53)

Parses raw HTML into structured document components:
- Title extraction
- Language detection
- Clean text / Markdown conversion
- Token count (using tiktoken)
- Metadata (author, date, canonical URL)
"""

import logging
import re
import hashlib
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Try to import optional html parsing libs
try:
    from bs4 import BeautifulSoup, Comment
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False
    logger.warning("beautifulsoup4 not installed; extractor will use regex fallback.")

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not installed; token count will be character-estimated.")


class ExtractionResult:
    """Structured result from HTML extraction."""

    def __init__(
        self,
        title: str,
        text: str,
        markdown: str,
        language: str,
        token_count: int,
        author: Optional[str],
        published_date: Optional[str],
        canonical_url: Optional[str],
        headings: List[str],
        content_hash: str,
        word_count: int,
    ):
        self.title = title
        self.text = text
        self.markdown = markdown
        self.language = language
        self.token_count = token_count
        self.author = author
        self.published_date = published_date
        self.canonical_url = canonical_url
        self.headings = headings
        self.content_hash = content_hash
        self.word_count = word_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "text": self.text,
            "markdown": self.markdown,
            "language": self.language,
            "token_count": self.token_count,
            "author": self.author,
            "published_date": self.published_date,
            "canonical_url": self.canonical_url,
            "headings": self.headings,
            "content_hash": self.content_hash,
            "word_count": self.word_count,
        }


class Extractor:
    """
    HTML-to-structured-document processor.
    Uses BeautifulSoup when available; falls back to regex on ImportError.
    """

    # Noise tags removed before text extraction
    STRIP_TAGS = ["script", "style", "noscript", "nav", "footer", "aside", "header", "form", "iframe"]

    def __init__(self):
        self._token_encoder = None
        if _TIKTOKEN_AVAILABLE:
            try:
                self._token_encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                pass

    # ──────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────

    def extract(self, html: str, base_url: str = "") -> ExtractionResult:
        """Parse HTML and return a structured ExtractionResult."""
        if _BS4_AVAILABLE:
            return self._extract_bs4(html, base_url)
        return self._extract_regex(html, base_url)

    # ──────────────────────────────────────────────
    # BeautifulSoup path
    # ──────────────────────────────────────────────

    def _extract_bs4(self, html: str, base_url: str) -> ExtractionResult:
        soup = BeautifulSoup(html, "html.parser")

        # Remove noise elements
        for tag in self.STRIP_TAGS:
            for el in soup.find_all(tag):
                el.decompose()
        # Remove HTML comments
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        title = self._extract_title_bs4(soup)
        language = self._extract_language_bs4(soup)
        author = self._extract_meta(soup, ["author", "article:author", "twitter:creator"])
        published_date = self._extract_meta(soup, ["article:published_time", "publishedDate", "datePublished"])
        canonical_url = self._extract_canonical(soup, base_url)
        headings = self._extract_headings_bs4(soup)

        # Get main content body
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id=re.compile(r"(content|main|article|body)", re.I))
            or soup.find(class_=re.compile(r"(content|main|article|post|entry)", re.I))
            or soup.body
            or soup
        )

        raw_text = main_content.get_text(separator=" ", strip=True) if main_content else ""
        clean_text = self._clean_text(raw_text)
        markdown = self._html_to_markdown_bs4(main_content)
        word_count = len(clean_text.split())
        token_count = self._count_tokens(clean_text)
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        return ExtractionResult(
            title=title,
            text=clean_text,
            markdown=markdown,
            language=language,
            token_count=token_count,
            author=author,
            published_date=published_date,
            canonical_url=canonical_url,
            headings=headings,
            content_hash=content_hash,
            word_count=word_count,
        )

    def _extract_title_bs4(self, soup) -> str:
        """Extract page title: og:title > <title> > first h1."""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def _extract_language_bs4(self, soup) -> str:
        """Detect language from <html lang=".."> attribute."""
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag["lang"].split("-")[0].lower()
        meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
        if meta_lang and meta_lang.get("content"):
            return meta_lang["content"].split(",")[0].strip().lower()
        return "en"

    def _extract_meta(self, soup, names: List[str]) -> Optional[str]:
        """Extract content from a list of possible meta property/name attributes."""
        for name in names:
            tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return None

    def _extract_canonical(self, soup, base_url: str) -> Optional[str]:
        """Resolve canonical URL from <link rel=canonical> or og:url."""
        link = soup.find("link", rel="canonical")
        if link and link.get("href"):
            href = link["href"].strip()
            return urljoin(base_url, href) if base_url else href
        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            return og_url["content"].strip()
        return base_url or None

    def _extract_headings_bs4(self, soup) -> List[str]:
        """Collect all heading texts (h1-h3) in document order."""
        headings = []
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        return headings[:20]  # Limit to 20 headings

    def _html_to_markdown_bs4(self, element) -> str:
        """Convert soup element to simplified markdown."""
        if element is None:
            return ""
        lines = []
        for tag in element.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"]):
            text = tag.get_text(strip=True)
            if not text:
                continue
            if tag.name == "h1":
                lines.append(f"# {text}")
            elif tag.name == "h2":
                lines.append(f"## {text}")
            elif tag.name == "h3":
                lines.append(f"### {text}")
            elif tag.name == "h4":
                lines.append(f"#### {text}")
            elif tag.name == "p":
                lines.append(text)
            elif tag.name == "li":
                lines.append(f"- {text}")
            elif tag.name == "blockquote":
                lines.append(f"> {text}")
            elif tag.name == "pre":
                lines.append(f"```\n{text}\n```")
        return "\n\n".join(lines)

    # ──────────────────────────────────────────────
    # Regex fallback path
    # ──────────────────────────────────────────────

    def _extract_regex(self, html: str, base_url: str) -> ExtractionResult:
        """Minimal regex-based extractor when bs4 is not available."""
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        lang_match = re.search(r"<html[^>]+lang=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
        language = lang_match.group(1).split("-")[0].lower() if lang_match else "en"

        # Strip tags for clean text
        clean_text = re.sub(r"<[^>]+>", " ", html)
        clean_text = self._clean_text(clean_text)

        h_matches = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.IGNORECASE | re.DOTALL)
        headings = [re.sub(r"<[^>]+>", "", h).strip() for h in h_matches[:20]]

        word_count = len(clean_text.split())
        token_count = self._count_tokens(clean_text)
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        return ExtractionResult(
            title=title,
            text=clean_text,
            markdown=clean_text,  # no markdown conversion in regex mode
            language=language,
            token_count=token_count,
            author=None,
            published_date=None,
            canonical_url=base_url or None,
            headings=headings,
            content_hash=content_hash,
            word_count=word_count,
        )

    # ──────────────────────────────────────────────
    # Shared helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalise whitespace and remove excessive blank lines."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _count_tokens(self, text: str) -> int:
        """Return token count using tiktoken if available, else char/4 estimate."""
        if self._token_encoder:
            try:
                return len(self._token_encoder.encode(text))
            except Exception:
                pass
        return len(text) // 4  # rough estimate
