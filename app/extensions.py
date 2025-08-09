"""
Flask Extensions Module

This module provides centralized access to Flask extensions and Redis client
for the cost-sim-vm-lambda application.
"""

import logging
import time
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


# Simple cache manager implementation
class CacheManager:
    """Simple in-memory cache manager for testing purposes."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self.default_timeout = 300  # 5 minutes

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            # Check if expired
            if time.time() - self._timestamps.get(key, 0) > self.default_timeout:
                self.delete(key)
                return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache."""
        self._cache[key] = value
        self._timestamps[key] = time.time()
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        return True

    def clear(self) -> bool:
        """Clear all cache."""
        self._cache.clear()
        self._timestamps.clear()
        return True


# Global cache manager instance
cache_manager = CacheManager()


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance.

    Returns:
        Optional[redis.Redis]: Redis client if available, None otherwise
    """
    global _redis_client

    if _redis_client is None:
        try:
            # Try to create Redis client with default settings
            _redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None

    return _redis_client


def init_extensions(app):
    """
    Initialize Flask extensions.

    Args:
        app: Flask application instance
    """
    # Initialize Redis if needed
    get_redis_client()
    logger.info("Extensions initialized")
