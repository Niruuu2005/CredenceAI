"""
Cache Manager for CredenceAI Iteration 0.5 (Sprint 58)

Provides a unified caching layer for:
- Federated queries
- Entity Wiki resolution lookups
- Vector embeddings

Uses Redis when available, falls back to a clean thread-safe in-memory cache.
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.utils.redis_ssl import redis_client_kwargs

logger = logging.getLogger(__name__)

# Thread-safe in-memory storage fallback
_IN_MEMORY_CACHE: Dict[str, tuple[Any, datetime]] = {}


class CacheManager:
    """
    Unified caching manager supporting Redis and in-memory fallbacks with TTL.
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self.redis_client = None

        try:
            import redis

            self.redis_client = redis.from_url(
                settings.redis_url,
                socket_timeout=2,
                decode_responses=True,
                **redis_client_kwargs(settings.redis_url, settings.REDIS_SSL_CERT_REQS),
            )
            self.redis_client.ping()
            logger.info("CACHE_MANAGER  Redis connected successfully.")
        except Exception:
            logger.info("CACHE_MANAGER  Redis unavailable. Using in-memory fallback cache.")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    try:
                        return json.loads(val)
                    except json.JSONDecodeError:
                        return val
                return None
            except Exception as e:
                logger.warning(f"CACHE_MANAGER  Redis GET failed: {e}")

        # In-memory fallback
        item = _IN_MEMORY_CACHE.get(key)
        if item:
            val, expiry = item
            if expiry > datetime.now(timezone.utc):
                return val
            else:
                self.delete(key)  # Clean up expired item
        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store a value in the cache with a TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.set(key, serialized, ex=ttl)
                return True
            except Exception as e:
                logger.warning(f"CACHE_MANAGER  Redis SET failed: {e}")

        # In-memory fallback
        expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        _IN_MEMORY_CACHE[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        """Remove a key from the cache."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"CACHE_MANAGER  Redis DELETE failed: {e}")

        if key in _IN_MEMORY_CACHE:
            del _IN_MEMORY_CACHE[key]
            return True
        return False

    def clear_all(self):
        """Flush all cache items (mainly for testing)."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"CACHE_MANAGER  Redis flush failed: {e}")
        _IN_MEMORY_CACHE.clear()
