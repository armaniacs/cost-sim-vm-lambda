# Enterprise Security Middleware

This module provides comprehensive enterprise-grade security middleware for the Flask application, including CORS configuration, rate limiting, security headers, input validation, CSRF protection, and security monitoring.

## Components

### 1. SecurityMiddleware (`middleware.py`)
The main security middleware class that integrates all security components:
- Unified initialization and configuration
- Security API endpoints
- Component coordination
- Monitoring integration

### 2. CORSConfig (`cors_config.py`)
Advanced CORS configuration with:
- Dynamic origin validation
- Pattern matching for origins
- Subdomain support
- Preflight request handling
- Credentials management

### 3. RateLimiter (`rate_limiter.py`)
Comprehensive rate limiting with:
- Per-IP rate limiting
- Per-user rate limiting
- Endpoint-specific limits
- Redis backend storage
- Burst protection
- Rate limit headers

### 4. SecurityHeaders (`security_headers.py`)
HTTP security headers implementation:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer Policy
- Permissions Policy

### 5. InputValidator (`input_validator.py`)
Input validation and sanitization:
- XSS prevention
- SQL injection detection
- Path traversal protection
- Command injection prevention
- Request size validation
- Content type validation

### 6. CSRFProtection (`csrf_protection.py`)
CSRF protection with:
- Token generation and validation
- Cookie-based storage
- Header validation
- Exempt endpoints
- Token refresh mechanism

### 7. SecurityMonitor (`security_monitor.py`)
Security monitoring and attack detection:
- Security event logging
- Attack pattern recognition
- IP blocking
- Suspicious activity detection
- Integration with monitoring system

### 8. SecurityConfig (`config.py`)
Centralized configuration management:
- Environment-specific settings
- JSON configuration file support
- Runtime configuration updates
- Validation and recommendations

## Usage

### Basic Usage

```python
from flask import Flask
from app.security.middleware import SecurityMiddleware

app = Flask(__name__)
security_middleware = SecurityMiddleware(app)
```

### Custom Configuration

```python
from app.security.middleware import SecurityMiddleware
from app.security.config import SecurityConfig

# Load custom configuration
config = SecurityConfig('custom_security_config.json')
security_middleware = SecurityMiddleware(app, config)
```

### Component Access

```python
# Access specific components
cors_config = security_middleware.get_component('cors')
rate_limiter = security_middleware.get_component('rate_limiter')
security_monitor = security_middleware.get_component('security_monitor')
```

## Configuration

### Environment Variables

```bash
# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5001

# Rate Limiting
REDIS_URL=redis://localhost:6379/0

# CSRF Protection
CSRF_SECRET_KEY=your-csrf-secret-key

# IP Whitelist
IP_WHITELIST=127.0.0.1,::1
```

### Configuration File

Create a `security_config.json` file:

```json
{
  "cors": {
    "enabled": true,
    "origins": ["http://localhost:3000"],
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "credentials": true
  },
  "rate_limiting": {
    "enabled": true,
    "default_limits": {
      "per_minute": 60,
      "per_hour": 1000
    },
    "endpoint_limits": {
      "/api/v1/auth/login": {
        "per_minute": 5,
        "per_hour": 20
      }
    }
  },
  "security_headers": {
    "enabled": true,
    "content_security_policy": {
      "enabled": true,
      "default_src": ["'self'"],
      "script_src": ["'self'", "'unsafe-inline'"]
    }
  },
  "input_validation": {
    "enabled": true,
    "max_request_size": 10485760,
    "sanitize_html": true
  },
  "csrf": {
    "enabled": true,
    "token_lifetime": 3600,
    "cookie_secure": true
  },
  "monitoring": {
    "enabled": true,
    "attack_detection": {
      "enabled": true,
      "thresholds": {
        "failed_auth_attempts": 5,
        "rate_limit_violations": 10
      }
    },
    "ip_blocking": {
      "enabled": true,
      "block_duration": 3600
    }
  }
}
```

## API Endpoints

The security middleware provides several API endpoints:

### Security Status
- `GET /api/v1/security/status` - Get security middleware status
- `GET /api/v1/security/config` - Get security configuration
- `PUT /api/v1/security/config` - Update security configuration
- `GET /api/v1/security/stats` - Get security statistics

