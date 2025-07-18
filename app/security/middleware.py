"""
Main security middleware class that integrates all security components.

This module provides:
- Unified security middleware initialization
- Configuration management
- Component coordination
- Security API endpoints
- Monitoring integration
"""

import json
from typing import Dict, Any, Optional, List
from flask import Flask, Blueprint, jsonify, request, current_app

from .config import SecurityConfig
from .cors_config import CORSConfig
from .rate_limiter import RateLimiter
from .security_headers import SecurityHeaders
from .input_validator import InputValidator
from .csrf_protection import CSRFProtection
from .security_monitor import SecurityMonitor


class SecurityMiddleware:
    """Main security middleware class"""
    
    def __init__(self, app: Flask = None, config_file: str = None):
        self.app = app
        self.config = SecurityConfig(config_file) if config_file else SecurityConfig()
        self.components = {}
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        try:
            # Initialize security components
            self._init_components()
            
            # Register security API endpoints
            self._register_endpoints()
            
            # Store reference in app
            app.security_middleware = self
            
            self.initialized = True
            app.logger.info("Security middleware initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Failed to initialize security middleware: {e}")
            raise
    
    def _init_components(self):
        """Initialize all security components"""
        config_dict = self.config.config
        
        # Initialize CORS configuration
        if self.config.is_enabled('cors'):
            try:
                cors_config = CORSConfig(self.app, config_dict)
                self.components['cors'] = cors_config
                self.app.logger.info("CORS configuration initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize CORS: {e}")
                raise
        
        # Initialize rate limiter
        if self.config.is_enabled('rate_limiting'):
            try:
                rate_limiter = RateLimiter(self.app, config_dict)
                self.components['rate_limiter'] = rate_limiter
                self.app.logger.info("Rate limiter initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize rate limiter: {e}")
                raise
        
        # Initialize security headers
        if self.config.is_enabled('security_headers'):
            try:
                security_headers = SecurityHeaders(self.app, config_dict)
                self.components['security_headers'] = security_headers
                self.app.logger.info("Security headers initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize security headers: {e}")
                raise
        
        # Initialize input validator
        if self.config.is_enabled('input_validation'):
            try:
                input_validator = InputValidator(self.app, config_dict)
                self.components['input_validator'] = input_validator
                self.app.logger.info("Input validator initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize input validator: {e}")
                raise
        
        # Initialize CSRF protection
        if self.config.is_enabled('csrf'):
            try:
                csrf_protection = CSRFProtection(self.app, config_dict)
                self.components['csrf_protection'] = csrf_protection
                self.app.logger.info("CSRF protection initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize CSRF protection: {e}")
                raise
        
        # Initialize security monitor
        if self.config.is_enabled('monitoring'):
            try:
                security_monitor = SecurityMonitor(self.app, config_dict)
                self.components['security_monitor'] = security_monitor
                self.app.logger.info("Security monitor initialized")
            except Exception as e:
                self.app.logger.error(f"Failed to initialize security monitor: {e}")
                raise
    
    def _register_endpoints(self):
        """Register security API endpoints"""
        # Create security blueprint
        security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')
        
        @security_bp.route('/status', methods=['GET'])
        def get_security_status():
            """Get security middleware status"""
            try:
                status = {
                    'initialized': self.initialized,
                    'components': {
                        name: component is not None
                        for name, component in self.components.items()
                    },
                    'config': {
                        'cors_enabled': self.config.is_enabled('cors'),
                        'rate_limiting_enabled': self.config.is_enabled('rate_limiting'),
                        'security_headers_enabled': self.config.is_enabled('security_headers'),
                        'input_validation_enabled': self.config.is_enabled('input_validation'),
                        'csrf_enabled': self.config.is_enabled('csrf'),
                        'monitoring_enabled': self.config.is_enabled('monitoring')
                    },
                    'environment': self.config.get_environment()
                }
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/config', methods=['GET'])
        def get_security_config():
            """Get security configuration"""
            try:
                # Return sanitized config (without secrets)
                config = self.config.config.copy()
                
                # Remove sensitive information
                if 'csrf' in config and 'secret_key' in config['csrf']:
                    config['csrf']['secret_key'] = '***REDACTED***'
                
                return jsonify(config)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/config', methods=['PUT'])
        def update_security_config():
            """Update security configuration"""
            try:
                new_config = request.get_json()
                if not new_config:
                    return jsonify({'error': 'No configuration provided'}), 400
                
                # Update configuration
                self.config.config.update(new_config)
                self.config.save()
                
                # Reinitialize components if needed
                self._reinitialize_components()
                
                return jsonify({'status': 'updated'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/stats', methods=['GET'])
        def get_security_stats():
            """Get security statistics"""
            try:
                stats = {
                    'timestamp': self.config.get_environment(),
                    'components': {}
                }
                
                # Get stats from each component
                for name, component in self.components.items():
                    if hasattr(component, 'get_security_stats'):
                        stats['components'][name] = component.get_security_stats()
                    elif hasattr(component, f'get_{name}_stats'):
                        stats['components'][name] = getattr(component, f'get_{name}_stats')()
                
                return jsonify(stats)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/blocked-ips', methods=['GET'])
        def get_blocked_ips():
            """Get list of blocked IPs"""
            try:
                if 'security_monitor' in self.components:
                    blocked_ips = self.components['security_monitor'].get_blocked_ips()
                    return jsonify({'blocked_ips': blocked_ips})
                else:
                    return jsonify({'error': 'Security monitor not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/blocked-ips/<ip>', methods=['DELETE'])
        def unblock_ip(ip: str):
            """Unblock IP address"""
            try:
                if 'security_monitor' in self.components:
                    self.components['security_monitor'].unblock_ip(ip)
                    return jsonify({'status': 'unblocked', 'ip': ip})
                else:
                    return jsonify({'error': 'Security monitor not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/whitelist', methods=['GET'])
        def get_whitelist():
            """Get IP whitelist"""
            try:
                if 'security_monitor' in self.components:
                    whitelist = self.components['security_monitor'].get_whitelist()
                    return jsonify({'whitelist': whitelist})
                else:
                    return jsonify({'error': 'Security monitor not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/whitelist', methods=['POST'])
        def add_to_whitelist():
            """Add IP to whitelist"""
            try:
                data = request.get_json()
                if not data or 'ip' not in data:
                    return jsonify({'error': 'IP address required'}), 400
                
                if 'security_monitor' in self.components:
                    self.components['security_monitor'].whitelist_ip(data['ip'])
                    return jsonify({'status': 'added', 'ip': data['ip']})
                else:
                    return jsonify({'error': 'Security monitor not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/rate-limit/<identifier>', methods=['GET'])
        def get_rate_limit_status(identifier: str):
            """Get rate limit status for identifier"""
            try:
                if 'rate_limiter' in self.components:
                    limit_type = request.args.get('type', 'ip')
                    status = self.components['rate_limiter'].get_rate_limit_status(identifier, limit_type)
                    return jsonify(status)
                else:
                    return jsonify({'error': 'Rate limiter not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/rate-limit/<identifier>', methods=['DELETE'])
        def reset_rate_limit(identifier: str):
            """Reset rate limit for identifier"""
            try:
                if 'rate_limiter' in self.components:
                    limit_type = request.args.get('type', 'ip')
                    success = self.components['rate_limiter'].reset_rate_limit(identifier, limit_type)
                    
                    if success:
                        return jsonify({'status': 'reset', 'identifier': identifier})
                    else:
                        return jsonify({'error': 'Failed to reset rate limit'}), 500
                else:
                    return jsonify({'error': 'Rate limiter not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/input-validation/test', methods=['POST'])
        def test_input_validation():
            """Test input validation"""
            try:
                data = request.get_json()
                if not data or 'input' not in data:
                    return jsonify({'error': 'Input data required'}), 400
                
                if 'input_validator' in self.components:
                    result = self.components['input_validator'].test_input(data['input'])
                    return jsonify(result)
                else:
                    return jsonify({'error': 'Input validator not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/csp-config', methods=['GET'])
        def get_csp_config():
            """Get CSP configuration"""
            try:
                if 'security_headers' in self.components:
                    csp_config = self.components['security_headers'].get_csp_config()
                    return jsonify(csp_config)
                else:
                    return jsonify({'error': 'Security headers not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @security_bp.route('/csp-config', methods=['PUT'])
        def update_csp_config():
            """Update CSP configuration"""
            try:
                new_config = request.get_json()
                if not new_config:
                    return jsonify({'error': 'No configuration provided'}), 400
                
                if 'security_headers' in self.components:
                    self.components['security_headers'].update_csp_config(new_config)
                    return jsonify({'status': 'updated'})
                else:
                    return jsonify({'error': 'Security headers not enabled'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Register CSP report endpoint
        if 'security_headers' in self.components:
            self.components['security_headers'].generate_csp_report_endpoint(self.app)
        
        # Register blueprint
        self.app.register_blueprint(security_bp)
        self.app.logger.info("Security API endpoints registered")
    
    def _reinitialize_components(self):
        """Reinitialize components after configuration change"""
        try:
            # Only reinitialize if already initialized
            if self.initialized:
                self.components.clear()
                self._init_components()
                self.app.logger.info("Security components reinitialized")
                
        except Exception as e:
            self.app.logger.error(f"Failed to reinitialize security components: {e}")
            raise
    
    def get_component(self, name: str):
        """Get specific security component"""
        return self.components.get(name)
    
    def is_component_enabled(self, name: str) -> bool:
        """Check if security component is enabled"""
        return name in self.components
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        status = {
            'initialized': self.initialized,
            'environment': self.config.get_environment(),
            'components': {},
            'summary': {
                'total_components': len(self.components),
                'enabled_components': list(self.components.keys()),
                'disabled_components': []
            }
        }
        
        # Check each component
        all_components = ['cors', 'rate_limiter', 'security_headers', 'input_validator', 'csrf_protection', 'security_monitor']
        
        for component_name in all_components:
            if component_name in self.components:
                status['components'][component_name] = {
                    'enabled': True,
                    'initialized': True
                }
            else:
                status['components'][component_name] = {
                    'enabled': False,
                    'initialized': False
                }
                status['summary']['disabled_components'].append(component_name)
        
        return status
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics from all components"""
        metrics = {
            'timestamp': self.config.get_environment(),
            'components': {}
        }
        
        # Collect metrics from each component
        for name, component in self.components.items():
            try:
                if hasattr(component, 'get_security_stats'):
                    metrics['components'][name] = component.get_security_stats()
                elif hasattr(component, f'get_{name}_stats'):
                    metrics['components'][name] = getattr(component, f'get_{name}_stats')()
                else:
                    metrics['components'][name] = {'status': 'no_metrics_available'}
                    
            except Exception as e:
                metrics['components'][name] = {'error': str(e)}
        
        return metrics
    
    def reload_config(self):
        """Reload security configuration"""
        try:
            self.config.reload()
            self._reinitialize_components()
            self.app.logger.info("Security configuration reloaded")
            
        except Exception as e:
            self.app.logger.error(f"Failed to reload security configuration: {e}")
            raise
    
    def shutdown(self):
        """Shutdown security middleware"""
        try:
            for component_name, component in self.components.items():
                if hasattr(component, 'shutdown'):
                    component.shutdown()
                    
            self.components.clear()
            self.initialized = False
            self.app.logger.info("Security middleware shut down")
            
        except Exception as e:
            self.app.logger.error(f"Error shutting down security middleware: {e}")
    
    def validate_configuration(self) -> List[str]:
        """Validate security configuration"""
        errors = []
        
        # Validate CORS configuration
        if self.config.is_enabled('cors'):
            cors_config = self.config.get_cors_config()
            if not cors_config.get('origins'):
                errors.append("CORS origins not configured")
        
        # Validate rate limiting configuration
        if self.config.is_enabled('rate_limiting'):
            rate_config = self.config.get_rate_limiting_config()
            if not rate_config.get('redis_url'):
                errors.append("Rate limiting Redis URL not configured")
        
        # Validate CSRF configuration
        if self.config.is_enabled('csrf'):
            csrf_config = self.config.get_csrf_config()
            if not csrf_config.get('secret_key'):
                errors.append("CSRF secret key not configured")
        
        # Validate CSP configuration
        if self.config.is_enabled('security_headers'):
            headers_config = self.config.get_security_headers_config()
            csp_config = headers_config.get('content_security_policy', {})
            if csp_config.get('enabled', True):
                if 'security_headers' in self.components:
                    csp_errors = self.components['security_headers'].validate_csp_config(csp_config)
                    errors.extend(csp_errors)
        
        return errors
    
    def get_configuration_recommendations(self) -> List[str]:
        """Get security configuration recommendations"""
        recommendations = []
        
        # Check if running in production
        if self.config.is_production():
            # Production-specific recommendations
            if not self.config.is_enabled('security_headers'):
                recommendations.append("Enable security headers in production")
            
            if not self.config.is_enabled('csrf'):
                recommendations.append("Enable CSRF protection in production")
            
            if not self.config.is_enabled('rate_limiting'):
                recommendations.append("Enable rate limiting in production")
            
            # Check HTTPS settings
            headers_config = self.config.get_security_headers_config()
            hsts_config = headers_config.get('strict_transport_security', {})
            if not hsts_config.get('enabled', True):
                recommendations.append("Enable HSTS in production")
        
        # Check for weak CSP settings
        if self.config.is_enabled('security_headers'):
            headers_config = self.config.get_security_headers_config()
            csp_config = headers_config.get('content_security_policy', {})
            
            if "'unsafe-inline'" in csp_config.get('script_src', []):
                recommendations.append("Remove 'unsafe-inline' from CSP script-src")
            
            if "'unsafe-eval'" in csp_config.get('script_src', []):
                recommendations.append("Remove 'unsafe-eval' from CSP script-src")
        
        return recommendations