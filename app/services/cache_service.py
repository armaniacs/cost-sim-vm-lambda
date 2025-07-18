"""
Advanced Caching Service with Redis Integration and Performance Optimization.

This service provides:
- Multi-level caching (L1: Memory, L2: Redis)
- Intelligent cache warming and invalidation
- Cache performance monitoring and optimization
- Distributed cache coordination
- Cache pattern optimization for cost calculation data
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis
from flask import current_app

from app.extensions import get_redis_client

logger = logging.getLogger(__name__)


class CacheLevel:
    """Defines cache levels."""
    MEMORY = "memory"
    REDIS = "redis"
    BOTH = "both"


class CacheStrategy:
    """Defines cache strategies."""
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"
    CACHE_ASIDE = "cache_aside"


class CacheStats:
    """Tracks cache statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.evictions = 0
        self.memory_usage = 0
        
    def record_hit(self):
        """Record cache hit."""
        self.hits += 1
    
    def record_miss(self):
        """Record cache miss."""
        self.misses += 1
    
    def record_set(self):
        """Record cache set."""
        self.sets += 1
    
    def record_delete(self):
        """Record cache delete."""
        self.deletes += 1
    
    def record_error(self):
        """Record cache error."""
        self.errors += 1
    
    def record_eviction(self):
        """Record cache eviction."""
        self.evictions += 1
    
    def get_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'errors': self.errors,
            'evictions': self.evictions,
            'hit_ratio': self.get_hit_ratio(),
            'memory_usage': self.memory_usage
        }


class MemoryCache:
    """In-memory cache implementation with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_order = []
        self.stats = CacheStats()
    
    def _evict_lru(self):
        """Evict least recently used items."""
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]
                self.stats.record_eviction()
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Check if cache item is expired."""
        return time.time() - item['timestamp'] > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from memory cache."""
        if key not in self.cache:
            self.stats.record_miss()
            return None
        
        item = self.cache[key]
        if self._is_expired(item):
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.stats.record_miss()
            return None
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        self.stats.record_hit()
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in memory cache."""
        try:
            self._evict_lru()
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self.ttl
            }
            
            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            self.stats.record_set()
            return True
            
        except Exception as e:
            logger.error(f"Memory cache set error: {e}")
            self.stats.record_error()
            return False
    
    def delete(self, key: str) -> bool:
        """Delete item from memory cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.stats.record_delete()
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all items from memory cache."""
        self.cache.clear()
        self.access_order.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        self.stats.memory_usage = len(self.cache)
        return self.stats.get_stats()


class RedisCache:
    """Redis cache implementation with advanced features."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or get_redis_client()
        self.stats = CacheStats()
        self.default_ttl = 3600
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from Redis cache."""
        if not self.redis_client:
            self.stats.record_error()
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                self.stats.record_miss()
                return None
            
            # Deserialize JSON
            result = json.loads(value)
            self.stats.record_hit()
            return result
            
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            self.stats.record_error()
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in Redis cache."""
        if not self.redis_client:
            self.stats.record_error()
            return False
        
        try:
            # Serialize to JSON
            serialized_value = json.dumps(value, default=str)
            
            ttl = ttl or self.default_ttl
            result = self.redis_client.setex(key, ttl, serialized_value)
            
            if result:
                self.stats.record_set()
                return True
            
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
            self.stats.record_error()
            
        return False
    
    def delete(self, key: str) -> bool:
        """Delete item from Redis cache."""
        if not self.redis_client:
            self.stats.record_error()
            return False
        
        try:
            result = self.redis_client.delete(key)
            if result:
                self.stats.record_delete()
                return True
                
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            self.stats.record_error()
            
        return False
    
    def clear(self, pattern: str = "*") -> bool:
        """Clear items matching pattern from Redis cache."""
        if not self.redis_client:
            self.stats.record_error()
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                return True
            return True
            
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")
            self.stats.record_error()
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        stats = self.stats.get_stats()
        
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['memory_usage'] = info.get('used_memory', 0)
                stats['memory_usage_human'] = info.get('used_memory_human', 'N/A')
                stats['keyspace_hits'] = info.get('keyspace_hits', 0)
                stats['keyspace_misses'] = info.get('keyspace_misses', 0)
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        
        return stats


class MultiLevelCache:
    """Multi-level cache with L1 (Memory) and L2 (Redis) tiers."""
    
    def __init__(self, memory_cache: MemoryCache = None, redis_cache: RedisCache = None):
        self.memory_cache = memory_cache or MemoryCache()
        self.redis_cache = redis_cache or RedisCache()
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from multi-level cache."""
        # Try L1 cache first
        value = self.memory_cache.get(key)
        if value is not None:
            self.stats.record_hit()
            return value
        
        # Try L2 cache
        value = self.redis_cache.get(key)
        if value is not None:
            # Promote to L1 cache
            self.memory_cache.set(key, value)
            self.stats.record_hit()
            return value
        
        self.stats.record_miss()
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in multi-level cache."""
        # Set in both levels
        l1_success = self.memory_cache.set(key, value, ttl)
        l2_success = self.redis_cache.set(key, value, ttl)
        
        success = l1_success or l2_success
        if success:
            self.stats.record_set()
        else:
            self.stats.record_error()
        
        return success
    
    def delete(self, key: str) -> bool:
        """Delete item from multi-level cache."""
        l1_success = self.memory_cache.delete(key)
        l2_success = self.redis_cache.delete(key)
        
        success = l1_success or l2_success
        if success:
            self.stats.record_delete()
        
        return success
    
    def clear(self, pattern: str = "*") -> bool:
        """Clear items from multi-level cache."""
        l1_success = self.memory_cache.clear()
        l2_success = self.redis_cache.clear(pattern)
        
        return l1_success and l2_success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive multi-level cache statistics."""
        return {
            'multi_level': self.stats.get_stats(),
            'l1_memory': self.memory_cache.get_stats(),
            'l2_redis': self.redis_cache.get_stats()
        }


