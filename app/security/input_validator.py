"""
Input validation middleware for XSS and SQL injection prevention.

This module provides:
- Request data sanitization
- XSS prevention
- SQL injection detection
- Input size validation
- Content type validation
- Malicious pattern detection
"""

import re
import json
import html
from typing import Dict, List, Any, Optional, Union
from urllib.parse import unquote
from flask import Flask, request, jsonify, current_app
import bleach


class InputValidator:
    """Input validation middleware for comprehensive security"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.blocked_patterns = []
        self.sql_patterns = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize input validator with Flask app"""
        self.app = app
        
        # Get input validation configuration
        validation_config = self.config.get('input_validation', {})
        
        if not validation_config.get('enabled', True):
            app.logger.info("Input validation is disabled")
            return
        
        # Compile patterns
        self._compile_patterns(validation_config)
        
        # Register input validation middleware
        self._register_middleware(app, validation_config)
        
        app.logger.info("Input validation initialized")
    
    def _compile_patterns(self, config: Dict[str, Any]):
        """Compile regex patterns for validation"""
        blocked_patterns = config.get('blocked_patterns', [])
        sql_patterns = config.get('sql_injection_patterns', [])
        
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in blocked_patterns
        ]
        
        self.sql_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in sql_patterns
        ]
    
    def _register_middleware(self, app: Flask, config: Dict[str, Any]):
        """Register input validation middleware"""
        
        @app.before_request
        def validate_input():
            """Validate input before processing request"""
            
            # Skip validation for certain paths
            if self._should_skip_validation():
                return
            
            # Check request size
            if not self._validate_request_size(config):
                return jsonify({'error': 'Request too large'}), 413
            
            # Validate content type
            if not self._validate_content_type(config):
                return jsonify({'error': 'Invalid content type'}), 415
            
            # Validate and sanitize request data
            validation_result = self._validate_request_data(config)
            if not validation_result['valid']:
                return jsonify({
                    'error': 'Invalid input',
                    'details': validation_result['errors']
                }), 400
            
            # Log suspicious activity
            if validation_result.get('suspicious'):
                self._log_suspicious_activity(validation_result['suspicious'])
    
    def _should_skip_validation(self) -> bool:
        """Check if validation should be skipped"""
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
    
    def _validate_request_size(self, config: Dict[str, Any]) -> bool:
        """Validate request size"""
        max_size = config.get('max_request_size', 10485760)  # 10MB default
        
        content_length = request.content_length
        if content_length and content_length > max_size:
            return False
        
        return True
    
    def _validate_content_type(self, config: Dict[str, Any]) -> bool:
        """Validate content type"""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        content_type = request.content_type
        if not content_type:
            return False
        
        # Allow common content types
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        ]
        
        return any(content_type.startswith(allowed_type) for allowed_type in allowed_types)
    
    def _validate_request_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize request data"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        # Validate JSON data
        if request.is_json:
            json_result = self._validate_json_data(request.get_json(), config)
            result['valid'] = result['valid'] and json_result['valid']
            result['errors'].extend(json_result['errors'])
            result['suspicious'].extend(json_result['suspicious'])
        
        # Validate form data
        if request.form:
            form_result = self._validate_form_data(request.form, config)
            result['valid'] = result['valid'] and form_result['valid']
            result['errors'].extend(form_result['errors'])
            result['suspicious'].extend(form_result['suspicious'])
        
        # Validate query parameters
        if request.args:
            args_result = self._validate_query_params(request.args, config)
            result['valid'] = result['valid'] and args_result['valid']
            result['errors'].extend(args_result['errors'])
            result['suspicious'].extend(args_result['suspicious'])
        
        # Validate headers
        headers_result = self._validate_headers(request.headers, config)
        result['valid'] = result['valid'] and headers_result['valid']
        result['errors'].extend(headers_result['errors'])
        result['suspicious'].extend(headers_result['suspicious'])
        
        return result
    
    def _validate_json_data(self, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON data"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        if not data:
            return result
        
        try:
            # Check JSON size
            json_str = json.dumps(data)
            max_json_size = config.get('max_json_size', 1048576)  # 1MB default
            
            if len(json_str) > max_json_size:
                result['valid'] = False
                result['errors'].append('JSON data too large')
                return result
            
            # Recursively validate JSON values
            self._validate_data_recursive(data, result, config)
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'JSON validation error: {str(e)}')
        
        return result
    
    def _validate_form_data(self, form_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate form data"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        max_fields = config.get('max_form_fields', 100)
        max_field_length = config.get('max_field_length', 10000)
        
        if len(form_data) > max_fields:
            result['valid'] = False
            result['errors'].append('Too many form fields')
            return result
        
        for key, value in form_data.items():
            # Validate field name
            if not self._validate_field_name(key):
                result['valid'] = False
                result['errors'].append(f'Invalid field name: {key}')
                continue
            
            # Validate field value
            if isinstance(value, str):
                if len(value) > max_field_length:
                    result['valid'] = False
                    result['errors'].append(f'Field too long: {key}')
                    continue
                
                validation_result = self._validate_string_value(value, config)
                if not validation_result['valid']:
                    result['valid'] = False
                    result['errors'].extend(validation_result['errors'])
                
                result['suspicious'].extend(validation_result['suspicious'])
        
        return result
    
    def _validate_query_params(self, args: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query parameters"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        max_field_length = config.get('max_field_length', 10000)
        
        for key, value in args.items():
            # Validate parameter name
            if not self._validate_field_name(key):
                result['valid'] = False
                result['errors'].append(f'Invalid parameter name: {key}')
                continue
            
            # Validate parameter value
            if isinstance(value, str):
                # URL decode the value
                try:
                    decoded_value = unquote(value)
                except Exception:
                    decoded_value = value
                
                if len(decoded_value) > max_field_length:
                    result['valid'] = False
                    result['errors'].append(f'Parameter too long: {key}')
                    continue
                
                validation_result = self._validate_string_value(decoded_value, config)
                if not validation_result['valid']:
                    result['valid'] = False
                    result['errors'].extend(validation_result['errors'])
                
                result['suspicious'].extend(validation_result['suspicious'])
        
        return result
    
    def _validate_headers(self, headers: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HTTP headers"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Originating-IP',
            'X-Remote-IP',
            'X-Client-IP'
        ]
        
        for header_name, header_value in headers.items():
            if isinstance(header_value, str):
                # Check for abnormally long headers
                if len(header_value) > 8192:  # 8KB limit
                    result['suspicious'].append(f'Long header: {header_name}')
                
                # Check for suspicious patterns in headers
                if self._contains_malicious_patterns(header_value):
                    result['suspicious'].append(f'Suspicious header content: {header_name}')
                
                # Check for SQL injection in headers
                if self._contains_sql_injection(header_value):
                    result['suspicious'].append(f'SQL injection attempt in header: {header_name}')
        
        return result
    
    def _validate_data_recursive(self, data: Any, result: Dict[str, Any], config: Dict[str, Any]):
        """Recursively validate data structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str):
                    if not self._validate_field_name(key):
                        result['valid'] = False
                        result['errors'].append(f'Invalid field name: {key}')
                        continue
                
                self._validate_data_recursive(value, result, config)
        
        elif isinstance(data, list):
            for item in data:
                self._validate_data_recursive(item, result, config)
        
        elif isinstance(data, str):
            validation_result = self._validate_string_value(data, config)
            if not validation_result['valid']:
                result['valid'] = False
                result['errors'].extend(validation_result['errors'])
            
            result['suspicious'].extend(validation_result['suspicious'])
    
    def _validate_field_name(self, field_name: str) -> bool:
        """Validate field name"""
        # Allow alphanumeric characters, underscores, hyphens, and dots
        pattern = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
        return bool(pattern.match(field_name))
    
    def _validate_string_value(self, value: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate string value"""
        result = {
            'valid': True,
            'errors': [],
            'suspicious': []
        }
        
        # Check for malicious patterns
        if self._contains_malicious_patterns(value):
            result['valid'] = False
            result['errors'].append('Malicious pattern detected')
            result['suspicious'].append(f'XSS attempt: {value[:100]}...')
        
        # Check for SQL injection
        if self._contains_sql_injection(value):
            result['valid'] = False
            result['errors'].append('SQL injection attempt detected')
            result['suspicious'].append(f'SQL injection: {value[:100]}...')
        
        # Check for path traversal
        if self._contains_path_traversal(value):
            result['valid'] = False
            result['errors'].append('Path traversal attempt detected')
            result['suspicious'].append(f'Path traversal: {value[:100]}...')
        
        # Check for command injection
        if self._contains_command_injection(value):
            result['valid'] = False
            result['errors'].append('Command injection attempt detected')
            result['suspicious'].append(f'Command injection: {value[:100]}...')
        
        return result
    
    def _contains_malicious_patterns(self, value: str) -> bool:
        """Check if value contains malicious patterns"""
        return any(pattern.search(value) for pattern in self.blocked_patterns)
    
    def _contains_sql_injection(self, value: str) -> bool:
        """Check if value contains SQL injection patterns"""
        return any(pattern.search(value) for pattern in self.sql_patterns)
    
    def _contains_path_traversal(self, value: str) -> bool:
        """Check if value contains path traversal patterns"""
        path_traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'%252e%252e%252f',
            r'%252e%252e%255c'
        ]
        
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in path_traversal_patterns)
    
    def _contains_command_injection(self, value: str) -> bool:
        """Check if value contains command injection patterns"""
        command_patterns = [
            r';\s*\w+',
            r'\|\s*\w+',
            r'&&\s*\w+',
            r'\$\(\w+\)',
            r'`\w+`',
            r'>\s*/\w+',
            r'<\s*/\w+'
        ]
        
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in command_patterns)
    
    def _log_suspicious_activity(self, suspicious_activities: List[str]):
        """Log suspicious activity"""
        for activity in suspicious_activities:
            self.app.logger.warning(f"Suspicious activity detected: {activity}")
            
            # Record in monitoring system if available
            if hasattr(self.app, 'monitoring_integration'):
                self.app.monitoring_integration.record_custom_metric(
                    'security.suspicious_activity',
                    1,
                    tags={
                        'type': 'input_validation',
                        'ip': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', 'unknown'),
                        'activity': activity[:100]  # Truncate for logging
                    }
                )
    
    def sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content"""
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'i', 'b',
            'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'blockquote', 'code', 'pre'
        ]
        
        allowed_attributes = {
            '*': ['class', 'id'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height']
        }
        
        return bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text content"""
        # HTML escape the text
        escaped_text = html.escape(text)
        
        # Remove null bytes and other control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', escaped_text)
        
        return sanitized
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email))
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        )
        return bool(url_pattern.match(url))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Simple phone validation - can be extended
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        return bool(phone_pattern.match(re.sub(r'[^\d+]', '', phone)))
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        # This would typically be implemented with actual counters
        return {
            'total_requests_validated': 0,
            'blocked_requests': 0,
            'xss_attempts': 0,
            'sql_injection_attempts': 0,
            'path_traversal_attempts': 0,
            'command_injection_attempts': 0
        }
    
    def add_blocked_pattern(self, pattern: str):
        """Add a new blocked pattern"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            self.blocked_patterns.append(compiled_pattern)
            
            # Update configuration
            if 'input_validation' not in self.config:
                self.config['input_validation'] = {}
            
            if 'blocked_patterns' not in self.config['input_validation']:
                self.config['input_validation']['blocked_patterns'] = []
            
            self.config['input_validation']['blocked_patterns'].append(pattern)
            
        except re.error as e:
            self.app.logger.error(f"Invalid regex pattern: {pattern}, error: {e}")
    
    def remove_blocked_pattern(self, pattern: str):
        """Remove a blocked pattern"""
        try:
            # Remove from compiled patterns
            self.blocked_patterns = [
                p for p in self.blocked_patterns
                if p.pattern != pattern
            ]
            
            # Update configuration
            if ('input_validation' in self.config and 
                'blocked_patterns' in self.config['input_validation']):
                if pattern in self.config['input_validation']['blocked_patterns']:
                    self.config['input_validation']['blocked_patterns'].remove(pattern)
            
        except Exception as e:
            self.app.logger.error(f"Error removing pattern: {pattern}, error: {e}")
    
    def get_blocked_patterns(self) -> List[str]:
        """Get list of blocked patterns"""
        return [pattern.pattern for pattern in self.blocked_patterns]
    
    def test_input(self, input_data: str) -> Dict[str, Any]:
        """Test input against validation rules"""
        result = self._validate_string_value(input_data, self.config.get('input_validation', {}))
        
        return {
            'input': input_data,
            'valid': result['valid'],
            'errors': result['errors'],
            'suspicious': result['suspicious'],
            'sanitized': self.sanitize_text(input_data)
        }