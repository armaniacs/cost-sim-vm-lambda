"""
Comprehensive security audit logging system for compliance and monitoring.

This module provides:
- Structured security event logging
- ISO8601 timestamp formatting
- Event classification and categorization
- Audit trail management
- Compliance reporting capabilities
"""

import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from flask import Flask, request, g, current_app
import structlog


class SecurityEventType(Enum):
    """Security event types for categorization"""
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INPUT_VALIDATION_FAILURE = "input_validation_failure"
    CSRF_ATTACK_DETECTED = "csrf_attack_detected"
    XSS_ATTACK_DETECTED = "xss_attack_detected"
    SQL_INJECTION_DETECTED = "sql_injection_detected"
    DATA_INTEGRITY_VIOLATION = "data_integrity_violation"
    SECURITY_HEADER_VIOLATION = "security_header_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_SCAN_RESULT = "security_scan_result"


class SecurityEventSeverity(Enum):
    """Security event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: str
    user_id: Optional[str]
    session_id: Optional[str]
    client_ip: str
    user_agent: str
    endpoint: str
    method: str
    status_code: Optional[int]
    request_id: Optional[str]
    trace_id: Optional[str]
    description: str
    details: Dict[str, Any]
    risk_score: float
    compliance_tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to their values
        result['event_type'] = self.event_type.value
        result['severity'] = self.severity.value
        return result


class SecurityAuditLogger:
    """Comprehensive security audit logging system"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.logger = None
        self.event_processors = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize audit logger with Flask app"""
        self.app = app
        
        # Get audit logging configuration
        audit_config = self.config.get('audit_logging', {})
        
        if not audit_config.get('enabled', True):
            app.logger.info("Security audit logging is disabled")
            return
        
        # Initialize structured logger
        self._init_structured_logger(audit_config)
        
        # Register event processors
        self._register_event_processors()
        
        # Register audit middleware
        self._register_audit_middleware(app)
        
        app.logger.info("Security audit logger initialized")
    
    def _init_structured_logger(self, config: Dict[str, Any]):
        """Initialize structured logger with proper configuration"""
        try:
            # Configure structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            
            self.logger = structlog.get_logger("security_audit")
        except Exception as e:
            # Fallback to Flask logger if structlog configuration fails
            self.app.logger.warning(f"Failed to configure structlog, using Flask logger: {e}")
            self.logger = self.app.logger
    
    def _register_event_processors(self):
        """Register event processors for different event types"""
        self.event_processors = [
            self._process_authentication_events,
            self._process_authorization_events,
            self._process_attack_events,
            self._process_system_events
        ]
    
    def _register_audit_middleware(self, app: Flask):
        """Register audit logging middleware"""
        
        @app.before_request
        def before_request_audit():
            """Initialize audit context before request processing"""
            # Generate request ID if not present
            if not hasattr(g, 'request_id'):
                g.request_id = str(uuid.uuid4())
            
            # Initialize audit context
            g.audit_context = {
                'request_start_time': time.time(),
                'client_ip': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'endpoint': request.endpoint or request.path,
                'method': request.method,
                'content_length': request.content_length or 0
            }
        
        @app.after_request
        def after_request_audit(response):
            """Log audit information after request processing"""
            if hasattr(g, 'audit_context'):
                # Calculate request duration
                duration = time.time() - g.audit_context.get('request_start_time', time.time())
                
                # Create basic access log event
                self._log_access_event(response, duration)
            
            return response
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        risk_score: float = 0.0,
        compliance_tags: Optional[List[str]] = None
    ) -> str:
        """Log a security event"""
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Get request context
        client_ip = self._get_client_ip()
        user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
        endpoint = request.endpoint or request.path if request else 'unknown'
        method = request.method if request else 'unknown'
        status_code = None  # Will be set by response middleware
        request_id = getattr(g, 'request_id', None) if request else None
        trace_id = getattr(g, 'trace_id', None) if request else None
        session_id = self._get_session_id() if request else None
        
        # Create security event
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=timestamp,
            user_id=user_id or self._get_current_user_id(),
            session_id=session_id,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_id=request_id,
            trace_id=trace_id,
            description=description,
            details=details or {},
            risk_score=risk_score,
            compliance_tags=compliance_tags or []
        )
        
        # Process event through processors
        self._process_event(event)
        
        # Log the event
        self._write_audit_log(event)
        
        return event_id
    
    def _log_access_event(self, response, duration: float):
        """Log general access event"""
        if not hasattr(g, 'audit_context'):
            return
        
        audit_context = g.audit_context
        
        # Determine event type based on response
        if response.status_code >= 500:
            event_type = SecurityEventType.SYSTEM_ERROR
            severity = SecurityEventSeverity.HIGH
        elif response.status_code >= 400:
            event_type = SecurityEventType.ACCESS_DENIED
            severity = SecurityEventSeverity.MEDIUM
        else:
            event_type = SecurityEventType.ACCESS_GRANTED
            severity = SecurityEventSeverity.INFO
        
        details = {
            'status_code': response.status_code,
            'response_size': response.content_length or 0,
            'duration_ms': round(duration * 1000, 2),
            'content_type': response.content_type
        }
        
        self.log_security_event(
            event_type=event_type,
            severity=severity,
            description=f"HTTP {audit_context['method']} request to {audit_context['endpoint']}",
            details=details,
            risk_score=self._calculate_risk_score(response.status_code, duration)
        )
    
    def _process_event(self, event: SecurityEvent):
        """Process event through registered processors"""
        for processor in self.event_processors:
            try:
                processor(event)
            except Exception as e:
                self.app.logger.error(f"Error in event processor: {e}")
    
    def _process_authentication_events(self, event: SecurityEvent):
        """Process authentication-related events"""
        if event.event_type in [SecurityEventType.AUTHENTICATION_SUCCESS, SecurityEventType.AUTHENTICATION_FAILURE]:
            # Add authentication-specific compliance tags
            event.compliance_tags.extend(['authentication', 'access_control', 'audit'])
            
            # Increase risk score for failed authentication
            if event.event_type == SecurityEventType.AUTHENTICATION_FAILURE:
                event.risk_score += 2.0
    
    def _process_authorization_events(self, event: SecurityEvent):
        """Process authorization-related events"""
        if event.event_type in [SecurityEventType.AUTHORIZATION_SUCCESS, SecurityEventType.AUTHORIZATION_FAILURE]:
            # Add authorization-specific compliance tags
            event.compliance_tags.extend(['authorization', 'access_control', 'privilege_management'])
            
            # Increase risk score for authorization failures
            if event.event_type == SecurityEventType.AUTHORIZATION_FAILURE:
                event.risk_score += 1.5
    
    def _process_attack_events(self, event: SecurityEvent):
        """Process attack-related events"""
        attack_events = [
            SecurityEventType.XSS_ATTACK_DETECTED,
            SecurityEventType.SQL_INJECTION_DETECTED,
            SecurityEventType.CSRF_ATTACK_DETECTED
        ]
        
        if event.event_type in attack_events:
            # Add security attack compliance tags
            event.compliance_tags.extend(['security_attack', 'threat_detection', 'incident'])
            
            # High risk score for attacks
            event.risk_score += 5.0
            event.severity = SecurityEventSeverity.HIGH
    
    def _process_system_events(self, event: SecurityEvent):
        """Process system-related events"""
        if event.event_type == SecurityEventType.SYSTEM_ERROR:
            # Add system error compliance tags
            event.compliance_tags.extend(['system_error', 'availability'])
            
            # Moderate risk score for system errors
            event.risk_score += 1.0
    
    def _write_audit_log(self, event: SecurityEvent):
        """Write audit log entry"""
        if not self.logger:
            return
        
        log_data = event.to_dict()
        
        # Add additional metadata
        log_data.update({
            'log_version': '1.0',
            'source': 'security_audit_logger',
            'environment': self._get_environment()
        })
        
        try:
            if hasattr(self.logger, 'info'):
                # Use structlog
                self.logger.info(
                    "Security audit event",
                    **log_data
                )
            else:
                # Use Flask logger
                self.app.logger.info(f"SECURITY_AUDIT: {json.dumps(log_data)}")
        except Exception as e:
            self.app.logger.error(f"Failed to write audit log: {e}")
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        if not request:
            return 'unknown'
        
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or '127.0.0.1'
    
    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from request context"""
        if not request:
            return None
        
        # Try to get user from Flask-Login or similar
        if hasattr(g, 'current_user'):
            user = g.current_user
            if hasattr(user, 'id'):
                return str(user.id)
            elif hasattr(user, 'get_id'):
                return user.get_id()
        
        return None
    
    def _get_session_id(self) -> Optional[str]:
        """Get session ID"""
        if not request:
            return None
        
        # Try to get session ID from Flask session
        try:
            from flask import session
            return session.get('session_id') or session.sid
        except Exception:
            return None
    
    def _get_environment(self) -> str:
        """Get current environment"""
        if self.app:
            return self.app.config.get('ENV', 'unknown')
        return 'unknown'
    
    def _calculate_risk_score(self, status_code: int, duration: float) -> float:
        """Calculate risk score based on request characteristics"""
        risk_score = 0.0
        
        # Status code risk
        if status_code >= 500:
            risk_score += 2.0
        elif status_code >= 400:
            risk_score += 1.0
        
        # Duration risk
        if duration > 10.0:  # More than 10 seconds
            risk_score += 1.5
        elif duration > 5.0:  # More than 5 seconds
            risk_score += 0.5
        
        return risk_score
    
    def get_audit_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get audit statistics for a date range"""
        # This would be implemented with actual data storage
        return {
            'total_events': 0,
            'events_by_type': {},
            'events_by_severity': {},
            'high_risk_events': 0,
            'compliance_violations': 0,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    def export_audit_trail(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[SecurityEventType]] = None,
        severity_levels: Optional[List[SecurityEventSeverity]] = None
    ) -> List[Dict[str, Any]]:
        """Export audit trail for compliance reporting"""
        # This would be implemented with actual data storage
        return []
    
    def validate_audit_integrity(self) -> Dict[str, Any]:
        """Validate audit log integrity"""
        # This would implement hash-based integrity checking
        return {
            'integrity_valid': True,
            'total_logs_checked': 0,
            'integrity_violations': 0,
            'last_check': datetime.now(timezone.utc).isoformat()
        }