class CacheService:
    """Advanced caching service with intelligent cache management."""
    
    def __init__(self, app=None):
        self.app = app
        self.cache = MultiLevelCache()
        self.cache_patterns = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache service with Flask app."""
        self.app = app
        
        # Configure cache patterns for different data types
        self.configure_cache_patterns()
    
    def configure_cache_patterns(self):
        """Configure cache patterns for different data types."""
        self.cache_patterns = {
            'pricing_data': {
                'ttl': 3600,  # 1 hour
                'key_prefix': 'pricing',
                'invalidation_pattern': 'pricing:*'
            },
            'calculation_results': {
                'ttl': 1800,  # 30 minutes
                'key_prefix': 'calc',
                'invalidation_pattern': 'calc:*'
            },
            'user_sessions': {
                'ttl': 86400,  # 24 hours
                'key_prefix': 'session',
                'invalidation_pattern': 'session:*'
            },
            'analytics_data': {
                'ttl': 600,  # 10 minutes
                'key_prefix': 'analytics',
                'invalidation_pattern': 'analytics:*'
            },
            'region_data': {
                'ttl': 7200,  # 2 hours
                'key_prefix': 'region',
                'invalidation_pattern': 'region:*'
            }
        }
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        key = ":".join(key_parts)
        
        # Create hash for very long keys
        if len(key) > 250:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:hash:{key_hash}"
        
        return key
    
    def get_with_pattern(self, pattern: str, *args, **kwargs) -> Optional[Any]:
        """Get cached value using predefined pattern."""
        if pattern not in self.cache_patterns:
            raise ValueError(f"Unknown cache pattern: {pattern}")
        
        config = self.cache_patterns[pattern]
        key = self.generate_cache_key(config['key_prefix'], *args, **kwargs)
        
        return self.cache.get(key)
    
    def set_with_pattern(self, pattern: str, value: Any, *args, **kwargs) -> bool:
        """Set cached value using predefined pattern."""
        if pattern not in self.cache_patterns:
            raise ValueError(f"Unknown cache pattern: {pattern}")
        
        config = self.cache_patterns[pattern]
        key = self.generate_cache_key(config['key_prefix'], *args, **kwargs)
        
        return self.cache.set(key, value, config['ttl'])
    
    def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate cache entries matching pattern."""
        if pattern not in self.cache_patterns:
            raise ValueError(f"Unknown cache pattern: {pattern}")
        
        config = self.cache_patterns[pattern]
        invalidation_pattern = config['invalidation_pattern']
        
        return self.cache.clear(invalidation_pattern)
    
    def warm_cache(self, pattern: str, data_loader_func, *args, **kwargs) -> bool:
        """Warm cache with data from loader function."""
        try:
            data = data_loader_func(*args, **kwargs)
            return self.set_with_pattern(pattern, data, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return False
    
    def get_pricing_data(self, provider: str, region: str, service: str) -> Optional[Dict]:
        """Get cached pricing data."""
        return self.get_with_pattern('pricing_data', provider, region, service)
    
    def set_pricing_data(self, provider: str, region: str, service: str, data: Dict) -> bool:
        """Cache pricing data."""
        return self.set_with_pattern('pricing_data', data, provider, region, service)
    
    def get_calculation_result(self, config_hash: str) -> Optional[Dict]:
        """Get cached calculation result."""
        return self.get_with_pattern('calculation_results', config_hash)
    
    def set_calculation_result(self, config_hash: str, result: Dict) -> bool:
        """Cache calculation result."""
        return self.set_with_pattern('calculation_results', result, config_hash)
    
    def get_analytics_data(self, metric: str, timeframe: str) -> Optional[Dict]:
        """Get cached analytics data."""
        return self.get_with_pattern('analytics_data', metric, timeframe)
    
    def set_analytics_data(self, metric: str, timeframe: str, data: Dict) -> bool:
        """Cache analytics data."""
        return self.set_with_pattern('analytics_data', data, metric, timeframe)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics."""
        return self.cache.get_stats()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        test_key = "health_check_test"
        test_value = {"timestamp": time.time()}
        
        try:
            # Test write
            set_success = self.cache.set(test_key, test_value, 60)
            
            # Test read
            retrieved_value = self.cache.get(test_key)
            read_success = retrieved_value == test_value
            
            # Test delete
            delete_success = self.cache.delete(test_key)
            
            return {
                'status': 'healthy' if all([set_success, read_success, delete_success]) else 'degraded',
                'operations': {
                    'set': set_success,
                    'get': read_success,
                    'delete': delete_success
                },
                'stats': self.get_performance_stats()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'stats': self.get_performance_stats()
            }


# Cache decorators
def cache_result(pattern: str, ttl: Optional[int] = None):
    """Decorator to cache function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_service = current_app.extensions.get('cache_service')
            if not cache_service:
                return func(*args, **kwargs)
            
            # Generate cache key
            func_key = f"{func.__module__}.{func.__name__}"
            cache_key = cache_service.generate_cache_key(pattern, func_key, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_service.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_ttl = ttl or cache_service.cache_patterns.get(pattern, {}).get('ttl', 3600)
            cache_service.cache.set(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            cache_service = current_app.extensions.get('cache_service')
            if cache_service:
                cache_service.invalidate_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()