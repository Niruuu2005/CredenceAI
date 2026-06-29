import pytest
from unittest.mock import patch, MagicMock
from app.services.crawler_task import crawl_url
from app.models import Document, CrawlPolicyDecision
from app.config import settings

@pytest.fixture(autouse=True)
def setup_mock_services():
    # Store original and restore after test
    orig_mock = settings.MOCK_SERVICES
    yield
    settings.MOCK_SERVICES = orig_mock

def test_crawl_url_allowed_mock(db_session):
    """Test successful mock crawling of a safe URL."""
    settings.MOCK_SERVICES = True
    url = "https://example.com/safe-page"
    job_id = "job_test_123"
    
    # Run task
    result = crawl_url(job_id, url)
    
    assert result["success"] is True
    assert result["status"] == "crawled"
    assert result["document_id"] is not None
    assert "Mocked Page" in result["title"]
    
    # Verify DB persistence of Document
    doc = db_session.query(Document).filter(Document.id == result["document_id"]).first()
    assert doc is not None
    assert doc.url == url
    assert doc.job_id == job_id
    assert "mocked crawl content" in doc.body_text
    assert doc.content_hash == result["content_hash"]
    
    # Verify DB persistence of CrawlPolicyDecision
    decision = db_session.query(CrawlPolicyDecision).filter(CrawlPolicyDecision.job_id == job_id).first()
    assert decision is not None
    assert decision.url == url
    assert decision.allowed is True
    assert decision.reason == ""

def test_crawl_url_blocked_mock(db_session):
    """Test policy block is captured and no Document is created."""
    settings.MOCK_SERVICES = True
    url = "https://example.com/admin/settings"
    job_id = "job_test_456"
    
    # Run task
    result = crawl_url(job_id, url)
    
    assert result["success"] is False
    assert result["status"] == "blocked"
    assert result["document_id"] is None
    
    # Verify Document is NOT in DB
    docs_count = db_session.query(Document).filter(Document.job_id == job_id).count()
    assert docs_count == 0
    
    # Verify DB persistence of Blocked CrawlPolicyDecision
    decision = db_session.query(CrawlPolicyDecision).filter(CrawlPolicyDecision.job_id == job_id).first()
    assert decision is not None
    assert decision.url == url
    assert decision.allowed is False
    assert "blocked by robots.txt" in decision.reason.lower()

def test_crawl_url_real_request(db_session):
    """Test crawl using real request calls mocked at socket/requests layer."""
    settings.MOCK_SERVICES = False
    url = "https://publicsite.com/news/article1"
    job_id = "job_test_789"
    
    # Mock socket resolution to return public IP
    # Mock requests.head and requests.get responses
    fake_html = "<html><head><title>Test Article</title></head><body><p>This is a real parsed body text from public site.</p></body></html>"
    
    mock_head_response = MagicMock()
    mock_head_response.headers = {
        "content-type": "text/html; charset=utf-8",
        "content-length": "200"
    }
    
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.headers = {
        "content-type": "text/html; charset=utf-8"
    }
    mock_get_response.text = fake_html
    
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("8.8.8.8", 80))]):
        with patch("requests.head", return_value=mock_head_response) as mock_head:
            with patch("requests.get", return_value=mock_get_response) as mock_get:
                
                result = crawl_url(job_id, url)
                
                assert result["success"] is True
                assert result["status"] == "crawled"
                assert result["title"] == "Test Article"
                
                # Check calls
                mock_head.assert_called_once()
                mock_get.assert_called_once()
                
                # Verify DB Document
                doc = db_session.query(Document).filter(Document.id == result["document_id"]).first()
                assert doc is not None
                assert doc.title == "Test Article"
                assert "real parsed body text" in doc.body_text
                assert doc.mime_type == "text/html"
