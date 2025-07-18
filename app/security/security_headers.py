"""
Security headers middleware for comprehensive HTTP security.

This module provides:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer Policy
- Permissions Policy
- Feature Policy
"""

import json
from typing import Dict, List, Any, Optional
from flask import Flask, request, current_app


class SecurityHeaders:
    """Security headers middleware for enterprise-grade HTTP security"""
    
    def __init__(self, app: Flask = None, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security headers with Flask app"""
        self.app = app
        
        # Get security headers configuration
        headers_config = self.config.get('security_headers', {})
        
        if not headers_config.get('enabled', True):
            app.logger.info("Security headers are disabled")
            return
        
        # Register security headers middleware
        self._register_middleware(app, headers_config)
        
        app.logger.info("Security headers initialized")
    
    def _register_middleware(self, app: Flask, config: Dict[str, Any]):
        """Register security headers middleware"""
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses"""
            
            # Skip for static files if configured
            if self._should_skip_headers():
                return response
            
            # Add each security header
            self._add_hsts_header(response, config)
            self._add_csp_header(response, config)
            self._add_frame_options_header(response, config)
            self._add_content_type_options_header(response, config)
            self._add_xss_protection_header(response, config)
            self._add_referrer_policy_header(response, config)
            self._add_permissions_policy_header(response, config)
            self._add_feature_policy_header(response, config)
            
            return response
    
    def _should_skip_headers(self) -> bool:
        """Check if security headers should be skipped"""
        # Skip for static files
        if request.endpoint == 'static':
            return True
        
        # Skip for specific paths if configured
        skip_paths = self.config.get('security_headers', {}).get('skip_paths', [])
        if request.path in skip_paths:
            return True
        
        return False
    
    def _add_hsts_header(self, response, config: Dict[str, Any]):
        """Add HTTP Strict Transport Security header"""
        hsts_config = config.get('strict_transport_security', {})
        
        if not hsts_config.get('enabled', True):
            return
        
        # Only add HSTS for HTTPS connections
        if not request.is_secure and not self._is_development():
            return
        
        max_age = hsts_config.get('max_age', 31536000)  # 1 year
        include_subdomains = hsts_config.get('include_subdomains', True)
        preload = hsts_config.get('preload', True)
        
        hsts_value = f"max-age={max_age}"
        
        if include_subdomains:
            hsts_value += "; includeSubDomains"
        
        if preload:
            hsts_value += "; preload"
        
        response.headers['Strict-Transport-Security'] = hsts_value
    
    def _add_csp_header(self, response, config: Dict[str, Any]):
        """Add Content Security Policy header"""
        csp_config = config.get('content_security_policy', {})
        
        if not csp_config.get('enabled', True):
            return
        
        # Build CSP directive
        csp_directives = []
        
        # Default directives
        directives = {
            'default-src': csp_config.get('default_src', ["'self'"]),
            'script-src': csp_config.get('script_src', ["'self'"]),
            'style-src': csp_config.get('style_src', ["'self'"]),
            'img-src': csp_config.get('img_src', ["'self'", "data:", "https:"]),
            'font-src': csp_config.get('font_src', ["'self'"]),
            'connect-src': csp_config.get('connect_src', ["'self'"]),
            'media-src': csp_config.get('media_src', ["'self'"]),
            'object-src': csp_config.get('object_src', ["'none'"]),
            'child-src': csp_config.get('child_src', ["'self'"]),
            'frame-ancestors': csp_config.get('frame_ancestors', ["'none'"]),
            'base-uri': csp_config.get('base_uri', ["'self'"]),
            'form-action': csp_config.get('form_action', ["'self'"])
        }
        
        # Build directive strings
        for directive, sources in directives.items():
            if sources:
                sources_str = ' '.join(sources)
                csp_directives.append(f"{directive} {sources_str}")
        
        # Add upgrade-insecure-requests if enabled
        if csp_config.get('upgrade_insecure_requests', True):
            csp_directives.append('upgrade-insecure-requests')
        
        # Add block-all-mixed-content if enabled
        if csp_config.get('block_all_mixed_content', False):
            csp_directives.append('block-all-mixed-content')
        
        csp_value = '; '.join(csp_directives)
        
        # Use report-only mode if configured
        if csp_config.get('report_only', False):
            response.headers['Content-Security-Policy-Report-Only'] = csp_value
        else:
            response.headers['Content-Security-Policy'] = csp_value
        
        # Add report URI if configured
        report_uri = csp_config.get('report_uri')
        if report_uri:
            if 'Content-Security-Policy' in response.headers:
                response.headers['Content-Security-Policy'] += f"; report-uri {report_uri}"
            if 'Content-Security-Policy-Report-Only' in response.headers:
                response.headers['Content-Security-Policy-Report-Only'] += f"; report-uri {report_uri}"
    
    def _add_frame_options_header(self, response, config: Dict[str, Any]):
        """Add X-Frame-Options header"""
        frame_options = config.get('x_frame_options', 'DENY')
        
        if frame_options:
            response.headers['X-Frame-Options'] = frame_options
    
    def _add_content_type_options_header(self, response, config: Dict[str, Any]):
        """Add X-Content-Type-Options header"""
        content_type_options = config.get('x_content_type_options', 'nosniff')
        
        if content_type_options:
            response.headers['X-Content-Type-Options'] = content_type_options
    
    def _add_xss_protection_header(self, response, config: Dict[str, Any]):
        """Add X-XSS-Protection header"""
        xss_protection = config.get('x_xss_protection', '1; mode=block')
        
        if xss_protection:
            response.headers['X-XSS-Protection'] = xss_protection
    
    def _add_referrer_policy_header(self, response, config: Dict[str, Any]):
        """Add Referrer-Policy header"""
        referrer_policy = config.get('referrer_policy', 'strict-origin-when-cross-origin')
        
        if referrer_policy:
            response.headers['Referrer-Policy'] = referrer_policy
    
    def _add_permissions_policy_header(self, response, config: Dict[str, Any]):
        """Add Permissions-Policy header"""
        permissions_config = config.get('permissions_policy', {})
        
        if not permissions_config:
            return
        
        # Build permissions policy
        permissions = []
        
        for feature, allowlist in permissions_config.items():
            if isinstance(allowlist, list):
                if not allowlist:
                    # Empty list means feature is disabled
                    permissions.append(f"{feature}=()")
                else:
                    # Convert allowlist to string
                    allowlist_str = ' '.join(f'"{origin}"' if origin != '*' else origin for origin in allowlist)
                    permissions.append(f"{feature}=({allowlist_str})")
            elif isinstance(allowlist, str):
                permissions.append(f"{feature}=({allowlist})")
        
        if permissions:
            response.headers['Permissions-Policy'] = ', '.join(permissions)
    
    def _add_feature_policy_header(self, response, config: Dict[str, Any]):
        """Add Feature-Policy header (deprecated but still supported)"""
        feature_config = config.get('feature_policy', {})
        
        if not feature_config:
            return
        
        # Build feature policy
        features = []
        
        for feature, value in feature_config.items():
            features.append(f"{feature} {value}")
        
        if features:
            response.headers['Feature-Policy'] = '; '.join(features)
    
    def _is_development(self) -> bool:
        """Check if running in development mode"""
        return current_app.config.get('DEBUG', False) or \
               current_app.config.get('FLASK_ENV') == 'development'
    
    def update_csp_config(self, new_config: Dict[str, Any]):
        """Update CSP configuration"""
        if 'security_headers' not in self.config:
            self.config['security_headers'] = {}
        
        if 'content_security_policy' not in self.config['security_headers']:
            self.config['security_headers']['content_security_policy'] = {}
        
        self.config['security_headers']['content_security_policy'].update(new_config)
    
    def add_csp_source(self, directive: str, source: str):
        """Add source to CSP directive"""
        csp_config = self.config.get('security_headers', {}).get('content_security_policy', {})
        
        if directive not in csp_config:
            csp_config[directive] = []
        
        if source not in csp_config[directive]:
            csp_config[directive].append(source)
    
    def remove_csp_source(self, directive: str, source: str):
        """Remove source from CSP directive"""
        csp_config = self.config.get('security_headers', {}).get('content_security_policy', {})
        
        if directive in csp_config and source in csp_config[directive]:
            csp_config[directive].remove(source)
    
    def get_csp_config(self) -> Dict[str, Any]:
        """Get current CSP configuration"""
        return self.config.get('security_headers', {}).get('content_security_policy', {})
    
    def validate_csp_config(self, csp_config: Dict[str, Any]) -> List[str]:
        """Validate CSP configuration"""
        errors = []
        
        # Check for common CSP mistakes
        if 'default_src' in csp_config:
            default_src = csp_config['default_src']
            if "'unsafe-eval'" in default_src:
                errors.append("'unsafe-eval' in default-src is not recommended")
            if "'unsafe-inline'" in default_src:
                errors.append("'unsafe-inline' in default-src is not recommended")
        
        if 'script_src' in csp_config:
            script_src = csp_config['script_src']
            if "'unsafe-eval'" in script_src:
                errors.append("'unsafe-eval' in script-src should be avoided")
            if "'unsafe-inline'" in script_src:
                errors.append("'unsafe-inline' in script-src should be avoided")
        
        # Check for missing important directives
        important_directives = ['default-src', 'script-src', 'style-src', 'img-src']
        for directive in important_directives:
            if directive.replace('-', '_') not in csp_config:
                errors.append(f"Missing important directive: {directive}")
        
        return errors
    
    def generate_csp_report_endpoint(self, app: Flask):
        """Generate CSP report endpoint"""
        
        @app.route('/api/v1/security/csp-report', methods=['POST'])
        def csp_report():
            """Handle CSP violation reports"""
            try:
                report_data = request.get_json()
                
                if report_data and 'csp-report' in report_data:
                    violation = report_data['csp-report']
                    
                    # Log the violation
                    app.logger.warning(f"CSP Violation: {json.dumps(violation, indent=2)}")
                    
                    # Record in monitoring system if available
                    if hasattr(app, 'monitoring_integration'):
                        app.monitoring_integration.record_custom_metric(
                            'security.csp_violations',
                            1,
                            tags={
                                'violated_directive': violation.get('violated-directive', 'unknown'),
                                'blocked_uri': violation.get('blocked-uri', 'unknown'),
                                'source_file': violation.get('source-file', 'unknown')
                            }
                        )
                
                return '', 204
                
            except Exception as e:
                app.logger.error(f"Error processing CSP report: {e}")
                return '', 400
    
    def get_security_headers_config(self) -> Dict[str, Any]:
        """Get current security headers configuration"""
        return self.config.get('security_headers', {})
    
    def update_security_headers_config(self, new_config: Dict[str, Any]):
        """Update security headers configuration"""
        if 'security_headers' not in self.config:
            self.config['security_headers'] = {}
        
        self.config['security_headers'].update(new_config)
    
    def get_security_headers_status(self) -> Dict[str, Any]:
        """Get security headers status"""
        config = self.get_security_headers_config()
        
        return {
            'enabled': config.get('enabled', True),
            'hsts_enabled': config.get('strict_transport_security', {}).get('enabled', True),
            'csp_enabled': config.get('content_security_policy', {}).get('enabled', True),
            'frame_options_enabled': bool(config.get('x_frame_options')),
            'content_type_options_enabled': bool(config.get('x_content_type_options')),
            'xss_protection_enabled': bool(config.get('x_xss_protection')),
            'referrer_policy_enabled': bool(config.get('referrer_policy')),
            'permissions_policy_enabled': bool(config.get('permissions_policy')),
            'feature_policy_enabled': bool(config.get('feature_policy'))
        }
    
    def analyze_security_headers(self, url: str) -> Dict[str, Any]:
        """Analyze security headers for a URL (for testing/validation)"""
        # This would be used for testing the headers
        # In a real implementation, this could make HTTP requests to test
        return {
            'url': url,
            'analysis': 'Security headers analysis would be implemented here',
            'recommendations': []
        }