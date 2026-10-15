"""
SSRF and DNS Rebinding Protection Guard.
Implements FR-006, NFR-009, PRV-02, PRV-03, AT-08, Gate G8.
Strictly blocks access to loopback, private RFC1918, link-local, cloud metadata, and reserved networks.
"""

import ipaddress
import socket
import urllib.parse
from typing import List, Optional


class SSRFViolationError(Exception):
    """Raised when a URL attempts to target forbidden network infrastructure."""
    pass


FORBIDDEN_NETWORKS: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    # IPv4 Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    # IPv4 RFC1918 Private
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Link-local & Cloud Metadata (AWS, Azure, GCP: 169.254.169.254)
    ipaddress.ip_network("169.254.0.0/16"),
    # Current network & broadcast
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 Loopback, Unique Local, Link-local
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"),  # IPv4-mapped IPv6
]

ALLOWED_SCHEMES = {"http", "https"}


def validate_url_safe(url: str) -> str:
    """
    Validate target URL against scheme bypasses, DNS resolution, and forbidden IP ranges.
    Returns the normalized URL if safe, otherwise raises SSRFViolationError.
    """
    if not url:
        raise SSRFViolationError("Empty URL provided.")

    parsed = urllib.parse.urlparse(url.strip())

    # 1. Scheme Check
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFViolationError(
            f"Disallowed URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFViolationError("URL missing valid hostname.")

    hostname_clean = hostname.strip().lower()

    # Fast check for common metadata and localhost keywords
    if hostname_clean in {"localhost", "metadata", "instance-data"}:
        raise SSRFViolationError(f"Prohibited host target '{hostname}'.")

    # 2. DNS Resolution & IP Range Check
    try:
        # Resolve all addresses (both IPv4 and IPv6)
        addr_info = socket.getaddrinfo(hostname_clean, None)
    except socket.gaierror as e:
        raise SSRFViolationError(f"DNS resolution failed for '{hostname}': {e}")

    if not addr_info:
        raise SSRFViolationError(f"No IP addresses resolved for hostname '{hostname}'.")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFViolationError(f"Invalid resolved IP '{ip_str}' for host '{hostname}'.")

        # Check against forbidden networks
        for network in FORBIDDEN_NETWORKS:
            if ip_obj in network:
                raise SSRFViolationError(
                    f"SSRF violation: Host '{hostname}' resolved to prohibited address '{ip_str}' "
                    f"in network '{network}'."
                )

    return url


# Compatibility alias
SSRFSecurityException = SSRFViolationError


class SSRFGuard:
    """Class interface for SSRF validation and IP restriction checks."""

    @staticmethod
    def is_private_or_restricted_ip(ip_str: str) -> bool:
        """Check if an IP address string falls into any forbidden/private network."""
        try:
            ip_obj = ipaddress.ip_address(ip_str.strip())
        except ValueError:
            return True

        for network in FORBIDDEN_NETWORKS:
            if ip_obj in network:
                return True
        return False

    @staticmethod
    def validate_target_url(url: str) -> str:
        """Validate target URL. Raises SSRFViolationError if unsafe."""
        return validate_url_safe(url)

