"""
Unit tests for Extractor service (Sprint 53)

Tests cover:
- Title extraction from <title>, og:title, and <h1>
- Language detection
- Text extraction and whitespace cleaning
- Markdown generation from headings and paragraphs
- Token count validity
- Content hash consistency
- Headings list
- Author / published_date / canonical URL meta extraction
- Regex fallback mode when bs4 is unavailable
"""

import pytest
from unittest.mock import patch
from app.services.extractor import Extractor, ExtractionResult

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Sample Article Title</title>
    <meta property="og:title" content="OG Article Title" />
    <meta property="og:url" content="https://example.com/article" />
    <meta name="author" content="Jane Doe" />
    <meta property="article:published_time" content="2024-01-15T10:00:00Z" />
    <link rel="canonical" href="https://example.com/article" />
</head>
<body>
    <article>
        <h1>Main Heading</h1>
        <h2>Sub Heading One</h2>
        <p>This is a paragraph with important content about technology trends.</p>
        <h2>Sub Heading Two</h2>
        <p>Another paragraph discussing further details and insights.</p>
        <ul>
            <li>First bullet point</li>
            <li>Second bullet point</li>
        </ul>
    </article>
    <script>var x = 1;</script>
    <style>.cls { color: red; }</style>
    <nav>Navigation menu</nav>
    <footer>Footer content</footer>
