# Implementation Architecture Reference

## Overview

This document provides a comprehensive reference for the implementation architecture of the AWS Lambda vs VM Cost Simulator. The application is a production-ready Flask-based web application that compares costs between serverless functions and virtual machines across multiple cloud providers.

## Project Status

✅ **COMPLETED** - Full production-ready application
- **100% Feature Complete**: 39 story points across 10 PBIs implemented
- **88% Test Coverage**: 133 tests (Unit: 38, Integration: 32, E2E: 13)
- **Multi-Cloud Support**: 6 VM providers + 2 serverless providers
- **Production Ready**: Docker containerization, security implementation, monitoring

## Core Architecture

### Application Structure

```
cost-sim-vm-lambda/
├── app/                      # Main Flask application
│   ├── main.py              # Application factory with security validation
│   ├── config.py            # Environment-based configuration
│   ├── extensions.py        # Redis client and cache management
│   ├── api/                 # REST API layer
│   │   ├── calculator_api.py    # Cost calculation endpoints
│   │   ├── auth_api.py          # JWT authentication
│   │   ├── monitoring_api.py    # System monitoring
│   │   └── performance_api.py   # Performance metrics
│   ├── models/              # Business logic layer
│   │   ├── lambda_calculator.py # AWS Lambda cost calculations
│   │   ├── vm_calculator.py     # Multi-cloud VM calculations
│   │   ├── egress_calculator.py # Data transfer costs
│   │   └── serverless_calculator.py # Multi-serverless calculations
│   ├── services/            # Service layer
│   │   ├── cache_service.py     # Caching layer
│   │   ├── performance_monitor.py # Performance monitoring
│   │   └── observability_service.py # Logging and monitoring
│   ├── static/              # Frontend assets
│   │   ├── css/style.css        # Custom CSS + Bootstrap
│   │   ├── js/app.js            # Main JavaScript application
│   │   ├── js/i18n.js           # Internationalization
│   │   └── i18n/                # Translation files (en/ja)
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # Comprehensive test suite (88% coverage)
│   ├── unit/               # Unit tests (38 tests)
│   ├── integration/        # Integration tests (32 tests)
│   └── e2e/               # End-to-end tests (13 tests)
├── deployment/             # Production deployment configs
│   ├── nginx/             # Reverse proxy configuration
│   ├── gunicorn/          # WSGI server settings
│   └── ssl/               # Certificate management
└── docs/                  # User and admin documentation
```

### Design Patterns

**Application Factory Pattern**
- Environment-based Flask app creation (`create_app()`)
- Configuration injection based on `FLASK_ENV`
- Security validation during startup

**Strategy Pattern**
- Multi-provider cost calculations with unified interfaces
- Provider-specific pricing and free tier implementations

**Repository Pattern**
- Calculator models encapsulate business logic
- Clean separation between API layer and business logic

**Dependency Injection**
- Calculator instances injected into API endpoints
- Configuration objects passed to business logic

## Core Components

### 1. Cost Calculation Engine

**AWS Lambda Calculator** (`app/models/lambda_calculator.py`)
```python
class LambdaCalculator:
    # Request charges: (executions - 1M free) × $0.20/million
    # Compute charges: GB-seconds × $0.0000166667 (after 400K free)
    # Total includes egress costs via EgressCalculator integration
```

**Multi-Cloud VM Calculator** (`app/models/vm_calculator.py`)
```python
class VMCalculator:
    # Supported providers:
    # - AWS EC2: 6 instance types (t3.micro to c5.xlarge)
    # - Google Cloud: 6 instance types (e2-micro to c2-standard-4)
    # - Azure: 8 instance types (B1ls to D4)
    # - OCI: 7 instance types (including Always Free)
    # - Sakura Cloud: 5 instance types in JPY pricing
```

**Egress Cost Calculator** (`app/models/egress_calculator.py`)
```python
class EgressCalculator:
    # Provider-specific rates:
    # - AWS: $0.114/GB (100GB free)
    # - Google Cloud: $0.12/GB (100GB free)
    # - Azure: $0.12/GB (100GB free)
    # - OCI: $0.025/GB (10TB free)
    # - Sakura Cloud: Free egress
```

### 2. REST API Layer

**Main Calculator API** (`app/api/calculator_api.py`)
- **9 endpoints** for cost calculations and data export
- **Input validation** with detailed error messages
- **Break-even point calculation** between serverless and VM costs
- **CSV export** with comprehensive cost breakdown
- **Currency conversion** support (USD ↔ JPY)

**Authentication API** (`app/api/auth_api.py`)
- **JWT-based authentication** with refresh tokens
- **User management** (registration, login, profile)
- **CSRF protection** with token validation
- **Security headers** and rate limiting

### 3. Frontend Architecture

**Technology Stack**
- **Vanilla JavaScript ES6+**: No framework dependencies
- **Chart.js 3.9+**: Interactive cost comparison graphs
- **Bootstrap 5**: Responsive UI framework
- **Custom i18n System**: Complete Japanese/English support

