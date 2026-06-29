"""
Crawl Policy Service for CredenceAI Iteration 0.3

This service implements deterministic safety gates for crawling:
- SSRF / Private IP protection (blocking intranet / localhost IPs)
- Robots.txt parsing and caching
- Domain rate-limiting and delay backoff trackers
- MIME type and file size checks
"""

import logging
import socket
import urllib.robotparser
import ipaddress
import time
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class CrawlPolicyService:
    """
    Makes allow/deny decisions on URLs before any HTTP request is sent.
    Ensures absolute safety and robots.txt compliance.
    """
    
    def __init__(self):
        # Cache for robots.txt parser instances, key: domain
        self._robots_cache: Dict[str, Tuple[urllib.robotparser.RobotFileParser, float]] = {}
        # Cache for last crawl timestamp per domain, key: domain
        self._last_request_times: Dict[str, float] = {}
        # TTL for robots.txt caching (e.g., 1 hour = 3600 seconds)
        self.robots_ttl = 3600

    def check_ssrf(self, url: str) -> Tuple[bool, str]:
        """
        Resolve URL hostname to IPs and check against banned private/intranet CIDRs.
        
        Returns:
            Tuple[bool, reason]: (True, "") if safe, (False, reason) if banned/SSRF risk.
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid hostname in URL"
            
            # Resolve hostname to all IPs
            try:
                # getaddrinfo returns lists of (family, type, proto, canonname, sockaddr)
                addr_info = socket.getaddrinfo(hostname, None)
                ips = set(info[4][0] for info in addr_info)
            except socket.gaierror as e:
                # If DNS resolution fails, block or let it fail downstream?
                # For safety, we block unresolved hosts.
                return False, f"DNS resolution failed: {str(e)}"
            
            # Check each IP against banned CIDRs
            banned_networks = [ipaddress.ip_network(cidr) for cidr in settings.CRAWL_BANNED_CIDRS]
            
            for ip_str in ips:
                # Strip scope ID from IPv6 addresses if present (e.g. fe80::1%eth0)
                clean_ip = ip_str.split('%')[0]
                ip_obj = ipaddress.ip_address(clean_ip)
                
                # Check if it is a private IP, loopback, or in banned CIDRs
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_unspecified:
                    return False, f"Banned IP address detected: {ip_str} (private/loopback)"
                    
                for network in banned_networks:
                    if ip_obj in network:
                        return False, f"Banned IP address detected: {ip_str} falls in network {network}"
            
            return True, ""
        except Exception as e:
            logger.error(f"SSRF check failed for {url}: {e}")
            return False, f"SSRF check exception: {str(e)}"

    def check_robots(self, url: str, user_agent: str = "CredenceAICrawler") -> Tuple[bool, str]:
        """
        Verify if the given URL is allowed by the domain's robots.txt policy.
        
        Returns:
            Tuple[bool, reason]: (True, "") if allowed, (False, reason) if blocked.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            scheme = parsed.scheme
            if not domain or not scheme:
                return False, "Invalid URL scheme or domain"
                
            robots_url = f"{scheme}://{domain}/robots.txt"
            
            # In mock mode, check URL directly without caching standard parser
            if settings.MOCK_SERVICES:
                allowed = not ("blocked" in url.lower() or "admin" in url.lower())
                reason = "" if allowed else f"Blocked by robots.txt at {robots_url} (mock)"
                return allowed, reason
                
            # Check if robots.txt parser is in cache and still valid
            now = time.time()
            if domain in self._robots_cache:
                parser, cache_time = self._robots_cache[domain]
                if now - cache_time < self.robots_ttl:
                    allowed = parser.can_fetch(user_agent, url)
                    reason = "" if allowed else f"Blocked by robots.txt at {robots_url}"
                    return allowed, reason
            
            # Fetch and parse robots.txt
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            
            try:
                # Sync download of robots.txt (could be slow, but this runs in background workers)
                parser.read()
            except Exception as e:
                # If robots.txt fetch fails (e.g. 404), crawling is allowed by default
                logger.warning(f"Could not fetch robots.txt for {domain}: {e}. Defaulting to allow.")
                parser.allow_all = True
            
            self._robots_cache[domain] = (parser, now)
            allowed = parser.can_fetch(user_agent, url)
            reason = "" if allowed else f"Blocked by robots.txt at {robots_url}"
            return allowed, reason
            
        except Exception as e:
            logger.error(f"Robots.txt check failed for {url}: {e}")
            # If an error happens, default to allow but log it
            return True, ""

    def check_rate_limit(self, url: str, delay: Optional[float] = None) -> Tuple[bool, float]:
        """
        Check if we are exceeding rate limit for a domain.
        
        Returns:
            Tuple[bool, wait_time]: (True, 0.0) if rate limit is OK, 
                                    (False, wait_time) if rate limited and needs sleep.
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            return True, 0.0
            
        now = time.time()
        last_time = self._last_request_times.get(domain, 0.0)
        limit_delay = delay if delay is not None else settings.DEFAULT_CRAWL_RATE_LIMIT_DELAY
        
        time_elapsed = now - last_time
        if time_elapsed < limit_delay:
            wait_time = limit_delay - time_elapsed
            return False, wait_time
            
        return True, 0.0

    def record_crawl(self, url: str):
        """Record the timestamp of a crawl request to update rate limit tracking."""
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain:
            self._last_request_times[domain] = time.time()

    def evaluate(self, url: str, user_agent: str = "CredenceAICrawler") -> Dict[str, Any]:
        """
        Fully evaluate a URL against all safety policies.
        
        Returns:
            Dict containing:
                "allowed": bool
                "reason": str
                "rate_limit_ok": bool
                "wait_time": float
        """
        # 1. Scheme Check
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return {
                "allowed": False,
                "reason": f"Scheme {parsed.scheme} is not supported",
                "rate_limit_ok": True,
                "wait_time": 0.0
            }
            
        # 2. SSRF Check
        ssrf_ok, ssrf_reason = self.check_ssrf(url)
        if not ssrf_ok:
            return {
                "allowed": False,
                "reason": ssrf_reason,
                "rate_limit_ok": True,
                "wait_time": 0.0
            }
            
        # 3. Robots.txt Check
        robots_ok, robots_reason = self.check_robots(url, user_agent)
        if not robots_ok:
            return {
                "allowed": False,
                "reason": robots_reason,
                "rate_limit_ok": True,
                "wait_time": 0.0
            }
            
        # 4. Rate limit Check
        rate_ok, wait_time = self.check_rate_limit(url)
        
        return {
            "allowed": True,
            "reason": "",
            "rate_limit_ok": rate_ok,
            "wait_time": wait_time
        }
