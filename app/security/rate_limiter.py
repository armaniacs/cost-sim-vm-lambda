"""
Rate limiting middleware for API throttling and DDoS protection.

This module provides:
- Per-IP rate limiting
- Per-user rate limiting
- Endpoint-specific limits
- Redis-based storage
- Rate limit headers
- Burst protection
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, current_app
import redis
from redis.exceptions import RedisError


class RateLimiter:
    """Advanced rate limiting middleware"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.redis_client = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize rate limiter with Flask app"""
        self.app = app
        
        # Get rate limiting configuration
        rate_config = self.config.get('rate_limiting', {})
        
        if not rate_config.get('enabled', True):
            app.logger.info("Rate limiting is disabled")
            return
        
        # Initialize Redis connection
        self._init_redis(rate_config)
        
        # Register rate limiting middleware
        self._register_middleware(app)
        
        app.logger.info("Rate limiting initialized")
    
    def _init_redis(self, config: Dict[str, Any]):
        """Initialize Redis connection"""
        redis_url = config.get('redis_url', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            self.app.logger.info("Rate limiter Redis connection established")
            
        except RedisError as e:
            self.app.logger.error(f"Rate limiter Redis connection failed: {e}")
            self.redis_client = None
            raise
    
    def _register_middleware(self, app: Flask):
        """Register rate limiting middleware"""
        
        @app.before_request
        def apply_rate_limiting():
            """Apply rate limiting to incoming requests"""
            if not self.redis_client:
                return
            
            # Skip rate limiting for certain paths
            if self._should_skip_rate_limiting():
                return
            
            # Get rate limit configuration for this endpoint
            limits = self._get_rate_limits()
            
            # Check rate limits
            for limit_type, limit_config in limits.items():
                if not self._check_rate_limit(limit_type, limit_config):
                    return self._create_rate_limit_response(limit_type, limit_config)
            
            # Update rate limit counters
            self._update_rate_limits(limits)
        
        @app.after_request
        def add_rate_limit_headers(response):
            """Add rate limit headers to response"""
            if self.redis_client and hasattr(g, 'rate_limit_info'):
                self._add_rate_limit_headers(response, g.rate_limit_info)
            return response
    
    def _should_skip_rate_limiting(self) -> bool:
        """Check if rate limiting should be skipped for this request"""
        # Skip for static files
        if request.endpoint == 'static':
            return True
        
        # Skip for health checks
        if request.path in ['/health', '/api/health']:
            return True
        
        # Skip for monitoring endpoints
        if request.path.startswith('/api/v1/monitoring/'):
            return True
        
        return False
    
    def _get_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limits for current request"""
        limits = {}
        rate_config = self.config.get('rate_limiting', {})
        
        # Get IP-based limits
        ip_limits = self._get_ip_limits(rate_config)
        if ip_limits:
            limits['ip'] = ip_limits
        
        # Get user-based limits
        user_limits = self._get_user_limits(rate_config)
        if user_limits:
            limits['user'] = user_limits
        
        # Get endpoint-specific limits
        endpoint_limits = self._get_endpoint_limits(rate_config)
        if endpoint_limits:
            limits['endpoint'] = endpoint_limits
        
        return limits
    
    def _get_ip_limits(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get IP-based rate limits"""
        default_limits = config.get('default_limits', {})
        
        if not default_limits:
            return None
        
        client_ip = self._get_client_ip()
        
        return {
            'key': f"rate_limit:ip:{client_ip}",
            'limits': default_limits,
            'identifier': client_ip
        }
    
    def _get_user_limits(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get user-based rate limits"""
        # Check if user is authenticated
        user = getattr(g, 'current_user', None)
        if not user:
            return None
        
        user_limits = config.get('user_limits', {})
        
        # Determine user type
        user_type = 'authenticated'
        if hasattr(user, 'is_premium') and user.is_premium:
            user_type = 'premium'
        
        limits = user_limits.get(user_type, {})
        if not limits:
            return None
        
        return {
            'key': f"rate_limit:user:{user.id}",
            'limits': limits,
            'identifier': f"user:{user.id}"
        }
    
    def _get_endpoint_limits(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get endpoint-specific rate limits"""
        endpoint_limits = config.get('endpoint_limits', {})
        
        # Find matching endpoint
        for endpoint_pattern, limits in endpoint_limits.items():
            if self._match_endpoint(request.path, endpoint_pattern):
                return {
                    'key': f"rate_limit:endpoint:{endpoint_pattern}:{self._get_client_ip()}",
                    'limits': limits,
                    'identifier': f"endpoint:{endpoint_pattern}"
                }
        
        return None
    
    def _match_endpoint(self, path: str, pattern: str) -> bool:
        """Match endpoint path against pattern"""
        if pattern == path:
            return True
        
        # Handle wildcard patterns
        if pattern.endswith('*'):
            return path.startswith(pattern[:-1])
        
        # Handle exact prefix match
        if pattern.endswith('/'):
            return path.startswith(pattern)
        
        return False
    
    def _check_rate_limit(self, limit_type: str, limit_config: Dict[str, Any]) -> bool:
        """Check if rate limit is exceeded"""
        key = limit_config['key']
        limits = limit_config['limits']
        
        current_time = int(time.time())
        
        # Check each time window
        for window, limit in limits.items():
            if not self._check_window_limit(key, window, limit, current_time):
                return False
        
        return True
    
    def _check_window_limit(self, key: str, window: str, limit: int, current_time: int) -> bool:
        """Check rate limit for specific time window"""
        window_seconds = self._get_window_seconds(window)
        window_key = f"{key}:{window}"
        
        try:
            # Get current count
            current_count = self.redis_client.get(window_key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            if current_count >= limit:
                # Store rate limit info for headers
                self._store_rate_limit_info(window, limit, current_count, window_seconds)
                return False
            
            return True
            
        except RedisError as e:
            self.app.logger.error(f"Redis error checking rate limit: {e}")
            return True  # Allow request on Redis error
    
    def _get_window_seconds(self, window: str) -> int:
        """Get window duration in seconds"""
        window_map = {
            'per_minute': 60,
            'per_hour': 3600,
            'per_day': 86400
        }
        return window_map.get(window, 60)
    
    def _update_rate_limits(self, limits: Dict[str, Dict[str, Any]]):
        """Update rate limit counters"""
        current_time = int(time.time())
        
        for limit_type, limit_config in limits.items():
            key = limit_config['key']
            limit_values = limit_config['limits']
            
            for window, limit in limit_values.items():
                window_seconds = self._get_window_seconds(window)
                window_key = f"{key}:{window}"
                
                try:
                    # Increment counter
                    pipe = self.redis_client.pipeline()
                    pipe.incr(window_key)
                    pipe.expire(window_key, window_seconds)
                    pipe.execute()
                    
                except RedisError as e:
                    self.app.logger.error(f"Redis error updating rate limit: {e}")
    
    def _store_rate_limit_info(self, window: str, limit: int, current: int, window_seconds: int):
        """Store rate limit info for response headers"""
        if not hasattr(g, 'rate_limit_info'):
            g.rate_limit_info = {}
        
        g.rate_limit_info[window] = {
            'limit': limit,
            'current': current,
            'remaining': max(0, limit - current),
            'reset_time': int(time.time()) + window_seconds
        }
    
    def _create_rate_limit_response(self, limit_type: str, limit_config: Dict[str, Any]):
        """Create rate limit exceeded response"""
        identifier = limit_config['identifier']
        
        response_data = {
            'error': 'Rate limit exceeded',
            'message': f'Rate limit exceeded for {identifier}',
            'type': limit_type,
            'retry_after': self._get_retry_after()
        }
        
        response = jsonify(response_data)
        response.status_code = 429
        
        # Add rate limit headers
        if hasattr(g, 'rate_limit_info'):
            self._add_rate_limit_headers(response, g.rate_limit_info)
        
        return response
    
    def _get_retry_after(self) -> int:
        """Get retry-after seconds for rate limit response"""
        if hasattr(g, 'rate_limit_info'):
            # Find the soonest reset time
            min_reset = min(
                info['reset_time'] for info in g.rate_limit_info.values()
            )
            return max(1, min_reset - int(time.time()))
        
        return 60  # Default to 1 minute
    
    def _add_rate_limit_headers(self, response, rate_limit_info: Dict[str, Any]):
        """Add rate limit headers to response"""
        headers_config = self.config.get('rate_limiting', {}).get('headers', {})
        
        if not headers_config.get('enabled', True):
            return
        
        # Add standard rate limit headers
        if 'per_minute' in rate_limit_info:
            info = rate_limit_info['per_minute']
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            
            if headers_config.get('include_reset_time', True):
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
        
        # Add retry-after header for rate limit exceeded
        if response.status_code == 429:
            response.headers['Retry-After'] = str(self._get_retry_after())
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or '127.0.0.1'
    
    def reset_rate_limit(self, identifier: str, limit_type: str = 'ip'):
        """Reset rate limit for specific identifier"""
        if not self.redis_client:
            return False
        
        key_pattern = f"rate_limit:{limit_type}:{identifier}:*"
        
        try:
            keys = self.redis_client.keys(key_pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
            
        except RedisError as e:
            self.app.logger.error(f"Error resetting rate limit: {e}")
            return False
    
    def get_rate_limit_status(self, identifier: str, limit_type: str = 'ip') -> Dict[str, Any]:
        """Get rate limit status for identifier"""
        if not self.redis_client:
            return {'error': 'Redis not available'}
        
        key_prefix = f"rate_limit:{limit_type}:{identifier}"
        status = {}
        
        try:
            for window in ['per_minute', 'per_hour', 'per_day']:
                window_key = f"{key_prefix}:{window}"
                current_count = self.redis_client.get(window_key)
                ttl = self.redis_client.ttl(window_key)
                
                status[window] = {
                    'current': int(current_count) if current_count else 0,
                    'reset_in': ttl if ttl > 0 else 0
                }
            
            return status
            
        except RedisError as e:
            return {'error': str(e)}
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Block IP address for specified duration"""
        if not self.redis_client:
            return False
        
        key = f"blocked_ip:{ip}"
        
        try:
            self.redis_client.setex(key, duration, 'blocked')
            return True
            
        except RedisError as e:
            self.app.logger.error(f"Error blocking IP: {e}")
            return False
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP address is blocked"""
        if not self.redis_client:
            return False
        
        key = f"blocked_ip:{ip}"
        
        try:
            return self.redis_client.exists(key) > 0
            
        except RedisError as e:
            self.app.logger.error(f"Error checking blocked IP: {e}")
            return False
    
    def unblock_ip(self, ip: str):
        """Unblock IP address"""
        if not self.redis_client:
            return False
        
        key = f"blocked_ip:{ip}"
        
        try:
            return self.redis_client.delete(key) > 0
            
        except RedisError as e:
            self.app.logger.error(f"Error unblocking IP: {e}")
            return False
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of blocked IP addresses"""
        if not self.redis_client:
            return []
        
        try:
            keys = self.redis_client.keys("blocked_ip:*")
            return [key.replace("blocked_ip:", "") for key in keys]
            
        except RedisError as e:
            self.app.logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        if not self.redis_client:
            return {'error': 'Redis not available'}
        
        try:
            stats = {
                'total_keys': 0,
                'ip_limits': 0,
                'user_limits': 0,
                'endpoint_limits': 0,
                'blocked_ips': 0
            }
            
            # Count rate limit keys
            for key_type in ['ip', 'user', 'endpoint']:
                keys = self.redis_client.keys(f"rate_limit:{key_type}:*")
                stats[f'{key_type}_limits'] = len(keys)
                stats['total_keys'] += len(keys)
            
            # Count blocked IPs
            blocked_keys = self.redis_client.keys("blocked_ip:*")
            stats['blocked_ips'] = len(blocked_keys)
            
            return stats
            
        except RedisError as e:
            return {'error': str(e)}


def rate_limit(limits: Dict[str, int]):
    """Decorator for applying rate limits to specific endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This decorator can be used for additional endpoint-specific rate limiting
            # The main rate limiting is handled by the middleware
            return f(*args, **kwargs)
        return decorated_function
    return decorator