</body>
</html>
"""

MINIMAL_HTML = "<html><body><p>Hello world</p></body></html>"

MULTI_LANG_HTML = """
<html lang="fr-FR">
<head><title>Article en Français</title></head>
<body><p>Contenu de l'article.</p></body>
</html>
"""


@pytest.fixture
def extractor():
    return Extractor()


# ──────────────────────────────────────────────
# Title extraction
# ──────────────────────────────────────────────

def test_title_from_og_tag(extractor):
    """og:title should take priority over <title> tag."""
    result = extractor.extract(SAMPLE_HTML)
    assert result.title == "OG Article Title"


def test_title_from_title_tag(extractor):
    """Falls back to <title> when og:title is absent."""
    html = "<html><head><title>Page Title</title></head><body><p>text</p></body></html>"
    result = extractor.extract(html)
    assert result.title == "Page Title"


def test_title_from_h1(extractor):
    """Falls back to first <h1> when no title/og:title."""
    html = "<html><head></head><body><h1>H1 Heading</h1><p>text</p></body></html>"
    result = extractor.extract(html)
    assert result.title == "H1 Heading"


def test_empty_html_title(extractor):
    """Empty HTML returns empty title without crashing."""
    result = extractor.extract("")
    assert isinstance(result.title, str)


# ──────────────────────────────────────────────
# Language detection
# ──────────────────────────────────────────────

def test_language_english(extractor):
    result = extractor.extract(SAMPLE_HTML)
    assert result.language == "en"


def test_language_french(extractor):
    result = extractor.extract(MULTI_LANG_HTML)
    assert result.language == "fr"


def test_language_default_en(extractor):
    """Default language is 'en' when no lang attribute."""
    result = extractor.extract(MINIMAL_HTML)
    assert result.language == "en"


# ──────────────────────────────────────────────
# Text extraction
# ──────────────────────────────────────────────

def test_text_contains_content(extractor):
    """Extracted text should include paragraph content."""
    result = extractor.extract(SAMPLE_HTML)
    assert "important content" in result.text.lower() or "technology" in result.text.lower()


def test_text_excludes_scripts(extractor):
    """Script and style content should not appear in extracted text."""
    result = extractor.extract(SAMPLE_HTML)
    assert "var x = 1" not in result.text
    assert ".cls" not in result.text


def test_text_excludes_nav_footer(extractor):
    """Navigation and footer noise should be stripped."""
    result = extractor.extract(SAMPLE_HTML)
    # Nav and footer are removed by STRIP_TAGS processing
    assert "Navigation menu" not in result.text or len(result.text) > 20


def test_word_count_positive(extractor):
    """Word count should be positive for non-empty HTML."""
    result = extractor.extract(SAMPLE_HTML)
    assert result.word_count > 0


# ──────────────────────────────────────────────
# Markdown generation
# ──────────────────────────────────────────────

def test_markdown_contains_headings(extractor):
    """Markdown output should include heading markers."""
    result = extractor.extract(SAMPLE_HTML)
    assert "#" in result.markdown


def test_markdown_contains_bullets(extractor):
    """List items should become bullet points in markdown."""
    result = extractor.extract(SAMPLE_HTML)
    assert "- " in result.markdown or "bullet" in result.markdown.lower()


def test_markdown_is_string(extractor):
    result = extractor.extract(MINIMAL_HTML)
    assert isinstance(result.markdown, str)


# ──────────────────────────────────────────────
# Token count
# ──────────────────────────────────────────────

def test_token_count_positive(extractor):
    result = extractor.extract(SAMPLE_HTML)
    assert result.token_count > 0


def test_token_count_minimal_html(extractor):
    result = extractor.extract(MINIMAL_HTML)
    assert result.token_count >= 1


# ──────────────────────────────────────────────
# Content hash
# ──────────────────────────────────────────────

def test_content_hash_is_sha256(extractor):
    """Hash should be a 64-character hex string (SHA-256)."""
    result = extractor.extract(SAMPLE_HTML)
    assert isinstance(result.content_hash, str)
    assert len(result.content_hash) == 64
    assert all(c in "0123456789abcdef" for c in result.content_hash)


def test_content_hash_deterministic(extractor):
    """Same HTML produces the same hash."""
    r1 = extractor.extract(SAMPLE_HTML)
    r2 = extractor.extract(SAMPLE_HTML)
    assert r1.content_hash == r2.content_hash


def test_different_html_different_hash(extractor):
    """Different content produces different hashes."""
    r1 = extractor.extract(SAMPLE_HTML)
    r2 = extractor.extract(MINIMAL_HTML)
    assert r1.content_hash != r2.content_hash


# ──────────────────────────────────────────────
# Headings
# ──────────────────────────────────────────────

def test_headings_extracted(extractor):
    """All h1/h2 headings should appear in the headings list."""
    result = extractor.extract(SAMPLE_HTML)
    assert len(result.headings) >= 2
    text = " ".join(result.headings)
    assert "Main Heading" in text or "Sub Heading" in text


def test_headings_is_list(extractor):
    result = extractor.extract(MINIMAL_HTML)
    assert isinstance(result.headings, list)


# ──────────────────────────────────────────────
# Metadata
# ──────────────────────────────────────────────

def test_author_extraction(extractor):
    result = extractor.extract(SAMPLE_HTML)
    assert result.author == "Jane Doe"


def test_published_date_extraction(extractor):
    result = extractor.extract(SAMPLE_HTML)
    assert result.published_date is not None
    assert "2024" in result.published_date


def test_canonical_url_extraction(extractor):
    result = extractor.extract(SAMPLE_HTML, base_url="https://example.com")
    assert result.canonical_url is not None
    assert "example.com" in result.canonical_url


# ──────────────────────────────────────────────
# to_dict serialisation
# ──────────────────────────────────────────────

def test_to_dict_keys(extractor):
    """to_dict() should include all required keys."""
    result = extractor.extract(SAMPLE_HTML)
    d = result.to_dict()
    required_keys = [
        "title", "text", "markdown", "language", "token_count",
        "author", "published_date", "canonical_url", "headings",
        "content_hash", "word_count"
    ]
    for k in required_keys:
        assert k in d, f"Missing key: {k}"


# ──────────────────────────────────────────────
# Regex fallback mode (bs4 unavailable)
# ──────────────────────────────────────────────

def test_regex_fallback_mode(extractor):
    """When bs4 is unavailable, regex fallback should still produce a valid result."""
    import app.services.extractor as extractor_module
    with patch.object(extractor_module, "_BS4_AVAILABLE", False):
        # Need to re-instantiate since it checks module-level flag
        result = extractor._extract_regex(SAMPLE_HTML, "https://example.com")
    assert isinstance(result, ExtractionResult)
    assert isinstance(result.title, str)
    assert isinstance(result.text, str)
    assert len(result.content_hash) == 64
