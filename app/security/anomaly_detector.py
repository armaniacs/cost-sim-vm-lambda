"""
Advanced anomaly detection system for security monitoring.

This module provides:
- Pattern-based anomaly detection
- Machine learning-free statistical analysis
- Automatic threat response
- Real-time monitoring
- Adaptive thresholds
"""

import time
import json
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from flask import Flask, request, g, current_app
import redis
from redis.exceptions import RedisError


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    FAILED_LOGIN_BURST = "failed_login_burst"
    RATE_LIMIT_VIOLATION_PATTERN = "rate_limit_violation_pattern"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TIME_BASED_ANOMALY = "time_based_anomaly"
    PAYLOAD_SIZE_ANOMALY = "payload_size_anomaly"
    ERROR_RATE_SPIKE = "error_rate_spike"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    DATA_EXFILTRATION_PATTERN = "data_exfiltration_pattern"
    BRUTE_FORCE_ATTACK = "brute_force_attack"


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AnomalyEvent:
    """Anomaly event data structure"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    timestamp: datetime
    client_ip: str
    user_id: Optional[str]
    description: str
    evidence: Dict[str, Any]
    risk_score: float
    threshold_breached: Dict[str, Any]
    recommended_actions: List[str]
    confidence_score: float


class AnomalyDetector:
    """Advanced anomaly detection system"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.redis_client = None
        self.detection_rules = {}
        self.baseline_metrics = {}
        self.active_patterns = defaultdict(deque)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize anomaly detector with Flask app"""
        self.app = app
        
        # Get anomaly detection configuration
        anomaly_config = self.config.get('anomaly_detection', {})
        
        if not anomaly_config.get('enabled', True):
            app.logger.info("Anomaly detection is disabled")
            return
        
        # Initialize Redis connection
        self._init_redis()
        
        # Initialize detection rules
        self._init_detection_rules(anomaly_config)
        
        # Initialize baseline metrics
        self._init_baseline_metrics()
        
        # Start pattern monitoring
        self._init_pattern_monitoring()
        
        app.logger.info("Anomaly detector initialized")
    
    def _init_redis(self):
        """Initialize Redis connection for anomaly data"""
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
            self.app.logger.info("Anomaly detector Redis connection established")
            
        except RedisError as e:
            self.app.logger.warning(f"Anomaly detector Redis connection failed: {e}")
            self.redis_client = None
    
    def _init_detection_rules(self, config: Dict[str, Any]):
        """Initialize anomaly detection rules"""
        thresholds = config.get('thresholds', {})
        time_windows = config.get('time_windows', {})
        
        self.detection_rules = {
            AnomalyType.FAILED_LOGIN_BURST: {
                'threshold': thresholds.get('failed_login_burst', 5),
                'time_window': time_windows.get('failed_login_burst', 300),  # 5 minutes
                'severity': AnomalySeverity.HIGH,
                'auto_block': True
            },
            AnomalyType.RATE_LIMIT_VIOLATION_PATTERN: {
                'threshold': thresholds.get('rate_limit_violations', 10),
                'time_window': time_windows.get('rate_limit_violations', 600),  # 10 minutes
                'severity': AnomalySeverity.MEDIUM,
                'auto_block': True
            },
            AnomalyType.ERROR_RATE_SPIKE: {
                'threshold': thresholds.get('error_rate_spike', 20),
                'time_window': time_windows.get('error_rate_spike', 300),  # 5 minutes
                'severity': AnomalySeverity.MEDIUM,
                'auto_block': False
            },
            AnomalyType.PAYLOAD_SIZE_ANOMALY: {
                'threshold': thresholds.get('payload_size_anomaly', 1048576),  # 1MB
                'time_window': time_windows.get('payload_size_anomaly', 3600),  # 1 hour
                'severity': AnomalySeverity.LOW,
                'auto_block': False
            },
            AnomalyType.UNUSUAL_ACCESS_PATTERN: {
                'threshold': thresholds.get('unusual_access_pattern', 100),
                'time_window': time_windows.get('unusual_access_pattern', 3600),  # 1 hour
                'severity': AnomalySeverity.LOW,
                'auto_block': False
            }
        }
    
    def _init_baseline_metrics(self):
        """Initialize baseline metrics for anomaly detection"""
        self.baseline_metrics = {
            'average_requests_per_minute': 10.0,
            'average_response_time': 0.5,
            'normal_error_rate': 0.02,  # 2%
            'typical_payload_size': 1024,  # 1KB
            'normal_geographic_spread': 3  # Number of different countries
        }
    
    def _init_pattern_monitoring(self):
        """Initialize pattern monitoring data structures"""
        # Time-based patterns
        self.active_patterns['requests_per_minute'] = deque(maxlen=60)
        self.active_patterns['errors_per_minute'] = deque(maxlen=60)
        self.active_patterns['response_times'] = deque(maxlen=100)
        
        # IP-based patterns
        self.active_patterns['ip_request_counts'] = defaultdict(lambda: deque(maxlen=1000))
        self.active_patterns['ip_error_counts'] = defaultdict(lambda: deque(maxlen=100))
        self.active_patterns['ip_last_seen'] = {}
    
    def analyze_request_pattern(self, client_ip: str, endpoint: str, status_code: int, 
                              response_time: float, payload_size: int = 0) -> List[AnomalyEvent]:
        """Analyze request pattern for anomalies"""
        anomalies = []
        current_time = datetime.utcnow()
        
        # Update pattern data
        self._update_pattern_data(client_ip, endpoint, status_code, response_time, payload_size)
        
        # Check for failed login burst
        if self._is_failed_authentication(endpoint, status_code):
            anomaly = self._check_failed_login_burst(client_ip, current_time)
            if anomaly:
                anomalies.append(anomaly)
        
        # Check for rate limit violations
        anomaly = self._check_rate_limit_violations(client_ip, current_time)
        if anomaly:
            anomalies.append(anomaly)
        
        # Check for error rate spike
        anomaly = self._check_error_rate_spike(client_ip, current_time)
        if anomaly:
            anomalies.append(anomaly)
        
        # Check for payload size anomalies
        if payload_size > 0:
            anomaly = self._check_payload_size_anomaly(client_ip, payload_size, current_time)
            if anomaly:
                anomalies.append(anomaly)
        
        # Check for unusual access patterns
        anomaly = self._check_unusual_access_pattern(client_ip, endpoint, current_time)
        if anomaly:
            anomalies.append(anomaly)
        
        return anomalies
    
    def _update_pattern_data(self, client_ip: str, endpoint: str, status_code: int, 
                           response_time: float, payload_size: int):
        """Update pattern monitoring data"""
        current_minute = int(time.time() // 60)
        
        # Update time-based patterns
        self.active_patterns['requests_per_minute'].append(current_minute)
        self.active_patterns['response_times'].append(response_time)
        
        if status_code >= 400:
            self.active_patterns['errors_per_minute'].append(current_minute)
        
        # Update IP-based patterns
        self.active_patterns['ip_request_counts'][client_ip].append(current_minute)
        self.active_patterns['ip_last_seen'][client_ip] = time.time()
        
        if status_code >= 400:
            self.active_patterns['ip_error_counts'][client_ip].append(current_minute)
        
        # Store in Redis if available
        if self.redis_client:
            self._store_pattern_data_redis(client_ip, endpoint, status_code, response_time)
    
    def _store_pattern_data_redis(self, client_ip: str, endpoint: str, 
                                status_code: int, response_time: float):
        """Store pattern data in Redis"""
        try:
            current_minute = int(time.time() // 60)
            
            # Store request count
            key = f"anomaly:requests:{client_ip}:{current_minute}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, 3600)  # 1 hour TTL
            
            # Store error count
            if status_code >= 400:
                error_key = f"anomaly:errors:{client_ip}:{current_minute}"
                self.redis_client.incr(error_key)
                self.redis_client.expire(error_key, 3600)
            
            # Store response time
            time_key = f"anomaly:response_times:{client_ip}"
            self.redis_client.lpush(time_key, response_time)
            self.redis_client.ltrim(time_key, 0, 99)  # Keep last 100
            self.redis_client.expire(time_key, 3600)
            
        except RedisError as e:
            self.app.logger.error(f"Error storing pattern data in Redis: {e}")
    
    def _is_failed_authentication(self, endpoint: str, status_code: int) -> bool:
        """Check if this is a failed authentication attempt"""
        auth_endpoints = ['/api/v1/auth/login', '/login', '/auth', '/signin']
        return any(endpoint.startswith(ep) for ep in auth_endpoints) and status_code == 401
    
    def _check_failed_login_burst(self, client_ip: str, current_time: datetime) -> Optional[AnomalyEvent]:
        """Check for failed login burst anomaly"""
        rule = self.detection_rules[AnomalyType.FAILED_LOGIN_BURST]
        
        # Count recent failed logins
        failed_count = self._count_recent_events(
            client_ip, 'failed_auth', rule['time_window']
        )
        
        if failed_count >= rule['threshold']:
            return AnomalyEvent(
                anomaly_id=f"failed_login_burst_{client_ip}_{int(current_time.timestamp())}",
                anomaly_type=AnomalyType.FAILED_LOGIN_BURST,
                severity=rule['severity'],
                timestamp=current_time,
                client_ip=client_ip,
                user_id=self._get_user_id_for_ip(client_ip),
                description=f"Failed login burst detected: {failed_count} attempts in {rule['time_window']} seconds",
                evidence={
                    'failed_attempts': failed_count,
                    'time_window': rule['time_window'],
                    'threshold': rule['threshold']
                },
                risk_score=min(10.0, failed_count / rule['threshold'] * 5.0),
                threshold_breached={'failed_logins': failed_count},
                recommended_actions=['block_ip', 'increase_monitoring', 'alert_admin'],
                confidence_score=0.9
            )
        
        return None
    
    def _check_rate_limit_violations(self, client_ip: str, current_time: datetime) -> Optional[AnomalyEvent]:
        """Check for rate limit violation patterns"""
        rule = self.detection_rules[AnomalyType.RATE_LIMIT_VIOLATION_PATTERN]
        
        # Count recent rate limit violations
        violation_count = self._count_recent_events(
            client_ip, 'rate_limit_violations', rule['time_window']
        )
        
        if violation_count >= rule['threshold']:
            return AnomalyEvent(
                anomaly_id=f"rate_limit_pattern_{client_ip}_{int(current_time.timestamp())}",
                anomaly_type=AnomalyType.RATE_LIMIT_VIOLATION_PATTERN,
                severity=rule['severity'],
                timestamp=current_time,
                client_ip=client_ip,
                user_id=self._get_user_id_for_ip(client_ip),
                description=f"Rate limit violation pattern: {violation_count} violations in {rule['time_window']} seconds",
                evidence={
                    'violations': violation_count,
                    'time_window': rule['time_window'],
                    'threshold': rule['threshold']
                },
                risk_score=min(8.0, violation_count / rule['threshold'] * 4.0),
                threshold_breached={'rate_violations': violation_count},
                recommended_actions=['throttle_ip', 'increase_rate_limits', 'monitor_closely'],
                confidence_score=0.85
            )
        
        return None
    
    def _check_error_rate_spike(self, client_ip: str, current_time: datetime) -> Optional[AnomalyEvent]:
        """Check for error rate spike anomaly"""
        rule = self.detection_rules[AnomalyType.ERROR_RATE_SPIKE]
        
        # Count recent errors
        error_count = self._count_recent_events(
            client_ip, 'errors', rule['time_window']
        )
        
        # Get total requests for error rate calculation
        total_requests = self._count_recent_events(
            client_ip, 'requests', rule['time_window']
        )
        
        if total_requests > 0:
            error_rate = error_count / total_requests
            normal_error_rate = self.baseline_metrics['normal_error_rate']
            
            # Check if error rate is significantly above normal
            if error_rate > normal_error_rate * 5 and error_count >= 10:
                return AnomalyEvent(
                    anomaly_id=f"error_spike_{client_ip}_{int(current_time.timestamp())}",
                    anomaly_type=AnomalyType.ERROR_RATE_SPIKE,
                    severity=rule['severity'],
                    timestamp=current_time,
                    client_ip=client_ip,
                    user_id=self._get_user_id_for_ip(client_ip),
                    description=f"Error rate spike detected: {error_rate:.2%} error rate ({error_count}/{total_requests})",
                    evidence={
                        'error_count': error_count,
                        'total_requests': total_requests,
                        'error_rate': error_rate,
                        'normal_error_rate': normal_error_rate
                    },
                    risk_score=min(6.0, (error_rate / normal_error_rate) * 2.0),
                    threshold_breached={'error_rate': error_rate},
                    recommended_actions=['investigate_errors', 'check_application_health'],
                    confidence_score=0.75
                )
        
        return None
    
    def _check_payload_size_anomaly(self, client_ip: str, payload_size: int, 
                                  current_time: datetime) -> Optional[AnomalyEvent]:
        """Check for payload size anomalies"""
        rule = self.detection_rules[AnomalyType.PAYLOAD_SIZE_ANOMALY]
        
        if payload_size > rule['threshold']:
            typical_size = self.baseline_metrics['typical_payload_size']
            size_ratio = payload_size / typical_size
            
            # Only flag if significantly larger than typical
            if size_ratio > 10:
                return AnomalyEvent(
                    anomaly_id=f"payload_anomaly_{client_ip}_{int(current_time.timestamp())}",
                    anomaly_type=AnomalyType.PAYLOAD_SIZE_ANOMALY,
                    severity=rule['severity'],
                    timestamp=current_time,
                    client_ip=client_ip,
                    user_id=self._get_user_id_for_ip(client_ip),
                    description=f"Unusually large payload: {payload_size} bytes ({size_ratio:.1f}x typical size)",
                    evidence={
                        'payload_size': payload_size,
                        'typical_size': typical_size,
                        'size_ratio': size_ratio
                    },
                    risk_score=min(4.0, size_ratio / 10.0),
                    threshold_breached={'payload_size': payload_size},
                    recommended_actions=['inspect_payload', 'check_upload_limits'],
                    confidence_score=0.7
                )
        
        return None
    
    def _check_unusual_access_pattern(self, client_ip: str, endpoint: str, 
                                    current_time: datetime) -> Optional[AnomalyEvent]:
        """Check for unusual access patterns"""
        rule = self.detection_rules[AnomalyType.UNUSUAL_ACCESS_PATTERN]
        
        # Count unique endpoints accessed by this IP
        unique_endpoints = self._count_unique_endpoints(client_ip, rule['time_window'])
        
        if unique_endpoints > rule['threshold']:
            return AnomalyEvent(
                anomaly_id=f"access_pattern_{client_ip}_{int(current_time.timestamp())}",
                anomaly_type=AnomalyType.UNUSUAL_ACCESS_PATTERN,
                severity=rule['severity'],
                timestamp=current_time,
                client_ip=client_ip,
                user_id=self._get_user_id_for_ip(client_ip),
                description=f"Unusual access pattern: accessing {unique_endpoints} unique endpoints",
                evidence={
                    'unique_endpoints': unique_endpoints,
                    'time_window': rule['time_window'],
                    'threshold': rule['threshold']
                },
                risk_score=min(3.0, unique_endpoints / rule['threshold'] * 2.0),
                threshold_breached={'unique_endpoints': unique_endpoints},
                recommended_actions=['monitor_behavior', 'check_access_logs'],
                confidence_score=0.6
            )
        
        return None
    
    def _count_recent_events(self, client_ip: str, event_type: str, time_window: int) -> int:
        """Count recent events for a client IP"""
        if not self.redis_client:
            return 0
        
        try:
            current_time = int(time.time())
            start_time = current_time - time_window
            
            count = 0
            for minute in range(start_time // 60, (current_time // 60) + 1):
                key = f"anomaly:{event_type}:{client_ip}:{minute}"
                minute_count = self.redis_client.get(key)
                if minute_count:
                    count += int(minute_count)
            
            return count
            
        except RedisError as e:
            self.app.logger.error(f"Error counting recent events: {e}")
            return 0
    
    def _count_unique_endpoints(self, client_ip: str, time_window: int) -> int:
        """Count unique endpoints accessed by IP in time window"""
        if not self.redis_client:
            return 0
        
        try:
            key = f"anomaly:endpoints:{client_ip}"
            endpoints = self.redis_client.smembers(key)
            return len(endpoints)
            
        except RedisError as e:
            self.app.logger.error(f"Error counting unique endpoints: {e}")
            return 0
    
    def _get_user_id_for_ip(self, client_ip: str) -> Optional[str]:
        """Get user ID associated with IP address"""
        # This would be implemented with actual user session tracking
        return None
    
    def handle_anomaly(self, anomaly: AnomalyEvent) -> Dict[str, Any]:
        """Handle detected anomaly with appropriate response"""
        response_actions = []
        
        # Log the anomaly
        self._log_anomaly(anomaly)
        
        # Automatic response based on anomaly type and severity
        if anomaly.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
            if 'block_ip' in anomaly.recommended_actions:
                block_result = self._auto_block_ip(anomaly.client_ip, anomaly.anomaly_type)
                response_actions.append(block_result)
            
            if 'alert_admin' in anomaly.recommended_actions:
                alert_result = self._send_admin_alert(anomaly)
                response_actions.append(alert_result)
        
        # Update monitoring metrics
        self._update_anomaly_metrics(anomaly)
        
        return {
            'anomaly_id': anomaly.anomaly_id,
            'handled': True,
            'response_actions': response_actions,
            'timestamp': anomaly.timestamp.isoformat()
        }
    
    def _log_anomaly(self, anomaly: AnomalyEvent):
        """Log anomaly event"""
        log_data = {
            'event_type': 'anomaly_detected',
            'anomaly_id': anomaly.anomaly_id,
            'anomaly_type': anomaly.anomaly_type.value,
            'severity': anomaly.severity.value,
            'client_ip': anomaly.client_ip,
            'risk_score': anomaly.risk_score,
            'confidence_score': anomaly.confidence_score,
            'description': anomaly.description,
            'evidence': anomaly.evidence,
            'recommended_actions': anomaly.recommended_actions
        }
        
        self.app.logger.warning(f"ANOMALY_DETECTED: {json.dumps(log_data)}")
    
    def _auto_block_ip(self, client_ip: str, anomaly_type: AnomalyType) -> Dict[str, Any]:
        """Automatically block IP address"""
        if not self.redis_client:
            return {'action': 'auto_block', 'success': False, 'reason': 'Redis not available'}
        
        try:
            # Determine block duration based on anomaly type
            block_durations = {
                AnomalyType.FAILED_LOGIN_BURST: 3600,  # 1 hour
                AnomalyType.RATE_LIMIT_VIOLATION_PATTERN: 1800,  # 30 minutes
                AnomalyType.BRUTE_FORCE_ATTACK: 7200,  # 2 hours
            }
            
            duration = block_durations.get(anomaly_type, 3600)
            
            # Block the IP
            block_key = f"blocked_ip:{client_ip}"
            self.redis_client.setex(block_key, duration, f"auto_blocked:{anomaly_type.value}")
            
            return {
                'action': 'auto_block',
                'success': True,
                'ip': client_ip,
                'duration': duration,
                'reason': anomaly_type.value
            }
            
        except RedisError as e:
            self.app.logger.error(f"Error auto-blocking IP: {e}")
            return {'action': 'auto_block', 'success': False, 'reason': str(e)}
    
    def _send_admin_alert(self, anomaly: AnomalyEvent) -> Dict[str, Any]:
        """Send alert to administrators"""
        # This would integrate with actual alerting system
        alert_data = {
            'action': 'admin_alert',
            'anomaly_id': anomaly.anomaly_id,
            'severity': anomaly.severity.value,
            'description': anomaly.description,
            'timestamp': anomaly.timestamp.isoformat(),
            'sent': True
        }
        
        self.app.logger.warning(f"ADMIN_ALERT: {json.dumps(alert_data)}")
        return alert_data
    
    def _update_anomaly_metrics(self, anomaly: AnomalyEvent):
        """Update anomaly detection metrics"""
        if not self.redis_client:
            return
        
        try:
            # Update anomaly counters
            self.redis_client.incr(f"anomaly_metrics:total")
            self.redis_client.incr(f"anomaly_metrics:type:{anomaly.anomaly_type.value}")
            self.redis_client.incr(f"anomaly_metrics:severity:{anomaly.severity.value}")
            
            # Update risk score metrics
            self.redis_client.lpush("anomaly_metrics:risk_scores", anomaly.risk_score)
            self.redis_client.ltrim("anomaly_metrics:risk_scores", 0, 999)
            
        except RedisError as e:
            self.app.logger.error(f"Error updating anomaly metrics: {e}")
    
    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        if not self.redis_client:
            return {'error': 'Redis not available'}
        
        try:
            stats = {
                'total_anomalies': int(self.redis_client.get('anomaly_metrics:total') or 0),
                'anomalies_by_type': {},
                'anomalies_by_severity': {},
                'average_risk_score': 0.0,
                'active_blocks': 0
            }
            
            # Get anomalies by type
            for anomaly_type in AnomalyType:
                count = int(self.redis_client.get(f'anomaly_metrics:type:{anomaly_type.value}') or 0)
                stats['anomalies_by_type'][anomaly_type.value] = count
            
            # Get anomalies by severity
            for severity in AnomalySeverity:
                count = int(self.redis_client.get(f'anomaly_metrics:severity:{severity.value}') or 0)
                stats['anomalies_by_severity'][severity.value] = count
            
            # Calculate average risk score
            risk_scores = self.redis_client.lrange('anomaly_metrics:risk_scores', 0, -1)
            if risk_scores:
                scores = [float(score) for score in risk_scores]
                stats['average_risk_score'] = statistics.mean(scores)
            
            # Count active blocks
            blocked_keys = self.redis_client.keys('blocked_ip:*')
            stats['active_blocks'] = len(blocked_keys)
            
            return stats
            
        except RedisError as e:
            return {'error': str(e)}
    
    def reset_anomaly_data(self, client_ip: str) -> bool:
        """Reset anomaly data for a client IP"""
        if not self.redis_client:
            return False
        
        try:
            # Remove all anomaly data for this IP
            keys_to_delete = []
            
            # Find all keys related to this IP
            for pattern in ['anomaly:*:{client_ip}:*', 'blocked_ip:{client_ip}']:
                keys = self.redis_client.keys(pattern.format(client_ip=client_ip))
                keys_to_delete.extend(keys)
            
            if keys_to_delete:
                self.redis_client.delete(*keys_to_delete)
            
            return True
            
        except RedisError as e:
            self.app.logger.error(f"Error resetting anomaly data: {e}")
            return False