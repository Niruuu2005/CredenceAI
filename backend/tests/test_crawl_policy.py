import pytest
import time
from unittest.mock import patch
from app.services.crawl_policy import CrawlPolicyService
from app.config import settings

@pytest.fixture
def crawl_policy_service():
    # Force settings mock_services to True or False for specific tests if needed
    return CrawlPolicyService()

def test_ssrf_protection_private_ips(crawl_policy_service):
    """Verify that private IP addresses are correctly detected and blocked."""
    # Test localhost IPv4
    allowed, reason = crawl_policy_service.check_ssrf("http://127.0.0.1/index.html")
    assert allowed is False
    assert "private/loopback" in reason.lower()

    # Test link-local
    allowed, reason = crawl_policy_service.check_ssrf("http://169.254.169.254/latest/meta-data/")
    assert allowed is False
    assert "private" in reason.lower() or "banned" in reason.lower()

    # Test private subnet class A
    allowed, reason = crawl_policy_service.check_ssrf("https://10.0.0.1/admin")
    assert allowed is False
    assert "private" in reason.lower() or "banned" in reason.lower()

    # Test private subnet class C
    allowed, reason = crawl_policy_service.check_ssrf("http://192.168.1.100/status")
    assert allowed is False
    assert "private" in reason.lower() or "banned" in reason.lower()

def test_ssrf_protection_ipv6(crawl_policy_service):
    """Verify that loopback IPv6 addresses are blocked."""
    allowed, reason = crawl_policy_service.check_ssrf("http://[::1]/index.html")
    assert allowed is False
    assert "private" in reason.lower() or "banned" in reason.lower() or "loopback" in reason.lower()

def test_ssrf_allowed_hostnames(crawl_policy_service):
    """Verify that a standard public hostname is allowed by SSRF check."""
    # We patch getaddrinfo to return a public IP (e.g., 8.8.8.8)
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("8.8.8.8", 80))]):
        allowed, reason = crawl_policy_service.check_ssrf("https://www.google.com/search")
        assert allowed is True
        assert reason == ""

def test_robots_txt_allow_rules(crawl_policy_service):
    """Test standard robots.txt rule resolution."""
    # In mock mode, we check that it handles standard URLs
    with patch.object(settings, "MOCK_SERVICES", True):
        allowed, reason = crawl_policy_service.check_robots("https://example.com/public/article")
        assert allowed is True
        assert reason == ""

        allowed, reason = crawl_policy_service.check_robots("https://example.com/admin/dashboard")
        assert allowed is False
        assert "blocked by robots.txt" in reason.lower()

def test_rate_limit_checking(crawl_policy_service):
    """Test rate limit detection and backoff calculation."""
    url = "https://example.com/item1"
    
    # First request: rate limit should be fine
    allowed, wait_time = crawl_policy_service.check_rate_limit(url, delay=1.0)
    assert allowed is True
    assert wait_time == 0.0
    
    # Record a crawl
    crawl_policy_service.record_crawl(url)
    
    # Immediate second request to same domain: should be rate limited
    allowed, wait_time = crawl_policy_service.check_rate_limit(url, delay=1.0)
    assert allowed is False
    assert wait_time > 0.0
    assert wait_time <= 1.0

    # Wait 1.1 seconds and check again
    time.sleep(1.05)
    allowed, wait_time = crawl_policy_service.check_rate_limit(url, delay=1.0)
    # The sleep time could vary slightly on Windows, check if it's either allowed or wait time is extremely small
    if not allowed:
        assert wait_time < 0.1
    else:
        assert wait_time == 0.0

def test_evaluate_endpoint(crawl_policy_service):
    """Test the full URL policy evaluation wrapper."""
    with patch("socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 80))]): # public IP of example.com
        with patch.object(settings, "MOCK_SERVICES", True):
            result = crawl_policy_service.evaluate("https://example.com/allowed-path")
            assert result["allowed"] is True
            assert result["reason"] == ""
            assert result["rate_limit_ok"] is True
            assert result["wait_time"] == 0.0

            result = crawl_policy_service.evaluate("ftp://example.com/file")
            assert result["allowed"] is False
            assert "not supported" in result["reason"].lower()
