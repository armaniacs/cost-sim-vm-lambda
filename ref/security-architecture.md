# Security Architecture Reference

## Overview

This document provides comprehensive security implementation details for the AWS Lambda vs VM Cost Simulator application. The security architecture follows enterprise-grade standards with defense-in-depth principles, implementing multiple layers of protection against common web application vulnerabilities.

## Table of Contents

1. [Multi-Layer Security Architecture](#multi-layer-security-architecture)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Input Validation and Sanitization](#input-validation-and-sanitization)
4. [Security Headers and CORS Configuration](#security-headers-and-cors-configuration)
5. [Environment and Secret Management](#environment-and-secret-management)
6. [Container Security Practices](#container-security-practices)
7. [Production Security Implementation](#production-security-implementation)
8. [Security Testing and Vulnerability Scanning](#security-testing-and-vulnerability-scanning)
9. [Monitoring and Audit Logging](#monitoring-and-audit-logging)
10. [Compliance and Best Practices](#compliance-and-best-practices)

## Multi-Layer Security Architecture

### Architecture Overview

The application implements a comprehensive defense-in-depth strategy with the following security layers:

```
┌─────────────────────────────────────────────────────────┐
│                    User/Client                          │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│               Network Layer                             │
│  - HTTPS/TLS Encryption                                 │
│  - CORS Protection                                      │
│  - Rate Limiting                                        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            Application Layer                            │
│  - Security Headers                                     │
│  - JWT Authentication                                   │
│  - CSRF Protection                                      │
│  - Input Validation                                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Data Layer                                 │
│  - Environment Variable Protection                      │
│  - Secret Management                                    │
│  - Audit Logging                                        │
└─────────────────────────────────────────────────────────┘
```

### Security Modules

The security implementation is modularized into specialized components:

| Module | File | Purpose |
|--------|------|---------|
| Security Headers | `app/security/security_headers.py` | HTTP security headers management |
| Rate Limiting | `app/security/rate_limiter.py` | API throttling and DDoS protection |
| Input Validation | `app/security/input_validator.py` | XSS and injection prevention |
| CSRF Protection | `app/security/csrf_protection.py` | Cross-site request forgery protection |
| Environment Validation | `app/security/env_validator.py` | Secure configuration validation |
| Audit Logging | `app/security/audit_logger.py` | Security event logging |
| Security Monitor | `app/security/security_monitor.py` | Real-time threat detection |

## Authentication and Authorization

### JWT Authentication System

The application implements a comprehensive JWT-based authentication system:

```python
# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")  # Required
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
JWT_ALGORITHM = "HS256"
```

#### Authentication Flow

1. **User Registration/Login**
   - Secure password hashing using bcrypt
   - Input validation and sanitization
   - Rate limiting to prevent brute force attacks

2. **Token Generation**
   - Access tokens with short expiration (1 hour)
   - Refresh tokens with longer expiration (30 days)
   - Secure token storage and transmission

3. **Token Validation**
   - Signature verification using HMAC-SHA256
   - Expiration time validation
   - Token blacklisting support

#### Implementation Example

```python
from app.auth.jwt_auth import JWTAuth

# Initialize JWT authentication
jwt_auth = JWTAuth()
jwt_auth.init_app(app)

# Protected route decorator
@app.route('/api/v1/protected')
@jwt_auth.jwt_required()
def protected_route():
    current_user = jwt_auth.get_current_user()
    return jsonify({'user_id': current_user.id})
```

### CSRF Protection

Cross-Site Request Forgery protection is implemented using secure tokens:

```python
# CSRF Configuration
CSRF_SECRET_KEY = os.environ.get("CSRF_SECRET_KEY")  # Required
CSRF_TOKEN_EXPIRES = timedelta(hours=1)
CSRF_DOUBLE_SUBMIT = True  # Double submit cookie pattern
```

#### CSRF Implementation

```python
from app.security.csrf_protection import CSRFProtection

csrf = CSRFProtection()
csrf.init_app(app)

# CSRF token generation endpoint
@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf_token():
    token = csrf.generate_csrf_token()
    return jsonify({'csrf_token': token})

# Protected endpoint with CSRF validation
@app.route('/api/v1/calculator/lambda', methods=['POST'])
@csrf.csrf_required()
def calculate_lambda_cost():
    # CSRF token is automatically validated
    return process_lambda_calculation()
```

### Rate Limiting

Advanced rate limiting protects against abuse and DDoS attacks:

```python
# Rate Limiting Configuration
RATE_LIMITING = {
    "enabled": True,
    "redis_url": "redis://localhost:6379/0",
    "default_limits": {
        "per_minute": 60,
        "per_hour": 1000,
        "per_day": 10000
    },
    "endpoint_limits": {
        "/api/v1/calculator/*": {
            "per_minute": 30,
            "per_hour": 500
        },
        "/api/v1/auth/*": {
            "per_minute": 10,
            "per_hour": 100
        }
    }
}
```

#### Rate Limiting Features

- **Per-IP limiting**: Prevents abuse from single sources
- **Per-user limiting**: Authenticated user quotas
- **Endpoint-specific limits**: Different limits for different API endpoints
- **Burst protection**: Prevents rapid request bursts
- **Redis-based storage**: Distributed rate limiting support

## Input Validation and Sanitization

### Comprehensive Input Validation

The input validation system protects against multiple attack vectors:

```python
from app.security.input_validator import InputValidator

# Initialize input validator
validator = InputValidator()
validator.init_app(app)

# Validation rules configuration
VALIDATION_CONFIG = {
    "input_validation": {
        "enabled": True,
        "max_request_size": 10485760,  # 10MB
        "max_json_size": 1048576,     # 1MB
        "max_form_fields": 100,
        "max_field_length": 10000,
        "blocked_patterns": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"expression\s*\(",
            r"import\s+os",
            r"eval\s*\(",
            r"exec\s*\("
        ],
        "sql_injection_patterns": [
            r"(\b(select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(union|having|group\s+by|order\s+by)\b)",
            r"('|(\\x27)|(\\x2D)|(\\x2d))",
            r"(\b(or|and)\b.*[=<>])",
            r"(;|\s|^)(\s)*(exec|execute|sp_executesql)",
            r"(\b(xp_|sp_)\w+\b)"
        ]
    }
}
```

#### Input Validation Features

1. **XSS Prevention**
   - HTML entity encoding
   - Script tag filtering
   - Event handler removal
   - CSS expression blocking

2. **SQL Injection Prevention**
   - SQL keyword detection
   - Parameterized query enforcement
   - Special character filtering

3. **Path Traversal Prevention**
   - Directory traversal pattern detection
   - File path validation
   - URL encoding attack prevention

4. **Command Injection Prevention**
   - Shell command detection
   - System function blocking
   - Environment variable protection

#### Sanitization Methods

```python
# HTML content sanitization
sanitized_html = validator.sanitize_html(user_input)

# Text content sanitization
sanitized_text = validator.sanitize_text(user_input)

# Email validation
if validator.validate_email(email):
    process_email(email)

# URL validation
if validator.validate_url(url):
    process_url(url)
```

## Security Headers and CORS Configuration

### HTTP Security Headers

Comprehensive security headers implementation:

```python
# Security Headers Configuration
SECURITY_HEADERS = {
    "enabled": True,
    "strict_transport_security": {
        "enabled": True,
        "max_age": 31536000,  # 1 year
        "include_subdomains": True,
        "preload": True
    },
    "content_security_policy": {
        "enabled": True,
        "default_src": ["'self'"],
        "script_src": ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
        "style_src": ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
        "img_src": ["'self'", "data:", "https:"],
        "font_src": ["'self'", "fonts.gstatic.com"],
        "connect_src": ["'self'"],
        "media_src": ["'self'"],
        "object_src": ["'none'"],
        "child_src": ["'self'"],
        "frame_ancestors": ["'none'"],
        "base_uri": ["'self'"],
        "form_action": ["'self'"],
        "upgrade_insecure_requests": True,
        "block_all_mixed_content": False,
        "report_uri": "/api/v1/security/csp-report"
    },
    "x_frame_options": "DENY",
    "x_content_type_options": "nosniff",
    "x_xss_protection": "1; mode=block",
    "referrer_policy": "strict-origin-when-cross-origin",
    "permissions_policy": {
        "accelerometer": [],
        "camera": [],
        "geolocation": [],
        "gyroscope": [],
        "magnetometer": [],
        "microphone": [],
        "payment": [],
        "usb": []
    }
}
```

#### Security Headers Implementation

```python
from app.security.security_headers import SecurityHeaders

# Initialize security headers
security_headers = SecurityHeaders()
security_headers.init_app(app)

# CSP violation reporting endpoint
@app.route('/api/v1/security/csp-report', methods=['POST'])
def csp_report():
    report_data = request.get_json()
    if report_data and 'csp-report' in report_data:
        violation = report_data['csp-report']
        app.logger.warning(f"CSP Violation: {violation}")
    return '', 204
```

### CORS Configuration

Secure Cross-Origin Resource Sharing configuration:

```python
# CORS Configuration
CORS_CONFIG = {
    "origins": [
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "https://cost-simulator.example.com"
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type",
        "Authorization", 
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    "expose_headers": [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ],
    "supports_credentials": True,
    "max_age": 3600
}
```

#### CORS Implementation

```python
from flask_cors import CORS

# Initialize CORS with security configuration
allowed_origins = os.environ.get('CORS_ORIGINS', 
    'http://localhost:5001,http://127.0.0.1:5001').split(',')
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

CORS(app, 
    origins=allowed_origins,
    supports_credentials=True,
    methods=CORS_CONFIG["methods"],
    allow_headers=CORS_CONFIG["allow_headers"],
    expose_headers=CORS_CONFIG["expose_headers"]
)
```

## Environment and Secret Management

### Environment Variable Validation

Secure environment configuration with validation:

```python
from app.security.env_validator import validate_environment_or_exit

# Required security environment variables
REQUIRED_ENV_VARS = [
    "SECRET_KEY",           # Flask session secret
    "CSRF_SECRET_KEY",      # CSRF protection secret
    "JWT_SECRET_KEY"        # JWT signing secret
]

# Validate environment on application startup
validate_environment_or_exit()
```

#### Environment Validation Features

1. **Required Variable Checking**
   - Ensures all critical secrets are set
   - Prevents application startup without proper configuration

2. **Security Value Validation**
   - Checks for dangerous default values
   - Validates minimum entropy requirements
   - Warns about weak secret keys

3. **Configuration Analysis**
   - Environment-specific validation
   - Production security requirements
   - Development/testing flexibility

#### Environment Setup Example

```bash
# Generate secure random keys
export SECRET_KEY=$(openssl rand -hex 32)
export CSRF_SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET_KEY=$(openssl rand -hex 32)

# Application configuration
export FLASK_ENV=production
export PORT=5001
export HOST=0.0.0.0

# Security configuration
export CORS_ORIGINS="https://app.example.com,https://www.example.com"
export RATE_LIMIT_REDIS_URL="redis://redis:6379/0"
```

### Secret Management Best Practices

1. **Environment Variables**
   - Use environment variables for all secrets
   - Never commit secrets to version control
   - Rotate secrets regularly

2. **Production Deployment**
   - Use container orchestration secrets
   - Implement secret rotation policies
   - Monitor secret access

3. **Development Environment**
   - Use `.mise.local.toml` for local secrets
   - Provide example configuration files
   - Document secret generation procedures

## Container Security Practices

### Secure Docker Configuration

The application uses a multi-stage Docker build with security best practices:

```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV FLASK_APP=app.main
ENV FLASK_ENV=production
ENV PORT=5001
ENV HOST=0.0.0.0

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# Start application
CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0", "--port", "5001"]
```

#### Container Security Features

1. **Non-root User Execution**
   - Creates dedicated application user
   - Runs with minimal privileges
   - Prevents privilege escalation

2. **Minimal Attack Surface**
   - Uses slim base images
   - Removes unnecessary packages
   - Multi-stage build reduces image size

3. **Health Monitoring**
   - Implements health check endpoints
   - Container restart on failures
   - Resource monitoring

4. **Security Scanning**
   - Automated vulnerability scanning
   - Base image security updates
   - Dependency vulnerability checks

### Container Orchestration Security

For production deployment with Kubernetes:

```yaml
# Security context configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-simulator
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: cost-simulator
        image: cost-simulator:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "0.5"
            memory: "256Mi"
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret-key
```

## Production Security Implementation

### Security Configuration for Production

Production-specific security configuration:

```python
class ProductionConfig(Config):
    """Production configuration with enhanced security"""
    
    DEBUG = False
    TESTING = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # JWT settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    
    # Logging
    LOG_LEVEL = 'INFO'
    SECURITY_LOG_LEVEL = 'WARNING'
```

### TLS/SSL Configuration

HTTPS enforcement and secure communication:

```python
# Force HTTPS in production
@app.before_request
def force_https():
    if not request.is_secure and app.config['FLASK_ENV'] == 'production':
        return redirect(request.url.replace('http://', 'https://'))
```

### Security Middleware Stack

Complete middleware registration:

```python
def register_security_middleware(app):
    """Register all security middleware"""
    
    # Environment validation
    validate_environment_or_exit()
    
    # Security headers
    security_headers = SecurityHeaders(config=SECURITY_CONFIG)
    security_headers.init_app(app)
    
    # Rate limiting
    rate_limiter = RateLimiter(config=SECURITY_CONFIG)
    rate_limiter.init_app(app)
    
    # Input validation
    input_validator = InputValidator(config=SECURITY_CONFIG)
    input_validator.init_app(app)
    
    # CSRF protection
    csrf_protection = CSRFProtection(config=SECURITY_CONFIG)
    csrf_protection.init_app(app)
    
    # JWT authentication
    jwt_auth = JWTAuth(config=SECURITY_CONFIG)
    jwt_auth.init_app(app)
    
    # Audit logging
    audit_logger = AuditLogger(config=SECURITY_CONFIG)
    audit_logger.init_app(app)
    
    # Security monitoring
    security_monitor = SecurityMonitor(config=SECURITY_CONFIG)
    security_monitor.init_app(app)
```

## Security Testing and Vulnerability Scanning

### Automated Security Scanning

The application includes comprehensive security scanning in CI/CD:

```yaml
# GitHub Actions security workflow
name: Security Scanning

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install safety pip-audit

    - name: Run Safety check
      run: |
        safety check --json --output safety-report.json

    - name: Run pip-audit
      run: |
        pip-audit --format=json --output=pip-audit-report.json

  secret-scan:
    name: Secret Detection
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run TruffleHog
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        base: main
        head: HEAD
        extra_args: --debug --only-verified

  code-analysis:
    name: Static Code Analysis
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install analysis tools
      run: |
        python -m pip install --upgrade pip
        pip install bandit semgrep

    - name: Run Bandit security linter
      run: |
        bandit -r app/ -f json -o bandit-security-report.json

    - name: Run Semgrep
      run: |
        semgrep --config=auto app/ --json --output=semgrep-security-report.json

  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        load: true
        tags: cost-simulator:security-scan

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'cost-simulator:security-scan'
        format: 'sarif'
        output: 'trivy-results.sarif'
```

### Security Testing Tools

1. **Dependency Scanning**
   - **Safety**: Python dependency vulnerability scanner
   - **pip-audit**: Official Python package auditing tool
   - **Snyk**: Commercial dependency scanning

2. **Secret Detection**
   - **TruffleHog**: Git repository secret scanning
   - **GitLeaks**: Secret detection in git repositories
   - **detect-secrets**: Pre-commit secret detection

3. **Static Code Analysis**
   - **Bandit**: Python security linter
   - **Semgrep**: Multi-language static analysis
   - **CodeQL**: GitHub's semantic code analysis

4. **Container Scanning**
   - **Trivy**: Comprehensive container vulnerability scanner
   - **Clair**: Static analysis for container vulnerabilities
   - **Anchore**: Container security and compliance

### Manual Security Testing

Security testing procedures:

1. **Penetration Testing**
   - OWASP ZAP automated scanning
   - Manual vulnerability assessment
   - Authentication bypass testing
   - Session management testing

2. **Input Validation Testing**
   - XSS payload testing
   - SQL injection testing
   - Path traversal testing
   - Command injection testing

3. **API Security Testing**
   - Authentication testing
   - Authorization testing
   - Rate limiting validation
   - Input boundary testing

## Monitoring and Audit Logging

### Comprehensive Audit Logging

Security event logging and monitoring:

```python
from app.security.audit_logger import AuditLogger

class AuditLogger:
    """Comprehensive security audit logging"""
    
    def __init__(self, app=None, config=None):
        self.app = app
        self.config = config or {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize audit logging"""
        self.app = app
        
        # Configure structured logging
        self._setup_security_logging()
        
        # Register audit middleware
        self._register_audit_middleware()
    
    def _register_audit_middleware(self):
        """Register audit logging middleware"""
        
        @self.app.before_request
        def log_request():
            """Log incoming requests"""
            g.request_start_time = time.time()
            
            # Log authentication attempts
            if request.endpoint in ['auth.login', 'auth.register']:
                self.log_auth_attempt()
            
            # Log sensitive operations
            if request.endpoint and 'calculator' in request.endpoint:
                self.log_calculation_request()
        
        @self.app.after_request
        def log_response(response):
            """Log response and metrics"""
            request_time = time.time() - g.get('request_start_time', time.time())
            
            self.log_request_completed(response, request_time)
            return response
    
    def log_auth_attempt(self):
        """Log authentication attempts"""
        audit_data = {
            'event_type': 'authentication_attempt',
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'endpoint': request.endpoint,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': g.get('request_id', 'unknown')
        }
        
        self.app.logger.info(f"AUTH_ATTEMPT: {json.dumps(audit_data)}")
    
    def log_security_event(self, event_type, details):
        """Log security events"""
        audit_data = {
            'event_type': event_type,
            'details': details,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session.get('id', 'anonymous'),
            'request_id': g.get('request_id', 'unknown')
        }
        
        self.app.logger.warning(f"SECURITY_EVENT: {json.dumps(audit_data)}")
```

#### Audit Event Types

1. **Authentication Events**
   - Login attempts (successful/failed)
   - Token generation/validation
   - Session creation/destruction
   - Password changes

2. **Authorization Events**
   - Access attempts to protected resources
   - Permission escalation attempts
   - Role changes

3. **Security Events**
   - Rate limit violations
   - Input validation failures
   - CSRF token violations
   - Suspicious request patterns

4. **Application Events**
   - Cost calculations
   - Configuration changes
   - Administrative actions

### Security Monitoring

Real-time security monitoring implementation:

```python
from app.security.security_monitor import SecurityMonitor

class SecurityMonitor:
    """Real-time security monitoring and alerting"""
    
    def __init__(self, app=None, config=None):
        self.app = app
        self.config = config or {}
        self.threat_patterns = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security monitoring"""
        self.app = app
        
        # Load threat detection patterns
        self._load_threat_patterns()
        
        # Register monitoring middleware
        self._register_monitoring_middleware()
    
    def _register_monitoring_middleware(self):
        """Register security monitoring middleware"""
        
        @self.app.before_request
        def monitor_request():
            """Monitor incoming requests for threats"""
            
            # Check for suspicious patterns
            if self._detect_suspicious_activity():
                self._handle_suspicious_activity()
            
            # Monitor for brute force attacks
            if self._detect_brute_force():
                self._handle_brute_force_attack()
            
            # Check for anomalous behavior
            if self._detect_anomaly():
                self._handle_anomaly()
    
    def _detect_suspicious_activity(self):
        """Detect suspicious request patterns"""
        # Check user agent patterns
        user_agent = request.headers.get('User-Agent', '')
        if any(pattern in user_agent.lower() for pattern in self.threat_patterns.get('malicious_user_agents', [])):
            return True
        
        # Check for scanner signatures
        if any(pattern in request.path for pattern in self.threat_patterns.get('scanner_patterns', [])):
            return True
        
        return False
    
    def _detect_brute_force(self):
        """Detect brute force attack patterns"""
        if request.endpoint == 'auth.login':
            ip = request.remote_addr
            
            # Check failed login attempts in time window
            failed_attempts = self._get_failed_login_count(ip)
            if failed_attempts > 5:  # Configurable threshold
                return True
        
        return False
    
    def _handle_security_incident(self, incident_type, details):
        """Handle security incidents"""
        incident_data = {
            'type': incident_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'severity': self._calculate_severity(incident_type)
        }
        
        # Log incident
        self.app.logger.critical(f"SECURITY_INCIDENT: {json.dumps(incident_data)}")
        
        # Send alerts if configured
        if self.config.get('alerting', {}).get('enabled'):
            self._send_security_alert(incident_data)
        
        # Take automatic response if configured
        if self.config.get('auto_response', {}).get('enabled'):
            self._take_automatic_response(incident_type, incident_data)
```

### Metrics and Alerting

Security metrics collection:

```python
# Security metrics
SECURITY_METRICS = {
    'authentication_attempts': 0,
    'authentication_failures': 0,
    'rate_limit_violations': 0,
    'input_validation_failures': 0,
    'csrf_violations': 0,
    'security_incidents': 0,
    'blocked_ips': 0,
    'suspicious_requests': 0
}

def record_security_metric(metric_name, value=1, tags=None):
    """Record security metric"""
    if hasattr(current_app, 'monitoring_integration'):
        current_app.monitoring_integration.record_custom_metric(
            f'security.{metric_name}',
            value,
            tags=tags or {}
        )
```

## Compliance and Best Practices

### Security Standards Compliance

The application implements security controls aligned with industry standards:

1. **OWASP Top 10 Protection**
   - A01: Broken Access Control → JWT authentication, authorization checks
   - A02: Cryptographic Failures → Secure secret management, HTTPS enforcement
   - A03: Injection → Input validation, parameterized queries
   - A04: Insecure Design → Security-by-design architecture
   - A05: Security Misconfiguration → Environment validation, secure defaults
   - A06: Vulnerable Components → Dependency scanning, regular updates
   - A07: Authentication Failures → Strong authentication, rate limiting
   - A08: Software Integrity Failures → Code signing, container scanning
   - A09: Logging/Monitoring Failures → Comprehensive audit logging
   - A10: Server-Side Request Forgery → Input validation, URL filtering

2. **CIS Controls Alignment**
   - Inventory and Control of Hardware Assets
   - Inventory and Control of Software Assets
   - Continuous Vulnerability Management
   - Controlled Use of Administrative Privileges
   - Secure Configuration Management
   - Maintenance, Monitoring, and Analysis of Audit Logs
   - Malware Defenses
   - Data Recovery Capabilities
   - Security Skills Assessment and Training
   - Secure Network Architecture

### Security Best Practices Implementation

1. **Defense in Depth**
   - Multiple security layers
   - Fail-safe defaults
   - Principle of least privilege
   - Complete mediation

2. **Secure Development Lifecycle**
   - Security requirements analysis
   - Threat modeling
   - Secure coding practices
   - Security testing
   - Vulnerability management

3. **Incident Response**
   - Security monitoring
   - Incident detection
   - Response procedures
   - Recovery planning

### Security Configuration Checklist

#### Production Deployment Checklist

- [ ] All environment variables properly configured
- [ ] HTTPS/TLS properly configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] CSRF protection enabled
- [ ] JWT authentication configured
- [ ] Audit logging enabled
- [ ] Security monitoring active
- [ ] Container security implemented
- [ ] Dependency scanning configured
- [ ] Backup and recovery procedures tested

#### Security Maintenance

1. **Regular Updates**
   - Security patches applied within 48 hours
   - Dependency updates monthly
   - Base image updates weekly
   - Security tool updates weekly

2. **Security Reviews**
   - Code review for security issues
   - Configuration review quarterly
   - Access review monthly
   - Incident response testing quarterly

3. **Monitoring and Alerting**
   - Security event monitoring 24/7
   - Alert response procedures defined
   - Escalation procedures documented
   - Incident response team trained

### Conclusion

This security architecture provides comprehensive protection for the Cost Simulator application through multiple layers of defense, following industry best practices and standards. The implementation includes authentication, authorization, input validation, secure communication, monitoring, and incident response capabilities.

Regular security assessments, updates, and training are essential to maintain the security posture and adapt to evolving threats. The modular design allows for easy updates and enhancements as security requirements evolve.

For questions or security concerns, please refer to the security team or create an issue in the project repository.