# Testing Framework Guide

## Overview

This document provides a comprehensive guide to the testing framework used in the Cost Simulator project. The framework implements an **Outside-In TDD + BDD** approach to ensure high-quality, maintainable code with excellent test coverage.

## Table of Contents

1. [Testing Methodology](#testing-methodology)
2. [Test Structure](#test-structure)
3. [Coverage Requirements](#coverage-requirements)
4. [Testing Tools and Frameworks](#testing-tools-and-frameworks)
5. [Test Execution Commands](#test-execution-commands)
6. [Test Writing Guidelines](#test-writing-guidelines)
7. [Mock and Stub Strategies](#mock-and-stub-strategies)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Continuous Integration](#continuous-integration)

## Testing Methodology

### Outside-In TDD + BDD Approach

The project follows **Outside-In Test-Driven Development (TDD)** combined with **Behavior-Driven Development (BDD)** principles:

#### Outside-In TDD Process
1. **Start with End-to-End (E2E) tests** - Define the behavior from the user's perspective
2. **Write Integration tests** - Test component interactions and API contracts
3. **Implement Unit tests** - Test individual classes and functions in isolation
4. **Red-Green-Refactor cycle** - Write failing test → Make it pass → Improve code quality

#### BDD Integration
- **Given-When-Then** scenarios for acceptance criteria
- **Business-readable test descriptions** using natural language
- **Feature-driven test organization** aligned with Product Backlog Items (PBIs)

### Test Pyramid Structure

```
        E2E Tests (13 tests)
       ┌─────────────────┐
      ┌─────────────────────┐
     │   Integration (32)   │
    ┌─────────────────────────┐
   │     Unit Tests (38)      │
  └──────────────────────────┘
```

## Test Structure

### Current Test Distribution (133 Total Tests)

#### Unit Tests (38 tests)
Located in `tests/unit/` - Test individual components in isolation:

- **Calculator Logic**: Lambda, VM, Serverless calculators
- **Business Logic**: Cost calculations, pricing algorithms
- **Data Models**: Configuration classes, result structures
- **Utilities**: Helper functions, validators
- **Services**: Authentication, monitoring, region management

**Example Unit Test Structure:**
```python
"""
Unit tests for Lambda cost calculation
Following t_wada TDD: Red -> Green -> Refactor
"""
import pytest
from app.models.lambda_calculator import LambdaCalculator, LambdaConfig

class TestLambdaCalculator:
    """Test AWS Lambda cost calculation logic"""
    
    def test_lambda_calculator_initialization(self):
        """Test LambdaCalculator can be initialized"""
        calculator = LambdaCalculator()
        assert calculator is not None
    
    def test_calculate_request_charges_without_free_tier(self):
        """Test request charges calculation without free tier"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,
            include_free_tier=False,
        )
        expected_charges = 0.40
        actual_charges = calculator.calculate_request_charges(config)
        assert actual_charges == pytest.approx(expected_charges, rel=1e-3)
```

#### Integration Tests (32 tests)
Located in `tests/integration/` - Test component interactions and API contracts:

- **API Endpoints**: REST API functionality and response validation
- **Database Integration**: Data persistence and retrieval
- **External Services**: Authentication providers, pricing APIs
- **Component Integration**: Service-to-service communication

**Example Integration Test Structure:**
```python
"""
Integration tests for authentication API endpoints
"""
import pytest
from unittest.mock import Mock, patch
from app.main import create_app

class TestAuthenticationAPI:
    """Test suite for authentication API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    def test_login_success(self, client, mock_auth_service):
        """Test successful login"""
        # Test implementation...
```

#### End-to-End Tests (13 tests)
Located in `tests/e2e/` - Test complete user workflows:

- **Security Features**: Authentication, authorization, data protection
- **Business Workflows**: Cost calculation end-to-end scenarios
- **User Interface**: Complete user interaction flows
- **Cross-Browser Testing**: Compatibility validation

**Example E2E Test Structure:**
```python
"""
E2E Tests for PBI-SEC-A: エンタープライズ認証・認可システム
BDDシナリオベースのテスト実装
"""
import pytest
import requests

class TestPBISecAAuthentication:
    """
    PBI-SEC-A E2Eテスト
    
    BDD受け入れシナリオ:
    1. システム管理者が安全な環境変数でアプリケーションを起動する
    2. 開発者が認証なしでAPIにアクセスを試みる (拒否される)
    3. 開発者が有効な認証でAPIにアクセスする (成功)
    """
    
    def test_authentication_flow_complete(self):
        """Complete authentication workflow test"""
        # Given: Application is running with secure configuration
        # When: User attempts to access protected endpoint
        # Then: Authentication is required and successful
```

### Test File Organization

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── fixtures/                  # Test data and fixtures
├── unit/                      # Unit tests (38 tests)
│   ├── test_lambda_calculator.py
│   ├── test_vm_calculator.py
│   ├── test_serverless_calculator.py
│   ├── test_auth_service.py
│   └── ...
├── integration/               # Integration tests (32 tests)
│   ├── test_auth_api.py
│   ├── test_egress_api.py
│   ├── test_google_cloud_api.py
│   └── ...
└── e2e/                      # End-to-end tests (13 tests)
    ├── test_pbi_sec_a_authentication.py
    ├── test_pbi_sec_b_secure_communications.py
    ├── test_egress_feature.py
    └── ...
```

## Coverage Requirements

### Minimum Coverage Targets

- **Overall Coverage**: 88% minimum (currently maintained)
- **Unit Test Coverage**: 95% minimum for business logic
- **Integration Test Coverage**: 80% minimum for API endpoints
- **Critical Path Coverage**: 100% for cost calculation logic

### Coverage Configuration

**pytest.ini configuration:**
```ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
```

### Coverage Exclusions

Excluded from coverage requirements:
- Configuration files
- Third-party integrations
- Development utilities
- Migration scripts

## Testing Tools and Frameworks

### Core Testing Stack

#### pytest (Primary Test Runner)
- **Version**: Latest stable
- **Features**: Fixtures, parametrization, markers
- **Plugins**: pytest-cov, pytest-mock, pytest-flask

#### unittest.mock (Mocking Framework)
- **Mock objects**: Isolate dependencies
- **Patch decorators**: Replace external dependencies
- **MagicMock**: Advanced mocking capabilities

#### Coverage.py (Code Coverage)
- **HTML reports**: Visual coverage analysis
- **Branch coverage**: Logical path coverage
- **Integration**: Seamless pytest integration

### Additional Tools

#### Black (Code Formatting)
```bash
black app/ tests/ --line-length 88
```

#### isort (Import Sorting)
```bash
isort app/ tests/ --profile black
```

#### flake8 (Linting)
```bash
flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
```

#### mypy (Type Checking)
```bash
mypy app/ --strict
```

## Test Execution Commands

### Daily Development Commands

#### Run All Tests
```bash
# Using make (recommended)
make test          # Full test suite with coverage
make t             # Short form

# Using mise
mise run test      # Full test suite with coverage

# Direct pytest
pytest tests/ --cov=app --cov-report=term-missing
```

#### Run Specific Test Categories
```bash
# Unit tests only
make test-unit
pytest tests/unit/ -v

# Integration tests only
mise run test-integration
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v

# Tests by marker
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "e2e" -v
```

#### Watch Mode (Continuous Testing)
```bash
make test-watch
pytest tests/ --cov=app -f
```

#### Specific Test Files or Functions
```bash
# Single test file
pytest tests/unit/test_lambda_calculator.py -v

# Single test function
pytest tests/unit/test_lambda_calculator.py::TestLambdaCalculator::test_calculation -v

# Pattern matching
pytest -k "lambda" -v
pytest -k "auth and not unit" -v
```

### Quality Assurance Commands

#### Pre-commit Checks
```bash
make check         # Format + Lint + Test
make pre-commit    # Run pre-commit hooks
```

#### Individual Quality Checks
```bash
make format        # Code formatting
make lint          # All linting checks
make security      # Security scanning
```

### Coverage Analysis

#### Generate Coverage Reports
```bash
# HTML report (detailed)
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=app --cov-report=term-missing

# XML report (for CI)
pytest tests/ --cov=app --cov-report=xml
```

## Test Writing Guidelines

### Naming Conventions

#### Test Files
- **Unit tests**: `test_<module_name>.py`
- **Integration tests**: `test_<feature>_api.py` or `test_<integration_name>.py`
- **E2E tests**: `test_<pbi_name>_<feature>.py`

#### Test Classes
- **Format**: `TestClassName` (matching the class being tested)
- **Example**: `TestLambdaCalculator`, `TestAuthenticationAPI`

#### Test Methods
- **Format**: `test_<action>_<expected_outcome>`
- **Examples**:
  - `test_calculate_lambda_cost_with_free_tier()`
  - `test_authentication_fails_with_invalid_credentials()`
  - `test_csv_export_generates_valid_format()`

### Test Structure (AAA Pattern)

#### Arrange-Act-Assert
```python
def test_calculate_lambda_cost_basic(self):
    """Test basic Lambda cost calculation"""
    # Arrange
    calculator = LambdaCalculator()
    config = LambdaConfig(
        memory_mb=512,
        execution_time_seconds=1.0,
        monthly_executions=1_000_000
    )
    
    # Act
    result = calculator.calculate_total_cost(config)
    
    # Assert
    assert result.total_cost > 0
    assert result.request_charges is not None
    assert result.compute_charges is not None
```

### BDD Test Structure (Given-When-Then)

```python
def test_user_authentication_workflow(self):
    """
    Given: A user with valid credentials
    When: They attempt to login
    Then: They receive a valid authentication token
    """
    # Given
    valid_credentials = {
        'email': 'test@example.com',
        'password': 'secure_password'
    }
    
    # When
    response = client.post('/api/auth/login', json=valid_credentials)
    
    # Then
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['user']['email'] == valid_credentials['email']
```

### Parameterized Tests

```python
@pytest.mark.parametrize("memory_mb,expected_tier", [
    (128, "free"),
    (512, "paid"),
    (1024, "paid"),
    (3008, "paid"),
])
def test_lambda_memory_tier_classification(memory_mb, expected_tier):
    """Test Lambda memory tier classification"""
    calculator = LambdaCalculator()
    tier = calculator.get_memory_tier(memory_mb)
    assert tier == expected_tier
```

### Test Fixtures

#### Shared Fixtures (conftest.py)
```python
@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app("testing")
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_lambda_config():
    """Sample Lambda configuration for testing"""
    return {
        "memory_mb": 512,
        "execution_time_seconds": 10,
        "monthly_executions": 1_000_000,
        "include_free_tier": True,
    }
```

## Mock and Stub Strategies

### External Dependencies Mocking

#### API Calls
```python
@patch('app.services.pricing_client.requests.get')
def test_fetch_pricing_data_success(self, mock_get):
    """Test successful pricing data retrieval"""
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = {'lambda_cost_per_request': 0.0000002}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Act
    pricing_client = PricingClient()
    data = pricing_client.fetch_lambda_pricing()
    
    # Assert
    assert data['lambda_cost_per_request'] == 0.0000002
    mock_get.assert_called_once()
```

#### Database Operations
```python
@patch('app.models.user.db.session')
def test_user_creation_database_error(self, mock_session):
    """Test user creation handles database errors gracefully"""
    # Arrange
    mock_session.add.side_effect = DatabaseError("Connection failed")
    
    # Act & Assert
    with pytest.raises(UserCreationError):
        user_service.create_user({'email': 'test@example.com'})
```

### Service Layer Mocking

#### Authentication Service
```python
@pytest.fixture
def mock_auth_service():
    """Mock authentication service"""
    with patch('app.api.auth_api.AuthService') as mock_service:
        mock_instance = Mock()
        mock_instance.authenticate_user.return_value = {
            'success': True,
            'user': {'id': 1, 'email': 'test@example.com'},
            'tokens': {'access_token': 'test_token'}
        }
        mock_service.return_value = mock_instance
        yield mock_instance
```

### Test Data Management

#### Factory Pattern for Test Data
```python
class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_lambda_config(**kwargs):
        """Create test Lambda configuration"""
        defaults = {
            'memory_mb': 512,
            'execution_time_seconds': 5.0,
            'monthly_executions': 1_000_000,
            'include_free_tier': True
        }
        defaults.update(kwargs)
        return LambdaConfig(**defaults)
    
    @staticmethod
    def create_vm_config(**kwargs):
        """Create test VM configuration"""
        defaults = {
            'provider': 'aws_ec2',
            'instance_type': 't3.small',
            'region': 'ap-northeast-1'
        }
        defaults.update(kwargs)
        return VMConfig(**defaults)
```

## Performance Testing

### Load Testing Strategy

#### Response Time Requirements
- **API Endpoints**: < 200ms for 95th percentile
- **Cost Calculations**: < 100ms for standard configurations
- **CSV Export**: < 2 seconds for 1000 records

#### Example Performance Test
```python
import time
import pytest

def test_lambda_calculation_performance():
    """Test Lambda calculation performance under load"""
    calculator = LambdaCalculator()
    config = LambdaConfig(
        memory_mb=512,
        execution_time_seconds=5.0,
        monthly_executions=10_000_000
    )
    
    # Measure execution time
    start_time = time.time()
    for _ in range(100):
        result = calculator.calculate_total_cost(config)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100
    assert avg_time < 0.1  # Less than 100ms average
```

### Memory Usage Testing

```python
import tracemalloc

def test_memory_usage_large_calculation():
    """Test memory usage for large calculations"""
    tracemalloc.start()
    
    calculator = LambdaCalculator()
    # Simulate large calculation
    for i in range(1000):
        config = LambdaConfig(
            memory_mb=512 + i,
            execution_time_seconds=1.0,
            monthly_executions=1_000_000
        )
        calculator.calculate_total_cost(config)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Assert memory usage is reasonable (less than 50MB)
    assert peak < 50 * 1024 * 1024
```

## Security Testing

### Input Validation Testing

#### SQL Injection Prevention
```python
def test_api_prevents_sql_injection(client):
    """Test API endpoints prevent SQL injection"""
    malicious_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "1; DELETE FROM calculations; --"
    ]
    
    for payload in malicious_payloads:
        response = client.post('/api/calculator/lambda', json={
            'memory_mb': payload,
            'execution_time_seconds': 1.0,
            'monthly_executions': 1000000
        })
        
        # Should return validation error, not execute malicious code
        assert response.status_code in [400, 422]
        assert 'error' in response.json
```

#### XSS Prevention
```python
def test_api_prevents_xss(client):
    """Test API prevents XSS attacks"""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for payload in xss_payloads:
        response = client.post('/api/calculator/vm', json={
            'provider': payload,
            'instance_type': 't3.small',
            'region': 'us-east-1'
        })
        
        assert response.status_code in [400, 422]
        # Ensure no script content in response
        assert '<script>' not in response.get_data(as_text=True)
```

### Authentication Security Testing

```python
def test_jwt_token_security(client):
    """Test JWT token security implementation"""
    # Test token expiration
    expired_token = generate_expired_jwt_token()
    headers = {'Authorization': f'Bearer {expired_token}'}
    
    response = client.get('/api/protected-endpoint', headers=headers)
    assert response.status_code == 401
    assert 'expired' in response.json['error'].lower()

def test_csrf_protection(client):
    """Test CSRF protection on state-changing operations"""
    # Attempt POST without CSRF token
    response = client.post('/api/calculator/save', json={
        'name': 'test_calculation',
        'config': {}
    })
    
    assert response.status_code == 403
    assert 'csrf' in response.json['error'].lower()
```

### Environment Security Testing

```python
def test_secure_environment_variables(app):
    """Test secure environment variable handling"""
    # Ensure sensitive data is not exposed
    assert app.config.get('SECRET_KEY') != 'default'
    assert app.config.get('JWT_SECRET_KEY') != 'default'
    assert len(app.config.get('SECRET_KEY', '')) >= 32
    
    # Ensure debug mode is off in production
    if app.config.get('FLASK_ENV') == 'production':
        assert app.config.get('DEBUG') is False
```

## Continuous Integration

### GitHub Actions Integration

The testing framework integrates with CI/CD pipelines:

#### Test Execution in CI
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11.8
      - name: Install dependencies
        run: make install
      - name: Run tests
        run: make test
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Quality Gates

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run test suite
        entry: make test
        language: system
        pass_filenames: false
        always_run: true
```

#### Coverage Requirements
- **Minimum overall coverage**: 88%
- **Coverage decrease prevention**: New code must maintain or improve coverage
- **Critical path coverage**: 100% for cost calculation logic

## Best Practices Summary

### Test Design Principles

1. **Follow AAA/Given-When-Then patterns** for clear test structure
2. **Use descriptive test names** that explain the scenario and expected outcome
3. **Test behavior, not implementation** to maintain test durability
4. **Keep tests independent** - no test should depend on another test's state
5. **Use appropriate test doubles** - mocks for verification, stubs for state

### Test Maintenance

1. **Regular test review** - Remove obsolete tests, update test data
2. **Refactor test code** - Apply DRY principles to test utilities
3. **Update test documentation** - Keep test intentions clear and current
4. **Monitor test performance** - Identify and optimize slow tests
5. **Maintain test coverage** - Ensure new features include comprehensive tests

### Common Anti-patterns to Avoid

1. **Testing implementation details** instead of behavior
2. **Creating interdependent tests** that break when run in isolation
3. **Writing overly complex tests** that are hard to understand and maintain
4. **Ignoring test failures** or accepting flaky tests
5. **Testing everything through the UI** instead of using appropriate test levels

## Conclusion

This testing framework provides a robust foundation for ensuring code quality and system reliability. By following the Outside-In TDD + BDD approach with comprehensive coverage at multiple test levels, the project maintains high confidence in its functionality while supporting rapid, safe development iterations.

For questions or improvements to this testing framework, refer to the development team or create an issue in the project repository.