### IP Management
- `GET /api/v1/security/blocked-ips` - Get blocked IPs
- `DELETE /api/v1/security/blocked-ips/<ip>` - Unblock IP
- `GET /api/v1/security/whitelist` - Get IP whitelist
- `POST /api/v1/security/whitelist` - Add IP to whitelist

### Rate Limiting
- `GET /api/v1/security/rate-limit/<identifier>` - Get rate limit status
- `DELETE /api/v1/security/rate-limit/<identifier>` - Reset rate limit

### Input Validation
- `POST /api/v1/security/input-validation/test` - Test input validation

### CSRF Protection
- `GET /api/v1/security/csrf-token` - Get CSRF token
- `POST /api/v1/security/csrf-validate` - Validate CSRF token

### CSP Management
- `GET /api/v1/security/csp-config` - Get CSP configuration
- `PUT /api/v1/security/csp-config` - Update CSP configuration
- `POST /api/v1/security/csp-report` - CSP violation reports

## Dependencies

The security middleware requires the following packages:

```
bleach==6.1.0          # HTML sanitization
Werkzeug==3.0.1        # Security utilities
Flask-Limiter==3.5.0   # Rate limiting
Flask-Talisman==1.1.0  # Security headers
redis==5.0.1           # Redis backend
```

## Security Features

### 1. CORS Protection
- Origin validation with pattern matching
- Subdomain support
- Preflight request handling
- Credential management

### 2. Rate Limiting
- Multiple rate limit types (IP, user, endpoint)
- Redis-based storage
- Configurable time windows
- Rate limit headers

### 3. Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer Policy
- Permissions Policy

### 4. Input Validation
- XSS prevention
- SQL injection detection
- Path traversal protection
- Command injection prevention
- Request size limits
- Content type validation

### 5. CSRF Protection
- Token-based protection
- Cookie storage
- Header validation
- Exempt endpoints
- Token refresh

### 6. Security Monitoring
- Attack detection
- IP blocking
- Security event logging
- Suspicious activity monitoring
- Integration with monitoring system

## Production Deployment

### Security Checklist

1. **HTTPS Only**: Enable HSTS and secure cookies
2. **Strong CSP**: Remove unsafe-inline and unsafe-eval
3. **Rate Limiting**: Configure appropriate limits
4. **IP Blocking**: Enable automatic IP blocking
5. **Monitoring**: Enable security event logging
6. **Secrets**: Use strong secret keys
7. **Redis**: Secure Redis configuration
8. **Geo-blocking**: Consider geo-location restrictions

### Configuration Recommendations

For production environments:

```json
{
  "security_headers": {
    "strict_transport_security": {
      "enabled": true,
      "max_age": 31536000,
      "include_subdomains": true,
      "preload": true
    }
  },
  "csrf": {
    "cookie_secure": true,
    "cookie_httponly": true,
    "cookie_samesite": "Strict"
  },
  "monitoring": {
    "attack_detection": {
      "enabled": true
    },
    "ip_blocking": {
      "enabled": true
    }
  }
}
```

## Monitoring Integration

The security middleware integrates with the existing monitoring system:

```python
# Record security metrics
security_middleware.get_component('security_monitor').record_security_event(
    'login_attempt',
    {'ip': '192.168.1.1', 'success': False}
)

# Send security alerts
security_middleware.get_component('security_monitor').send_security_alert(
    'brute_force_detected',
    {'ip': '192.168.1.1', 'attempts': 10}
)
```

## Testing

The security middleware includes comprehensive testing utilities:

```python
# Test input validation
result = security_middleware.get_component('input_validator').test_input(
    "<script>alert('xss')</script>"
)

# Test CSRF token
token = security_middleware.get_component('csrf_protection').get_csrf_token()
is_valid = security_middleware.get_component('csrf_protection').is_token_valid(token)

# Test rate limiting
status = security_middleware.get_component('rate_limiter').get_rate_limit_status(
    '192.168.1.1', 'ip'
)
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**: Check Redis URL and connectivity
2. **CORS Errors**: Verify origin configuration
3. **Rate Limiting Too Aggressive**: Adjust limits in configuration
4. **CSP Violations**: Check CSP report endpoint for violations
5. **CSRF Token Errors**: Verify token generation and validation

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.security').setLevel(logging.DEBUG)
```

### Health Check

Use the status endpoint to verify security middleware:

```bash
curl http://localhost:5001/api/v1/security/status
```

## License

This security middleware is part of the enterprise cost management platform and follows the same licensing terms.