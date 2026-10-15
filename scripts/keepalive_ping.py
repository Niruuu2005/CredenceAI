#!/usr/bin/env python3
"""
Keep-alive ping daemon for CredenceAI Render Backend.

Sends a lightweight GET request to the Render API (/api/health) every 40-45 seconds
to prevent Render free-tier web services from entering idle spin-down.

Usage:
    python scripts/keepalive_ping.py
    python scripts/keepalive_ping.py --url https://credenceai-api.onrender.com/api/health
    python scripts/keepalive_ping.py --min-interval 40 --max-interval 45
"""

import argparse
import os
import random
import sys
import time
from datetime import datetime
import urllib.request
import urllib.error

DEFAULT_URL = os.environ.get("API_URL", "https://credenceai-api.onrender.com/api/health")

def main():
    parser = argparse.ArgumentParser(description="CredenceAI API Keep-Alive Daemon")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Health endpoint URL (default: {DEFAULT_URL})")
    parser.add_argument("--min-interval", type=int, default=40, help="Minimum interval in seconds (default: 40)")
    parser.add_argument("--max-interval", type=int, default=45, help="Maximum interval in seconds (default: 45)")
    args = parser.parse_args()

    url = args.url.strip()
    if not url.endswith("/api/health"):
        if "/api" in url:
            url = f"{url.rstrip('/')}/health"
        else:
            url = f"{url.rstrip('/')}/api/health"

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CredenceAI Keep-Alive Daemon started")
    print(f"Target URL: {url}")
    print(f"Ping interval: {args.min_interval}-{args.max_interval} seconds of inactivity")
    print("Press Ctrl+C to terminate\n")

    consecutive_failures = 0

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CredenceAI-KeepAlive/2.0"}
            )
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=30) as response:
                status = response.getcode()
                elapsed = time.time() - start_time
                print(f"[{timestamp}] PING OK - Status: {status} - Latency: {elapsed:.2f}s")
                consecutive_failures = 0
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start_time
            print(f"[{timestamp}] PING HTTP {e.code} - Latency: {elapsed:.2f}s")
        except Exception as e:
            consecutive_failures += 1
            print(f"[{timestamp}] PING FAILED ({consecutive_failures}): {e}")

        # Sleep random interval between min and max seconds (40 - 45s)
        sleep_sec = random.randint(args.min_interval, args.max_interval)
        time.sleep(sleep_sec)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeep-Alive Daemon stopped by user.")
        sys.exit(0)
