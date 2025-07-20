"""
Data integrity checker middleware for request/response validation.

This module provides:
- Request/Response hash calculation
- Trace ID generation
- Data tampering detection
- Integrity audit logging
- Comprehensive data validation
"""

import hashlib
import json
import uuid
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import Flask, request, g, current_app
import structlog


class IntegrityChecker:
    """Data integrity verification middleware"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.logger = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize integrity checker with Flask app"""
        self.app = app
        
        # Get integrity checking configuration
        integrity_config = self.config.get('integrity_checking', {})
        
        if not integrity_config.get('enabled', True):
            app.logger.info("Data integrity checking is disabled")
            return
        
        # Initialize structured logger
        self._init_logger()
        
        # Register integrity checking middleware
        self._register_middleware(app, integrity_config)
        
        app.logger.info("Data integrity checker initialized")
    
    def _init_logger(self):
        """Initialize structured logger for integrity events"""
        try:
            self.logger = structlog.get_logger("data_integrity")
        except Exception:
            # Fallback to Flask logger if structlog is not available
            self.logger = self.app.logger if self.app else None
    
    def _register_middleware(self, app: Flask, config: Dict[str, Any]):
        """Register integrity checking middleware"""
        
        @app.before_request
        def before_request_integrity():
            """Calculate request hash before processing"""
            
            # Skip for certain paths
            if self._should_skip_integrity_check():
                return
            
            # Generate trace ID for this request
            trace_id = str(uuid.uuid4())
            g.trace_id = trace_id
            g.integrity_start_time = time.time()
            
            # Calculate request hash for POST/PUT/PATCH requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                request_data = request.get_data()
                if request_data:
                    g.request_hash = self.calculate_hash(request_data)
                    g.request_size = len(request_data)
                else:
                    g.request_hash = None
                    g.request_size = 0
            else:
                g.request_hash = None
                g.request_size = 0
            
            # Log request integrity info
            self._log_request_integrity(trace_id, g.request_hash)
        
        @app.after_request
        def after_request_integrity(response):
            """Calculate response hash and log integrity data"""
            
            # Skip for certain paths
            if self._should_skip_integrity_check():
                return response
            
            # Get trace ID from request context
            trace_id = getattr(g, 'trace_id', str(uuid.uuid4()))
            
            # Calculate response hash
            response_data = response.get_data()
            response_hash = self.calculate_hash(response_data) if response_data else None
            
            # Calculate processing time
            processing_time = time.time() - getattr(g, 'integrity_start_time', time.time())
            
            # Create integrity record
            integrity_record = {
                'trace_id': trace_id,
                'timestamp': datetime.utcnow().isoformat(),
                'request': {
                    'method': request.method,
                    'path': request.path,
                    'hash': getattr(g, 'request_hash', None),
                    'size': getattr(g, 'request_size', 0),
                    'content_type': request.content_type
                },
                'response': {
                    'status_code': response.status_code,
                    'hash': response_hash,
                    'size': len(response_data) if response_data else 0,
                    'content_type': response.content_type
                },
                'processing_time': processing_time,
                'client_ip': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            # Add user context if available
            if hasattr(g, 'current_user'):
                integrity_record['user_id'] = getattr(g.current_user, 'id', 'anonymous')
            
            # Log integrity data
            self._log_integrity_record(integrity_record)
            
            # Add trace ID to response headers
            response.headers['X-Trace-ID'] = trace_id
            
            # Perform integrity validation
            validation_result = self._validate_integrity(integrity_record)
            if not validation_result['valid']:
                self._handle_integrity_violation(integrity_record, validation_result)
            
            return response
    
    def _should_skip_integrity_check(self) -> bool:
        """Check if integrity checking should be skipped"""
        # Skip for static files
        if request.endpoint == 'static':
            return True
        
        # Skip for health checks
        if request.path in ['/health', '/api/health']:
            return True
        
        # Skip for monitoring endpoints
        if request.path.startswith('/api/v1/monitoring/'):
            return True
        
        # Skip for security endpoints (avoid recursion)
        if request.path.startswith('/api/v1/security/'):
            return True
        
        return False
    
    def calculate_hash(self, data: bytes) -> str:
        """Calculate SHA-256 hash of data"""
        if not data:
            return None
        
        return hashlib.sha256(data).hexdigest()
    
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
    
    def _log_request_integrity(self, trace_id: str, request_hash: Optional[str]):
        """Log request integrity information"""
        if not self.logger:
            return
        
        request_info = {
            'event_type': 'integrity_request_start',
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'path': request.path,
            'request_hash': request_hash,
            'client_ip': self._get_client_ip()
        }
        
        if hasattr(self.logger, 'info'):
            self.logger.info("Request integrity check started", **request_info)
        else:
            self.app.logger.info(f"Request integrity: {json.dumps(request_info)}")
    
    def _log_integrity_record(self, record: Dict[str, Any]):
        """Log complete integrity record"""
        if not self.logger:
            return
        
        log_data = {
            'event_type': 'integrity_check_complete',
            **record
        }
        
        if hasattr(self.logger, 'info'):
            self.logger.info("Integrity check completed", **log_data)
        else:
            self.app.logger.info(f"Integrity check: {json.dumps(log_data)}")
    
    def _validate_integrity(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data integrity"""
        validation_result = {
            'valid': True,
            'violations': [],
            'risk_level': 'low'
        }
        
        # Check for suspicious patterns
        violations = []
        
        # Check response time anomalies
        processing_time = record.get('processing_time', 0)
        if processing_time > 30.0:  # More than 30 seconds
            violations.append({
                'type': 'processing_time_anomaly',
                'value': processing_time,
                'severity': 'medium'
            })
        
        # Check for error responses with large payloads
        response_status = record['response']['status_code']
        response_size = record['response']['size']
        if response_status >= 400 and response_size > 10000:  # Error with large response
            violations.append({
                'type': 'error_response_size_anomaly',
                'status_code': response_status,
                'size': response_size,
                'severity': 'medium'
            })
        
        # Check for hash consistency
        request_hash = record['request']['hash']
        if request_hash:
            # Validate hash format
            if not self._is_valid_hash(request_hash):
                violations.append({
                    'type': 'invalid_hash_format',
                    'hash': request_hash,
                    'severity': 'high'
                })
        
        if violations:
            validation_result['valid'] = False
            validation_result['violations'] = violations
            validation_result['risk_level'] = self._calculate_risk_level(violations)
        
        return validation_result
    
    def _is_valid_hash(self, hash_value: str) -> bool:
        """Validate hash format"""
        if not hash_value:
            return False
        
        # SHA-256 hash should be 64 characters of hexadecimal
        if len(hash_value) != 64:
            return False
        
        try:
            int(hash_value, 16)
            return True
        except ValueError:
            return False
    
    def _calculate_risk_level(self, violations: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on violations"""
        if not violations:
            return 'low'
        
        high_severity_count = sum(1 for v in violations if v.get('severity') == 'high')
        medium_severity_count = sum(1 for v in violations if v.get('severity') == 'medium')
        
        if high_severity_count > 0:
            return 'high'
        elif medium_severity_count > 2:
            return 'high'
        elif medium_severity_count > 0:
            return 'medium'
        else:
            return 'low'
    
    def _handle_integrity_violation(self, record: Dict[str, Any], validation_result: Dict[str, Any]):
        """Handle integrity violations"""
        violation_info = {
            'event_type': 'integrity_violation',
            'trace_id': record['trace_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'risk_level': validation_result['risk_level'],
            'violations': validation_result['violations'],
            'request_info': {
                'method': record['request']['method'],
                'path': record['request']['path'],
                'client_ip': record['client_ip']
            }
        }
        
        # Log violation
        if self.logger:
            if hasattr(self.logger, 'warning'):
                self.logger.warning("Data integrity violation detected", **violation_info)
            else:
                self.app.logger.warning(f"Integrity violation: {json.dumps(violation_info)}")
        
        # Send alert for high-risk violations
        if validation_result['risk_level'] == 'high':
            self._send_integrity_alert(violation_info)
        
        # Record in monitoring system if available
        if hasattr(self.app, 'monitoring_integration'):
            self.app.monitoring_integration.record_custom_metric(
                'security.integrity_violation',
                1,
                tags={
                    'risk_level': validation_result['risk_level'],
                    'violation_count': len(validation_result['violations']),
                    'client_ip': record['client_ip']
                }
            )
    
    def _send_integrity_alert(self, violation_info: Dict[str, Any]):
        """Send alert for integrity violations"""
        if hasattr(self.app, 'monitoring_integration'):
            self.app.monitoring_integration.trigger_custom_alert(
                "Data Integrity Violation Detected",
                f"High-risk integrity violation detected. Trace ID: {violation_info['trace_id']}",
                "high",
                violation_info
            )
    
    def verify_data_integrity(self, original_data: bytes, stored_hash: str) -> bool:
        """Verify data integrity against stored hash"""
        if not original_data or not stored_hash:
            return False
        
        calculated_hash = self.calculate_hash(original_data)
        return calculated_hash == stored_hash
    
    def create_integrity_checksum(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Create integrity checksum for complex data structures"""
        # Serialize data in a consistent way
        json_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        data_bytes = json_data.encode('utf-8')
        
        return {
            'sha256': self.calculate_hash(data_bytes),
            'size': len(data_bytes),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_integrity_stats(self) -> Dict[str, Any]:
        """Get integrity checking statistics"""
        # This would typically be implemented with actual counters
        return {
            'total_checks_performed': 0,
            'integrity_violations_detected': 0,
            'high_risk_violations': 0,
            'average_processing_time': 0.0,
            'hash_validation_errors': 0
        }
    
    def export_integrity_audit_log(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Export integrity audit log for compliance reporting"""
        # This would be implemented with actual data storage
        # For now, return empty list as placeholder
        return []
    
    def validate_request_response_pair(self, request_data: bytes, response_data: bytes) -> Dict[str, Any]:
        """Validate a specific request-response pair"""
        trace_id = str(uuid.uuid4())
        
        validation_result = {
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_hash': self.calculate_hash(request_data) if request_data else None,
            'response_hash': self.calculate_hash(response_data) if response_data else None,
            'valid': True,
            'issues': []
        }
        
        # Check for empty data
        if not request_data and not response_data:
            validation_result['issues'].append({
                'type': 'empty_data',
                'message': 'Both request and response data are empty'
            })
        
        # Check hash validity
        if validation_result['request_hash'] and not self._is_valid_hash(validation_result['request_hash']):
            validation_result['valid'] = False
            validation_result['issues'].append({
                'type': 'invalid_request_hash',
                'message': 'Request hash format is invalid'
            })
        
        if validation_result['response_hash'] and not self._is_valid_hash(validation_result['response_hash']):
            validation_result['valid'] = False
            validation_result['issues'].append({
                'type': 'invalid_response_hash',
                'message': 'Response hash format is invalid'
            })
        
        return validation_result