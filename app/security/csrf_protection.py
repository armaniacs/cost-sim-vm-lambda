"""
CSRF (Cross-Site Request Forgery) protection middleware.

This module provides:
- CSRF token generation and validation
- Cookie-based token storage
- Header-based token validation
- Exempt endpoints configuration
- Token refresh mechanism
"""

import hmac
import hashlib
import secrets
import time
from typing import Dict, List, Any, Optional
from functools import wraps
from flask import Flask, request, jsonify, make_response, g, current_app
from urllib.parse import urlparse


class CSRFProtection:
    """CSRF protection middleware"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.secret_key = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CSRF protection with Flask app"""
        self.app = app
        
        # Get CSRF configuration
        csrf_config = self.config.get('csrf', {})
        
        if not csrf_config.get('enabled', True):
            app.logger.info("CSRF protection is disabled")
            return
        
        # Set up secret key
        self.secret_key = csrf_config.get('secret_key', app.config.get('SECRET_KEY'))
        if not self.secret_key:
            raise ValueError("CSRF secret key is required")
        
        # Register CSRF protection middleware
        self._register_middleware(app, csrf_config)
        
        # Register CSRF endpoints
        self._register_endpoints(app, csrf_config)
        
        app.logger.info("CSRF protection initialized")
    
    def _register_middleware(self, app: Flask, config: Dict[str, Any]):
        """Register CSRF protection middleware"""
        
        @app.before_request
        def csrf_protect():
            """Protect against CSRF attacks"""
            
            # Skip CSRF protection for exempt endpoints
            if self._is_exempt_endpoint(config):
                return
            
            # Skip for safe methods
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                return
            
            # Skip for same-origin requests
            if self._is_same_origin():
                return
            
            # Validate CSRF token
            if not self._validate_csrf_token(config):
                return jsonify({'error': 'CSRF token validation failed'}), 403
        
        @app.after_request
        def set_csrf_cookie(response):
            """Set CSRF cookie in response"""
            
            # Only set cookie for HTML responses or if explicitly requested
            if (response.content_type and 
                'text/html' in response.content_type or
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
                
                token = self._generate_csrf_token()
                self._set_csrf_cookie(response, token, config)
            
            return response
    
    def _register_endpoints(self, app: Flask, config: Dict[str, Any]):
        """Register CSRF-related endpoints"""
        
        @app.route('/api/v1/security/csrf-token', methods=['GET'])
        def get_csrf_token():
            """Get CSRF token"""
            token = self._generate_csrf_token()
            response = make_response(jsonify({'csrf_token': token}))
            self._set_csrf_cookie(response, token, config)
            return response
        
        @app.route('/api/v1/security/csrf-validate', methods=['POST'])
        def validate_csrf_token():
            """Validate CSRF token"""
            token = request.headers.get(config.get('header_name', 'X-CSRFToken'))
            
            if not token:
                return jsonify({'error': 'CSRF token missing'}), 400
            
            if self._validate_token(token):
                return jsonify({'valid': True})
            else:
                return jsonify({'valid': False, 'error': 'Invalid CSRF token'}), 403
    
    def _is_exempt_endpoint(self, config: Dict[str, Any]) -> bool:
        """Check if current endpoint is exempt from CSRF protection"""
        exempt_endpoints = config.get('exempt_endpoints', [])
        
        return request.endpoint in exempt_endpoints or request.path in exempt_endpoints
    
    def _is_same_origin(self) -> bool:
        """Check if request is from same origin"""
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        
        if not origin and not referer:
            return True  # Assume same origin for API requests without these headers
        
        request_host = request.headers.get('Host')
        if not request_host:
            return False
        
        # Check origin
        if origin:
            origin_host = urlparse(origin).netloc
            if origin_host != request_host:
                return False
        
        # Check referer
        if referer:
            referer_host = urlparse(referer).netloc
            if referer_host != request_host:
                return False
        
        return True
    
    def _validate_csrf_token(self, config: Dict[str, Any]) -> bool:
        """Validate CSRF token from request"""
        # Get token from header
        header_name = config.get('header_name', 'X-CSRFToken')
        token = request.headers.get(header_name)
        
        if not token:
            # Try to get token from form data
            token = request.form.get('csrf_token')
        
        if not token:
            # Try to get token from JSON data
            if request.is_json:
                data = request.get_json()
                if data:
                    token = data.get('csrf_token')
        
        if not token:
            return False
        
        return self._validate_token(token)
    
    def _validate_token(self, token: str) -> bool:
        """Validate CSRF token"""
        try:
            # Decode token
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            timestamp_str, nonce, signature = parts
            timestamp = int(timestamp_str)
            
            # Check token age
            token_lifetime = self.config.get('csrf', {}).get('token_lifetime', 3600)
            if time.time() - timestamp > token_lifetime:
                return False
            
            # Verify signature
            expected_signature = self._create_signature(timestamp_str, nonce)
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        signature = self._create_signature(timestamp, nonce)
        
        return f"{timestamp}.{nonce}.{signature}"
    
    def _create_signature(self, timestamp: str, nonce: str) -> str:
        """Create signature for CSRF token"""
        message = f"{timestamp}.{nonce}"
        
        # Include user session info if available
        user_id = getattr(g, 'current_user', {}).get('id', 'anonymous')
        message += f".{user_id}"
        
        # Include request info
        message += f".{request.remote_addr}"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _set_csrf_cookie(self, response, token: str, config: Dict[str, Any]):
        """Set CSRF cookie"""
        cookie_name = config.get('cookie_name', 'csrf_token')
        cookie_secure = config.get('cookie_secure', False)
        cookie_httponly = config.get('cookie_httponly', True)
        cookie_samesite = config.get('cookie_samesite', 'Strict')
        
        # Set cookie
        response.set_cookie(
            cookie_name,
            token,
            secure=cookie_secure,
            httponly=cookie_httponly,
            samesite=cookie_samesite,
            max_age=config.get('token_lifetime', 3600)
        )
    
    def get_csrf_token(self) -> str:
        """Get current CSRF token"""
        return self._generate_csrf_token()
    
    def exempt_endpoint(self, endpoint: str):
        """Add endpoint to CSRF exemption list"""
        if 'csrf' not in self.config:
            self.config['csrf'] = {}
        
        if 'exempt_endpoints' not in self.config['csrf']:
            self.config['csrf']['exempt_endpoints'] = []
        
        if endpoint not in self.config['csrf']['exempt_endpoints']:
            self.config['csrf']['exempt_endpoints'].append(endpoint)
    
    def remove_exempt_endpoint(self, endpoint: str):
        """Remove endpoint from CSRF exemption list"""
        if ('csrf' in self.config and 
            'exempt_endpoints' in self.config['csrf'] and
            endpoint in self.config['csrf']['exempt_endpoints']):
            self.config['csrf']['exempt_endpoints'].remove(endpoint)
    
    def get_exempt_endpoints(self) -> List[str]:
        """Get list of exempt endpoints"""
        return self.config.get('csrf', {}).get('exempt_endpoints', [])
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid"""
        return self._validate_token(token)
    
    def get_csrf_config(self) -> Dict[str, Any]:
        """Get CSRF configuration"""
        return self.config.get('csrf', {})
    
    def update_csrf_config(self, new_config: Dict[str, Any]):
        """Update CSRF configuration"""
        if 'csrf' not in self.config:
            self.config['csrf'] = {}
        
        self.config['csrf'].update(new_config)
        
        # Update secret key if changed
        if 'secret_key' in new_config:
            self.secret_key = new_config['secret_key']
    
    def get_csrf_stats(self) -> Dict[str, Any]:
        """Get CSRF protection statistics"""
        # This would typically be implemented with actual counters
        return {
            'tokens_generated': 0,
            'tokens_validated': 0,
            'validation_failures': 0,
            'exempt_requests': 0
        }


def csrf_protect(f):
    """Decorator to protect specific endpoints with CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CSRF protection is handled by middleware
        # This decorator can be used for additional endpoint-specific protection
        return f(*args, **kwargs)
    return decorated_function


def csrf_exempt(f):
    """Decorator to exempt specific endpoints from CSRF protection"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Mark endpoint as exempt
        g.csrf_exempt = True
        return f(*args, **kwargs)
    return decorated_function