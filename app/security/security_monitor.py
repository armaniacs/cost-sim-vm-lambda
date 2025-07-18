"""
Security monitoring middleware for attack detection and response.

This module provides:
- Security event logging
- Attack pattern recognition
- Suspicious activity detection
- IP blocking
- Geo-location based blocking
- Integration with monitoring system
"""

import json
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import Flask, request, current_app, g
import redis
from redis.exceptions import RedisError


class SecurityMonitor:
    """Security monitoring and attack detection middleware"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.redis_client = None
        self.attack_patterns = {}
        self.blocked_ips = set()
        self.suspicious_activities = defaultdict(deque)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security monitor with Flask app"""
        self.app = app
        
        # Get monitoring configuration
        monitoring_config = self.config.get('monitoring', {})
        
        if not monitoring_config.get('enabled', True):
            app.logger.info("Security monitoring is disabled")
            return
        
        # Initialize Redis for storing security data
        self._init_redis()
        
        # Initialize attack detection patterns
        self._init_attack_patterns(monitoring_config)
        
        # Register security monitoring middleware
        self._register_middleware(app, monitoring_config)
        
        app.logger.info("Security monitoring initialized")
    
    def _init_redis(self):
        """Initialize Redis connection for security data"""
        try:
            redis_url = self.config.get('rate_limiting', {}).get('redis_url', 'redis://localhost:6379/0')
            
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            self.app.logger.info("Security monitor Redis connection established")
            
        except RedisError as e:
            self.app.logger.warning(f"Security monitor Redis connection failed: {e}")
            self.redis_client = None
    
    def _init_attack_patterns(self, config: Dict[str, Any]):
        """Initialize attack detection patterns"""
        attack_config = config.get('attack_detection', {})
        
        self.attack_patterns = {
            'failed_auth': {
                'threshold': attack_config.get('thresholds', {}).get('failed_auth_attempts', 5),
                'window': attack_config.get('time_windows', {}).get('failed_auth', 300)
            },
            'rate_limit': {
                'threshold': attack_config.get('thresholds', {}).get('rate_limit_violations', 10),
                'window': attack_config.get('time_windows', {}).get('rate_limit', 60)
            },
            'suspicious': {
                'threshold': attack_config.get('thresholds', {}).get('suspicious_requests', 20),
                'window': attack_config.get('time_windows', {}).get('suspicious', 600)
            }
        }
    
    def _register_middleware(self, app: Flask, config: Dict[str, Any]):
        """Register security monitoring middleware"""
        
        @app.before_request
        def monitor_security():
            """Monitor security events before processing request"""
            
            # Check if IP is blocked
            client_ip = self._get_client_ip()
            if self._is_ip_blocked(client_ip):
                return self._create_blocked_response()
            
            # Check for geo-blocking
            if self._is_geo_blocked(client_ip):
                return self._create_blocked_response("Geographic location blocked")
            
            # Store request info for monitoring
            g.security_start_time = time.time()
            g.client_ip = client_ip
        
        @app.after_request
        def log_security_event(response):
            """Log security events after processing request"""
            
            # Log security event
            self._log_security_event(response)
            
            # Analyze for suspicious patterns
            self._analyze_suspicious_activity(response)
            
            return response
    
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
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        # Check in-memory blocked IPs
        if ip in self.blocked_ips:
            return True
        
        # Check Redis for blocked IPs
        if self.redis_client:
            try:
                key = f"blocked_ip:{ip}"
                return self.redis_client.exists(key) > 0
            except RedisError:
                pass
        
        return False
    
    def _is_geo_blocked(self, ip: str) -> bool:
        """Check if IP is geo-blocked"""
        geo_config = self.config.get('monitoring', {}).get('geo_blocking', {})
        
        if not geo_config.get('enabled', False):
            return False
        
        # This would integrate with a geo-location service
        # For now, return False as it's not implemented
        return False
    
    def _create_blocked_response(self, message: str = "IP address blocked"):
        """Create response for blocked requests"""
        from flask import jsonify
        
        response = jsonify({
            'error': 'Access denied',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        response.status_code = 403
        
        return response
    
    def _log_security_event(self, response):
        """Log security event"""
        if not self.config.get('monitoring', {}).get('log_security_events', True):
            return
        
        # Calculate request duration
        start_time = getattr(g, 'security_start_time', time.time())
        duration = time.time() - start_time
        
        # Create security event
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': getattr(g, 'client_ip', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': duration,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'referer': request.headers.get('Referer', ''),
            'content_length': response.content_length or 0,
            'user_id': getattr(g, 'current_user', {}).get('id', 'anonymous')
        }
        
        # Add additional security context
        event.update(self._get_security_context())
        
        # Log to application logger
        self.app.logger.info(f"Security Event: {json.dumps(event)}")
        
        # Store in Redis for analysis
        self._store_security_event(event)
        
        # Send to monitoring system if available
        if hasattr(self.app, 'monitoring_integration'):
            self.app.monitoring_integration.log_audit_event(
                'security_event',
                event,
                event['user_id']
            )
    
    def _get_security_context(self) -> Dict[str, Any]:
        """Get additional security context"""
        context = {}
        
        # Check for suspicious headers
        suspicious_headers = []
        for header_name, header_value in request.headers.items():
            if self._is_suspicious_header(header_name, header_value):
                suspicious_headers.append(header_name)
        
        if suspicious_headers:
            context['suspicious_headers'] = suspicious_headers
        
        # Check for suspicious patterns in request
        if hasattr(g, 'suspicious_activities'):
            context['suspicious_activities'] = g.suspicious_activities
        
        # Check for rate limiting violations
        if hasattr(g, 'rate_limit_exceeded'):
            context['rate_limit_exceeded'] = g.rate_limit_exceeded
        
        return context
    
    def _is_suspicious_header(self, name: str, value: str) -> bool:
        """Check if header is suspicious"""
        # Check for abnormally long headers
        if len(value) > 8192:
            return True
        
        # Check for suspicious header names
        suspicious_names = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Originating-IP',
            'X-Remote-IP',
            'X-Client-IP'
        ]
        
        if name in suspicious_names and ',' in value:
            # Multiple IPs in forwarded headers can be suspicious
            return True
        
        return False
    
    def _store_security_event(self, event: Dict[str, Any]):
        """Store security event in Redis"""
        if not self.redis_client:
            return
        
        try:
            # Store event with TTL
            key = f"security_event:{event['timestamp']}:{event['client_ip']}"
            self.redis_client.setex(key, 86400, json.dumps(event))  # 24 hour TTL
            
            # Add to client IP events list
            ip_key = f"ip_events:{event['client_ip']}"
            self.redis_client.lpush(ip_key, key)
            self.redis_client.ltrim(ip_key, 0, 100)  # Keep last 100 events
            self.redis_client.expire(ip_key, 86400)  # 24 hour TTL
            
        except RedisError as e:
            self.app.logger.error(f"Error storing security event: {e}")
    
    def _analyze_suspicious_activity(self, response):
        """Analyze request for suspicious activity"""
        client_ip = getattr(g, 'client_ip', 'unknown')
        
        # Check for failed authentication
        if response.status_code == 401 and '/auth/' in request.path:
            self._record_failed_auth(client_ip)
        
        # Check for rate limiting violations
        if response.status_code == 429:
            self._record_rate_limit_violation(client_ip)
        
        # Check for suspicious requests
        if self._is_suspicious_request(response):
            self._record_suspicious_request(client_ip)
        
        # Check for attack patterns
        self._check_attack_patterns(client_ip)
    
    def _record_failed_auth(self, ip: str):
        """Record failed authentication attempt"""
        if not self.redis_client:
            return
        
        try:
            key = f"failed_auth:{ip}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, self.attack_patterns['failed_auth']['window'])
            
        except RedisError as e:
            self.app.logger.error(f"Error recording failed auth: {e}")
    
    def _record_rate_limit_violation(self, ip: str):
        """Record rate limit violation"""
        if not self.redis_client:
            return
        
        try:
            key = f"rate_limit_violations:{ip}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, self.attack_patterns['rate_limit']['window'])
            
        except RedisError as e:
            self.app.logger.error(f"Error recording rate limit violation: {e}")
    
    def _record_suspicious_request(self, ip: str):
        """Record suspicious request"""
        if not self.redis_client:
            return
        
        try:
            key = f"suspicious_requests:{ip}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, self.attack_patterns['suspicious']['window'])
            
        except RedisError as e:
            self.app.logger.error(f"Error recording suspicious request: {e}")
    
    def _is_suspicious_request(self, response) -> bool:
        """Check if request is suspicious"""
        # Check for error responses
        if response.status_code >= 400:
            return True
        
        # Check for suspicious patterns in request
        if hasattr(g, 'suspicious_activities') and g.suspicious_activities:
            return True
        
        # Check for unusual request patterns
        if self._has_unusual_patterns():
            return True
        
        return False
    
    def _has_unusual_patterns(self) -> bool:
        """Check for unusual request patterns"""
        # Check for rapid requests
        client_ip = getattr(g, 'client_ip', 'unknown')
        
        # This would be implemented with proper timing analysis
        # For now, return False
        return False
    
    def _check_attack_patterns(self, ip: str):
        """Check for attack patterns and take action"""
        if not self.redis_client:
            return
        
        try:
            # Check failed authentication attempts
            failed_auth_count = self.redis_client.get(f"failed_auth:{ip}")
            if failed_auth_count and int(failed_auth_count) >= self.attack_patterns['failed_auth']['threshold']:
                self._handle_attack_detected(ip, 'failed_auth', int(failed_auth_count))
            
            # Check rate limit violations
            rate_limit_count = self.redis_client.get(f"rate_limit_violations:{ip}")
            if rate_limit_count and int(rate_limit_count) >= self.attack_patterns['rate_limit']['threshold']:
                self._handle_attack_detected(ip, 'rate_limit', int(rate_limit_count))
            
            # Check suspicious requests
            suspicious_count = self.redis_client.get(f"suspicious_requests:{ip}")
            if suspicious_count and int(suspicious_count) >= self.attack_patterns['suspicious']['threshold']:
                self._handle_attack_detected(ip, 'suspicious', int(suspicious_count))
            
        except RedisError as e:
            self.app.logger.error(f"Error checking attack patterns: {e}")
    
    def _handle_attack_detected(self, ip: str, attack_type: str, count: int):
        """Handle detected attack"""
        self.app.logger.warning(f"Attack detected from {ip}: {attack_type} ({count} occurrences)")
        
        # Block IP if IP blocking is enabled
        ip_blocking_config = self.config.get('monitoring', {}).get('ip_blocking', {})
        if ip_blocking_config.get('enabled', True):
            self._block_ip(ip, ip_blocking_config.get('block_duration', 3600))
        
        # Send alert
        if self.config.get('monitoring', {}).get('alert_on_attacks', True):
            self._send_security_alert(ip, attack_type, count)
        
        # Record in monitoring system
        if hasattr(self.app, 'monitoring_integration'):
            self.app.monitoring_integration.record_custom_metric(
                'security.attack_detected',
                1,
                tags={
                    'attack_type': attack_type,
                    'ip': ip,
                    'count': count
                }
            )
    
    def _block_ip(self, ip: str, duration: int):
        """Block IP address"""
        # Check if IP is in whitelist
        whitelist = self.config.get('monitoring', {}).get('ip_blocking', {}).get('whitelist', [])
        if ip in whitelist:
            self.app.logger.info(f"IP {ip} is whitelisted, not blocking")
            return
        
        # Add to in-memory blocked IPs
        self.blocked_ips.add(ip)
        
        # Store in Redis
        if self.redis_client:
            try:
                key = f"blocked_ip:{ip}"
                self.redis_client.setex(key, duration, 'blocked')
                
            except RedisError as e:
                self.app.logger.error(f"Error blocking IP in Redis: {e}")
        
        self.app.logger.info(f"Blocked IP {ip} for {duration} seconds")
    
    def _send_security_alert(self, ip: str, attack_type: str, count: int):
        """Send security alert"""
        if hasattr(self.app, 'monitoring_integration'):
            self.app.monitoring_integration.trigger_custom_alert(
                f"Security Attack Detected",
                f"Attack type: {attack_type} from IP: {ip} ({count} occurrences)",
                "high",
                {
                    'ip': ip,
                    'attack_type': attack_type,
                    'count': count,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security monitoring statistics"""
        stats = {
            'blocked_ips': len(self.blocked_ips),
            'attack_patterns': {},
            'recent_events': 0
        }
        
        if self.redis_client:
            try:
                # Get attack pattern statistics
                for pattern_name, pattern_config in self.attack_patterns.items():
                    pattern_keys = self.redis_client.keys(f"{pattern_name}:*")
                    stats['attack_patterns'][pattern_name] = len(pattern_keys)
                
                # Get recent events count
                event_keys = self.redis_client.keys("security_event:*")
                stats['recent_events'] = len(event_keys)
                
            except RedisError as e:
                self.app.logger.error(f"Error getting security stats: {e}")
        
        return stats
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of blocked IPs"""
        blocked_ips = list(self.blocked_ips)
        
        if self.redis_client:
            try:
                redis_blocked = self.redis_client.keys("blocked_ip:*")
                for key in redis_blocked:
                    ip = key.replace("blocked_ip:", "")
                    if ip not in blocked_ips:
                        blocked_ips.append(ip)
                        
            except RedisError as e:
                self.app.logger.error(f"Error getting blocked IPs: {e}")
        
        return blocked_ips
    
    def unblock_ip(self, ip: str):
        """Unblock IP address"""
        # Remove from in-memory blocked IPs
        self.blocked_ips.discard(ip)
        
        # Remove from Redis
        if self.redis_client:
            try:
                key = f"blocked_ip:{ip}"
                self.redis_client.delete(key)
                
            except RedisError as e:
                self.app.logger.error(f"Error unblocking IP: {e}")
        
        self.app.logger.info(f"Unblocked IP {ip}")
    
    def get_ip_events(self, ip: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get events for specific IP"""
        events = []
        
        if self.redis_client:
            try:
                ip_key = f"ip_events:{ip}"
                event_keys = self.redis_client.lrange(ip_key, 0, limit - 1)
                
                for event_key in event_keys:
                    event_data = self.redis_client.get(event_key)
                    if event_data:
                        events.append(json.loads(event_data))
                        
            except RedisError as e:
                self.app.logger.error(f"Error getting IP events: {e}")
        
        return events
    
    def whitelist_ip(self, ip: str):
        """Add IP to whitelist"""
        if 'monitoring' not in self.config:
            self.config['monitoring'] = {}
        
        if 'ip_blocking' not in self.config['monitoring']:
            self.config['monitoring']['ip_blocking'] = {}
        
        if 'whitelist' not in self.config['monitoring']['ip_blocking']:
            self.config['monitoring']['ip_blocking']['whitelist'] = []
        
        if ip not in self.config['monitoring']['ip_blocking']['whitelist']:
            self.config['monitoring']['ip_blocking']['whitelist'].append(ip)
            
        # Also unblock if currently blocked
        self.unblock_ip(ip)
    
    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist"""
        whitelist = self.config.get('monitoring', {}).get('ip_blocking', {}).get('whitelist', [])
        if ip in whitelist:
            whitelist.remove(ip)
    
    def get_whitelist(self) -> List[str]:
        """Get IP whitelist"""
        return self.config.get('monitoring', {}).get('ip_blocking', {}).get('whitelist', [])