"""
CORS (Cross-Origin Resource Sharing) configuration middleware.

This module provides comprehensive CORS configuration with:
- Origin validation
- Method and header control
- Credentials handling
- Preflight request handling
- Dynamic origin validation
"""

import re
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
from flask import Flask, request, jsonify, current_app
from flask_cors import CORS


class CORSConfig:
    """Advanced CORS configuration middleware"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.cors_instance = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CORS configuration with Flask app"""
        self.app = app
        
        # Get CORS configuration
        cors_config = self.config.get('cors', {})
        
        if not cors_config.get('enabled', True):
            app.logger.info("CORS is disabled")
            return
        
        # Configure CORS with advanced options
        self._configure_cors(app, cors_config)
        
        # Register CORS event handlers
        self._register_cors_handlers(app)
        
        app.logger.info("CORS configuration initialized")
    
    def _configure_cors(self, app: Flask, config: Dict[str, Any]):
        """Configure CORS with advanced options"""
        
        # Extract configuration
        origins = config.get('origins', ['*'])
        methods = config.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        headers = config.get('headers', ['Content-Type', 'Authorization'])
        credentials = config.get('credentials', True)
        max_age = config.get('max_age', 3600)
        expose_headers = config.get('expose_headers', [])
        
        # Create CORS configuration
        cors_config = {
            'origins': self._process_origins(origins),
            'methods': methods,
            'allow_headers': headers,
            'supports_credentials': credentials,
            'max_age': max_age,
            'expose_headers': expose_headers
        }
        
        # Initialize CORS with configuration
        self.cors_instance = CORS(app, **cors_config)
        
        # Add custom origin validation if needed
        if self._needs_custom_validation(origins):
            self._setup_custom_origin_validation(app, origins)
    
    def _process_origins(self, origins: List[str]) -> Union[List[str], str]:
        """Process origin configuration"""
        if not origins:
            return []
        
        # Check if all origins are allowed
        if '*' in origins:
            return '*'
        
        # Filter out patterns that need custom validation
        static_origins = []
        for origin in origins:
            if not self._is_pattern(origin):
                static_origins.append(origin)
        
        return static_origins if static_origins else origins
    
    def _is_pattern(self, origin: str) -> bool:
        """Check if origin contains patterns requiring custom validation"""
        return any(char in origin for char in ['*', '?', '[', ']'])
    
    def _needs_custom_validation(self, origins: List[str]) -> bool:
        """Check if custom origin validation is needed"""
        return any(self._is_pattern(origin) for origin in origins)
    
    def _setup_custom_origin_validation(self, app: Flask, origins: List[str]):
        """Setup custom origin validation for pattern matching"""
        
        @app.before_request
        def validate_origin():
            """Validate origin before processing request"""
            if request.method == 'OPTIONS':
                return self._handle_preflight_request(origins)
            
            origin = request.headers.get('Origin')
            if origin and not self._is_origin_allowed(origin, origins):
                return jsonify({'error': 'Origin not allowed'}), 403
        
        @app.after_request
        def add_cors_headers(response):
            """Add CORS headers to response"""
            origin = request.headers.get('Origin')
            if origin and self._is_origin_allowed(origin, origins):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                
                if request.method == 'OPTIONS':
                    response.headers['Access-Control-Allow-Methods'] = ', '.join(
                        self.config.get('cors', {}).get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
                    )
                    response.headers['Access-Control-Allow-Headers'] = ', '.join(
                        self.config.get('cors', {}).get('headers', ['Content-Type', 'Authorization'])
                    )
                    response.headers['Access-Control-Max-Age'] = str(
                        self.config.get('cors', {}).get('max_age', 3600)
                    )
                
                # Add exposed headers
                expose_headers = self.config.get('cors', {}).get('expose_headers', [])
                if expose_headers:
                    response.headers['Access-Control-Expose-Headers'] = ', '.join(expose_headers)
            
            return response
    
    def _handle_preflight_request(self, origins: List[str]):
        """Handle preflight OPTIONS request"""
        origin = request.headers.get('Origin')
        
        if not origin or not self._is_origin_allowed(origin, origins):
            return jsonify({'error': 'Origin not allowed'}), 403
        
        # Create preflight response
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = ', '.join(
            self.config.get('cors', {}).get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        )
        response.headers['Access-Control-Allow-Headers'] = ', '.join(
            self.config.get('cors', {}).get('headers', ['Content-Type', 'Authorization'])
        )
        response.headers['Access-Control-Max-Age'] = str(
            self.config.get('cors', {}).get('max_age', 3600)
        )
        
        return response
    
    def _is_origin_allowed(self, origin: str, origins: List[str]) -> bool:
        """Check if origin is allowed using pattern matching"""
        if '*' in origins:
            return True
        
        for allowed_origin in origins:
            if self._match_origin(origin, allowed_origin):
                return True
        
        return False
    
    def _match_origin(self, origin: str, pattern: str) -> bool:
        """Match origin against pattern"""
        if pattern == origin:
            return True
        
        # Handle wildcard patterns
        if '*' in pattern:
            # Convert pattern to regex
            regex_pattern = pattern.replace('*', '.*')
            return re.match(f'^{regex_pattern}$', origin) is not None
        
        # Handle subdomain patterns
        if pattern.startswith('*.'):
            domain = pattern[2:]
            parsed_origin = urlparse(origin)
            origin_host = parsed_origin.hostname or ''
            
            # Check if origin is exactly the domain or a subdomain
            return origin_host == domain or origin_host.endswith(f'.{domain}')
        
        return False
    
    def _register_cors_handlers(self, app: Flask):
        """Register CORS-related event handlers"""
        
        @app.before_request
        def log_cors_request():
            """Log CORS-related request information"""
            origin = request.headers.get('Origin')
            if origin:
                app.logger.debug(f"CORS request from origin: {origin}")
        
        @app.after_request
        def validate_cors_response(response):
            """Validate CORS response configuration"""
            if current_app.config.get('DEBUG', False):
                origin = request.headers.get('Origin')
                if origin:
                    # Log CORS headers for debugging
                    cors_headers = {
                        key: value for key, value in response.headers.items()
                        if key.startswith('Access-Control-')
                    }
                    app.logger.debug(f"CORS response headers: {cors_headers}")
            
            return response
    
    def add_origin(self, origin: str):
        """Dynamically add an allowed origin"""
        if 'cors' not in self.config:
            self.config['cors'] = {}
        
        if 'origins' not in self.config['cors']:
            self.config['cors']['origins'] = []
        
        if origin not in self.config['cors']['origins']:
            self.config['cors']['origins'].append(origin)
            
            # Reconfigure CORS if already initialized
            if self.cors_instance and self.app:
                self._configure_cors(self.app, self.config['cors'])
    
    def remove_origin(self, origin: str):
        """Dynamically remove an allowed origin"""
        if 'cors' in self.config and 'origins' in self.config['cors']:
            if origin in self.config['cors']['origins']:
                self.config['cors']['origins'].remove(origin)
                
                # Reconfigure CORS if already initialized
                if self.cors_instance and self.app:
                    self._configure_cors(self.app, self.config['cors'])
    
    def get_allowed_origins(self) -> List[str]:
        """Get list of allowed origins"""
        return self.config.get('cors', {}).get('origins', [])
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed"""
        origins = self.get_allowed_origins()
        return self._is_origin_allowed(origin, origins)
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get current CORS configuration"""
        return self.config.get('cors', {})
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update CORS configuration"""
        if 'cors' not in self.config:
            self.config['cors'] = {}
        
        self.config['cors'].update(new_config)
        
        # Reconfigure CORS if already initialized
        if self.cors_instance and self.app:
            self._configure_cors(self.app, self.config['cors'])
    
    def validate_origin_format(self, origin: str) -> bool:
        """Validate origin format"""
        try:
            parsed = urlparse(origin)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def get_origin_info(self, origin: str) -> Dict[str, Any]:
        """Get information about an origin"""
        try:
            parsed = urlparse(origin)
            return {
                'scheme': parsed.scheme,
                'hostname': parsed.hostname,
                'port': parsed.port,
                'is_secure': parsed.scheme == 'https',
                'is_localhost': parsed.hostname in ['localhost', '127.0.0.1', '::1'],
                'is_valid': self.validate_origin_format(origin),
                'is_allowed': self.is_origin_allowed(origin)
            }
        except Exception as e:
            return {
                'error': str(e),
                'is_valid': False,
                'is_allowed': False
            }