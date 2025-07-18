"""
Security configuration management for enterprise security middleware.

This module provides centralized configuration management for all security
components including CORS, rate limiting, security headers, and monitoring.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import timedelta


class SecurityConfig:
    """Security configuration management"""
    
    def __init__(self, config_file: str = "security_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration from file or environment"""
        # Try to load from file first
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Fall back to default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default security configuration"""
        return {
            "cors": {
                "enabled": True,
                "origins": self._get_env_list("CORS_ORIGINS", ["http://localhost:3000", "http://localhost:5001"]),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "headers": ["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken"],
                "credentials": True,
                "max_age": 3600,
                "expose_headers": ["X-Total-Count", "X-Rate-Limit-Remaining"],
                "allow_headers": ["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"]
            },
            "rate_limiting": {
                "enabled": True,
                "default_limits": {
                    "per_minute": 60,
                    "per_hour": 1000,
                    "per_day": 10000
                },
                "endpoint_limits": {
                    "/api/v1/auth/login": {"per_minute": 5, "per_hour": 20},
                    "/api/v1/auth/register": {"per_minute": 2, "per_hour": 10},
                    "/api/v1/calculator/calculate": {"per_minute": 30, "per_hour": 500},
                    "/api/v1/pricing/": {"per_minute": 100, "per_hour": 2000}
                },
                "user_limits": {
                    "authenticated": {"per_minute": 120, "per_hour": 2000},
                    "premium": {"per_minute": 200, "per_hour": 5000}
                },
                "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
                "key_prefix": "rate_limit",
                "headers": {
                    "enabled": True,
                    "include_reset_time": True
                }
            },
            "security_headers": {
                "enabled": True,
                "strict_transport_security": {
                    "enabled": True,
                    "max_age": 31536000,
                    "include_subdomains": True,
                    "preload": True
                },
                "content_security_policy": {
                    "enabled": True,
                    "default_src": ["'self'"],
                    "script_src": ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
                    "style_src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
                    "img_src": ["'self'", "data:", "https:"],
                    "font_src": ["'self'", "https://fonts.gstatic.com"],
                    "connect_src": ["'self'", "wss:", "ws:"],
                    "frame_ancestors": ["'none'"],
                    "base_uri": ["'self'"],
                    "form_action": ["'self'"],
                    "upgrade_insecure_requests": True
                },
                "x_frame_options": "DENY",
                "x_content_type_options": "nosniff",
                "x_xss_protection": "1; mode=block",
                "referrer_policy": "strict-origin-when-cross-origin",
                "permissions_policy": {
                    "camera": [],
                    "microphone": [],
                    "geolocation": [],
                    "payment": [],
                    "usb": []
                },
                "feature_policy": {
                    "camera": "'none'",
                    "microphone": "'none'",
                    "geolocation": "'none'"
                }
            },
            "input_validation": {
                "enabled": True,
                "max_request_size": 10485760,  # 10MB
                "max_json_size": 1048576,     # 1MB
                "max_form_fields": 100,
                "max_field_length": 10000,
                "sanitize_html": True,
                "validate_json": True,
                "blocked_patterns": [
                    r"<script[^>]*>.*?</script>",
                    r"javascript:",
                    r"vbscript:",
                    r"on\w+\s*=",
                    r"expression\s*\(",
                    r"@import",
                    r"data:\s*text/html"
                ],
                "sql_injection_patterns": [
                    r"(\bunion\b.*\bselect\b)",
                    r"(\bselect\b.*\bfrom\b)",
                    r"(\binsert\b.*\binto\b)",
                    r"(\bupdate\b.*\bset\b)",
                    r"(\bdelete\b.*\bfrom\b)",
                    r"(\bdrop\b.*\btable\b)",
                    r"(\balter\b.*\btable\b)",
                    r"(\bcreate\b.*\btable\b)",
                    r"(\btruncate\b.*\btable\b)",
                    r"(\bexec\b.*\()",
                    r"(\bsp_executesql\b)",
                    r"(\bxp_cmdshell\b)"
                ]
            },
            "csrf": {
                "enabled": True,
                "secret_key": os.environ.get("CSRF_SECRET_KEY", "csrf-secret-key-change-in-production"),
                "token_lifetime": 3600,  # 1 hour
                "cookie_name": "csrf_token",
                "header_name": "X-CSRFToken",
                "cookie_secure": os.environ.get("FLASK_ENV") == "production",
                "cookie_httponly": True,
                "cookie_samesite": "Strict",
                "exempt_endpoints": ["/api/v1/auth/login", "/api/v1/auth/register"]
            },
            "monitoring": {
                "enabled": True,
                "log_security_events": True,
                "alert_on_attacks": True,
                "attack_detection": {
                    "enabled": True,
                    "thresholds": {
                        "failed_auth_attempts": 5,
                        "rate_limit_violations": 10,
                        "suspicious_requests": 20
                    },
                    "time_windows": {
                        "failed_auth": 300,      # 5 minutes
                        "rate_limit": 60,        # 1 minute
                        "suspicious": 600        # 10 minutes
                    }
                },
                "ip_blocking": {
                    "enabled": True,
                    "block_duration": 3600,     # 1 hour
                    "max_violations": 50,
                    "whitelist": self._get_env_list("IP_WHITELIST", ["127.0.0.1", "::1"])
                },
                "geo_blocking": {
                    "enabled": False,
                    "blocked_countries": [],
                    "allowed_countries": []
                }
            },
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256-GCM",
                "key_rotation_interval": 86400,  # 24 hours
                "session_encryption": True,
                "database_encryption": {
                    "enabled": False,
                    "fields": ["email", "phone", "address"]
                }
            }
        }
    
    def _get_env_list(self, env_var: str, default: List[str]) -> List[str]:
        """Get list from environment variable"""
        value = os.environ.get(env_var)
        if value:
            return [item.strip() for item in value.split(',')]
        return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving security config: {e}")
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return self.get('cors', {})
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return self.get('rate_limiting', {})
    
    def get_security_headers_config(self) -> Dict[str, Any]:
        """Get security headers configuration"""
        return self.get('security_headers', {})
    
    def get_input_validation_config(self) -> Dict[str, Any]:
        """Get input validation configuration"""
        return self.get('input_validation', {})
    
    def get_csrf_config(self) -> Dict[str, Any]:
        """Get CSRF protection configuration"""
        return self.get('csrf', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get security monitoring configuration"""
        return self.get('monitoring', {})
    
    def is_enabled(self, component: str) -> bool:
        """Check if security component is enabled"""
        return self.get(f'{component}.enabled', True)
    
    def get_environment(self) -> str:
        """Get current environment"""
        return os.environ.get('FLASK_ENV', 'development')
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.get_environment() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.get_environment() == 'development'
    
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.get_environment() == 'testing'