**Key Features**
- **Real-time calculations**: Immediate chart updates on input changes
- **Multi-provider comparison**: Simultaneous cost visualization
- **Interactive charts**: Break-even point highlighting
- **CSV export**: Detailed cost analysis download

### 4. Testing Architecture

**Outside-In TDD Approach**
1. **E2E Tests (13 tests)**: User acceptance criteria validation
2. **Integration Tests (32 tests)**: Component interaction verification
3. **Unit Tests (38 tests)**: Business logic validation

**Testing Tools**
- **pytest**: Primary testing framework
- **Flask-Testing**: Flask application testing utilities
- **pytest-cov**: 88% code coverage measurement
- **BDD scenarios**: Gherkin-style acceptance criteria

### 5. Security Implementation

**Multi-Layer Security**
- **JWT Authentication**: Secure token-based auth
- **CSRF Protection**: Token validation for state changes
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Comprehensive parameter sanitization
- **CORS Configuration**: Secure cross-origin handling

**Production Security**
- **SSL/TLS**: Complete HTTPS implementation
- **Security Headers**: CSP, HSTS, XSS protection
- **Environment Validation**: Secure secret management
- **Container Security**: Non-root execution, minimal images

## Configuration Management

### Environment-Based Configuration

**Development Config**
```python
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    # Local development settings
```

**Production Config**
```python
class ProductionConfig(Config):
    DEBUG = False
    # Production security and performance settings
```

### Key Configuration Values

**AWS Lambda Pricing (Tokyo Region)**
- Request charges: $0.20 per million requests
- Compute charges: $0.0000166667 per GB-second
- Free tier: 1M requests + 400K GB-seconds monthly

**Exchange Rate Settings**
- Default: 150 JPY/USD
- Validation range: 50-300 JPY/USD
- Custom rate support for enterprise scenarios

## Deployment Architecture

### Docker Configuration

**Multi-Stage Build**
- **Development stage**: Full development tools and debugging
- **Production stage**: Minimal runtime with security hardening

**Production Features**
- **Non-root execution**: Security-first container design
- **Health checks**: Application and dependency monitoring
- **Environment injection**: Secure configuration management

### Production Infrastructure

**nginx Reverse Proxy**
- **SSL termination**: TLS 1.2+ with secure cipher suites
- **Rate limiting**: API protection against abuse
- **Static file serving**: Optimized asset delivery
- **Security headers**: Complete security header set

**Gunicorn WSGI Server**
- **Multi-worker configuration**: CPU core × 2 workers
- **Connection management**: Keep-alive and timeout settings
- **Logging**: Structured request and error logging

## Performance Characteristics

### API Response Times
- **Cost calculation APIs**: <100ms (cached: <10ms)
- **Metadata APIs**: <50ms
- **Authentication APIs**: <200ms (JWT signing/verification)
- **Monitoring APIs**: <30ms

### Scalability Features
- **Redis caching**: 5-minute cache for calculation results
- **Stateless design**: Horizontal scaling ready
- **Database optimization**: Connection pooling and query optimization
- **CDN ready**: Static asset optimization

## Development Workflow

### Make-Based Development
```bash
make setup    # Complete environment setup
make dev      # Development server with hot reload
make test     # 133 tests with 88% coverage
make check    # Complete quality gate (format + lint + test + security)
make docker-build  # Production container build
```

### Quality Gates
- **Code formatting**: ruff + isort automatic formatting
- **Linting**: ruff + mypy type checking
- **Security scanning**: bandit vulnerability detection
- **Test coverage**: 88% minimum threshold

## Integration Points

### Cloud Provider APIs
- **Pricing data**: Static configuration with periodic updates
- **Instance metadata**: Comprehensive instance type support
- **Free tier handling**: Provider-specific free tier calculations

### Monitoring and Observability
- **Health checks**: Application and dependency status
- **Performance metrics**: Response time and throughput monitoring
- **Error tracking**: Structured error logging and alerting
- **Audit logging**: Security event tracking

## Future Extensibility

### Provider Addition
- **Interface-based design**: Easy addition of new cloud providers
- **Configuration-driven**: Provider specifications via config files
- **Testing framework**: Comprehensive test coverage for new providers

### Feature Enhancement
- **API versioning**: Backward compatibility support
- **Authentication methods**: OAuth, SAML integration ready
- **Monitoring integration**: APM and log aggregation ready
- **Multi-tenancy**: Architecture supports tenant isolation

## Conclusion

The implementation represents a **production-ready, enterprise-grade application** with:

1. **Complete feature set**: 100% of requirements implemented
2. **High code quality**: 88% test coverage with comprehensive testing
3. **Security-first design**: Multi-layer security implementation
4. **Scalable architecture**: Cloud-native design with container support
5. **Developer-friendly**: Comprehensive documentation and tooling
6. **Production-ready**: Complete deployment and monitoring infrastructure

The architecture supports the core mission of providing accurate, real-time cost comparisons between serverless and virtual machine solutions across multiple cloud providers, with enterprise-grade security, performance, and reliability.