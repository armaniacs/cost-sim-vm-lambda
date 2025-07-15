# Testing Framework Guide

## Testing Philosophy

The project follows **Outside-In Test-Driven Development (TDD)** combined with **Behavior-Driven Development (BDD)** principles, implementing the **t_wada methodology** for robust, maintainable test coverage.

## Test Architecture

### Three-Layer Testing Strategy

```
E2E Tests (13 tests)          ← User behavior validation
    ↓
Integration Tests (32 tests)  ← API contract validation  
    ↓
Unit Tests (38 tests)         ← Business logic validation
```

**Total Coverage**: 133 tests with 88% code coverage

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components and business logic in isolation

#### Test Files Overview

**`test_lambda_calculator.py`** (10 tests)
- Lambda cost calculation logic
- Free tier application
- Memory scaling and execution time calculations
- Egress cost integration
- Internet transfer ratio application (PBI10)

```python
def test_calculate_cost_with_free_tier():
    """Test Lambda cost calculation with free tier applied"""
    calculator = LambdaCalculator()
    config = LambdaConfig(
        memory_mb=512,
        execution_time_seconds=5,
        monthly_executions=500_000,  # Under free tier
        include_free_tier=True
    )
    
    result = calculator.calculate_cost(config)
    
    assert result["request_cost_usd"] == 0.0  # Covered by free tier
    assert result["total_cost_usd"] > 0  # Some compute costs
```

**`test_vm_calculator.py`** (18 tests)
- Multi-cloud VM pricing calculations
- Instance recommendation algorithms
- Currency conversion logic
- Provider-specific pricing validation

```python
def test_get_azure_cost_b1ls():
    """Test Azure B1ls (cheapest option) pricing"""
    calculator = VMCalculator()
    result = calculator.get_azure_cost("B1ls")
    
    assert result["hourly_cost_usd"] == 0.0092
    assert result["specs"]["memory_gb"] == 0.5
    assert result["provider"] == "azure"
```

**`test_egress_calculator.py`** (7 tests)
- Internet egress cost calculations
- Provider-specific free tier handling
- Transfer volume validation
- Multi-currency egress costs

**`test_app_creation.py`** (3 tests)
- Flask application factory testing
- Configuration validation
- Blueprint registration verification

#### Unit Test Patterns

**Arrange-Act-Assert Pattern**:
```python
def test_calculation_method():
    # Arrange: Set up test data
    calculator = Calculator()
    config = Configuration(param1=value1, param2=value2)
    
    # Act: Execute the method under test
    result = calculator.calculate(config)
    
    # Assert: Verify expected outcomes
    assert result["expected_field"] == expected_value
    assert result["total"] > 0
```

**Parameterized Testing**:
```python
@pytest.mark.parametrize("memory,expected_cost", [
    (128, 4.17),
    (512, 16.67),
    (1024, 33.33),
    (2048, 66.67)
])
def test_memory_scaling(memory, expected_cost):
    """Test Lambda cost scaling with memory size"""
    # Test implementation
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test API endpoints and component integration

#### Test Files Overview

**`test_egress_api.py`** (24 tests)
- Complete API integration testing
- Egress cost calculation workflows
- Multi-provider cost comparison
- Error handling and validation
- CSV export functionality

```python
def test_comparison_api_with_egress():
    """Test cost comparison API including egress calculations"""
    response = client.post('/api/v1/calculator/comparison', json={
        "lambda_config": {
            "memory_mb": 512,
            "execution_time_seconds": 5,
            "monthly_executions": 1_000_000,
            "egress_per_request_kb": 100
        },
        "vm_configs": [
            {"provider": "aws_ec2", "instance_type": "t3.small"}
        ]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "break_even_points" in data["data"]
```

**`test_google_cloud_api.py`** (8 tests)
- Google Cloud provider integration
- Asia-northeast1 region pricing
- Instance type validation
- GCP-specific cost calculations

#### Integration Test Features

**Flask Test Client**: 
```python
@pytest.fixture
def client():
    """Create Flask test client"""
    app = create_app("testing")
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

**API Contract Testing**:
- Request/response format validation
- HTTP status code verification
- Error message consistency
- Data type and structure validation

### 3. E2E Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows and business scenarios

#### Test Files Overview

**`test_egress_feature.py`** (4 tests)
- Complete egress cost calculation workflows
- Performance testing (<100ms requirement)
- CSV export integration testing
- Error handling scenarios

**`test_internet_transfer_ratio_feature.py`** (9 tests)
- PBI10 feature complete testing
- Preset ratio button functionality
- Custom ratio input validation
- Private network scenarios (0% ratio)

#### BDD Implementation

**Given-When-Then Structure**:
```python
def test_preset_transfer_ratio_calculation():
    """
    BDD Scenario: プリセット転送割合での計算
    Given: Lambda設定が入力されている
    When: インターネット転送割合を50%に設定する
    And: 計算を実行する
    Then: egress費用が50%に調整されて表示される
    """
    # Given: Lambda configuration
    lambda_config = {
        "memory_mb": 512,
        "execution_time_seconds": 5,
        "monthly_executions": 1_000_000,
        "egress_per_request_kb": 100,
        "internet_transfer_ratio": 50.0  # When: 50% ratio
    }
    
    # When: Execute calculation
    response = requests.post(f"{BASE_URL}/api/v1/calculator/lambda", 
                           json=lambda_config)
    
    # Then: Verify 50% egress adjustment
    assert response.status_code == 200
    data = response.json()["data"]
    expected_egress = full_egress_cost * 0.5
    assert abs(data["egress_cost_usd"] - expected_egress) < 0.01
```

#### E2E Test Scenarios

**Complete User Workflows**:
1. User inputs Lambda configuration
2. User selects VM providers for comparison
3. User configures egress and transfer settings
4. System calculates costs and break-even points
5. User exports results to CSV
6. System validates all data consistency

## Test Configuration

### pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=85
```

### Test Fixtures (`conftest.py`)

**Flask Application Fixture**:
```python
@pytest.fixture(scope="session")
def app():
    """Create application for testing"""
    app = create_app("testing")
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
```

**Data Fixtures**:
```python
@pytest.fixture
def sample_lambda_config():
    """Standard Lambda configuration for testing"""
    return {
        "memory_mb": 512,
        "execution_time_seconds": 5,
        "monthly_executions": 1_000_000,
        "include_free_tier": True,
        "egress_per_request_kb": 100.0,
        "internet_transfer_ratio": 100.0
    }
```

## Test Data Management

### Test Data Strategy

**Realistic Test Data**:
- Production-equivalent pricing data
- Real-world execution scenarios
- Edge case coverage (0 executions, maximum executions)
- Boundary value testing

**Test Data Categories**:
1. **Normal Cases**: Typical usage patterns
2. **Edge Cases**: Boundary conditions and limits
3. **Error Cases**: Invalid inputs and error conditions
4. **Performance Cases**: Large-scale scenarios

### Test Data Examples

```python
# Normal usage scenarios
NORMAL_TEST_CASES = [
    {
        "name": "small_workload",
        "memory_mb": 512,
        "monthly_executions": 100_000,
        "expected_lambda_cheaper": True
    },
    {
        "name": "large_workload", 
        "memory_mb": 1024,
        "monthly_executions": 10_000_000,
        "expected_vm_cheaper": True
    }
]

# Edge case scenarios
EDGE_TEST_CASES = [
    {"executions": 0, "expected_cost": 0},
    {"executions": 1, "expected_minimum_cost": True},
    {"memory_mb": 128, "expected_minimum_memory": True},
    {"memory_mb": 2048, "expected_maximum_memory": True}
]
```

## Coverage Analysis

### Current Coverage Metrics

**Overall Coverage**: 88% (478 lines covered, 56 missed)

**Module-level Coverage**:
- `lambda_calculator.py`: 98% (49/50 lines)
- `vm_calculator.py`: 98% (114/116 lines)  
- `egress_calculator.py`: 98% (42/43 lines)
- `calculator_api.py`: 81% (181/224 lines)
- `main.py`: 80% (35/44 lines)

**Uncovered Code Analysis**:
- Error handling paths (deliberate choice)
- Configuration edge cases
- Defensive programming checks

### Coverage Goals

**Target Coverage**: 90%+ overall
- **Critical Paths**: 100% coverage required
- **Business Logic**: 95%+ coverage required
- **Error Handling**: 80%+ coverage sufficient
- **Configuration**: 85%+ coverage sufficient

## Test Execution

### Running Tests

**Full Test Suite**:
```bash
make test          # Run all tests with coverage
make test-unit     # Run only unit tests
make test-integration  # Run only integration tests
make test-e2e      # Run only E2E tests
```

**Specific Test Files**:
```bash
# Run specific test file
pytest tests/unit/test_lambda_calculator.py -v

# Run specific test method
pytest tests/unit/test_vm_calculator.py::TestVMCalculator::test_get_azure_cost_b1ls -v

# Run tests matching pattern
pytest -k "egress" -v  # All egress-related tests
```

**Coverage Reports**:
```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Performance Testing

**Performance Requirements**:
- API response time < 100ms
- Chart rendering < 200ms
- CSV export < 500ms for 1000 data points

**Performance Test Example**:
```python
def test_api_performance():
    """Verify API performance meets requirements"""
    start_time = time.time()
    
    response = client.post('/api/v1/calculator/comparison', 
                          json=large_calculation_config)
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to ms
    
    assert response_time < 100, f"Response took {response_time}ms, expected <100ms"
    assert response.status_code == 200
```

## Test Best Practices

### Code Organization

**Test File Structure**:
```python
"""
Test module docstring describing test scope and purpose
"""
import pytest
from app.models.calculator import Calculator

class TestCalculatorFeature:
    """Test class for specific calculator feature"""
    
    def test_normal_case(self):
        """Test normal operation scenario"""
        pass
    
    def test_edge_case(self):
        """Test boundary conditions"""
        pass
    
    def test_error_case(self):
        """Test error handling"""
        pass
```

### Assertion Strategies

**Precise Assertions**:
```python
# Good: Specific assertion
assert result["total_cost_usd"] == pytest.approx(123.45, rel=1e-3)

# Good: Multiple specific assertions
assert response.status_code == 200
assert "success" in data
assert data["success"] is True

# Avoid: Vague assertion
assert result  # Too general
```

**Error Testing**:
```python
def test_invalid_input_handling():
    """Test proper error handling for invalid inputs"""
    with pytest.raises(ValueError, match="Invalid memory size"):
        calculator.calculate(invalid_config)
```

### Test Maintenance

**Regular Test Reviews**:
- Monthly test suite execution time review
- Quarterly test coverage analysis
- Annual test architecture assessment

**Test Refactoring Signals**:
- Tests taking > 100ms (except E2E)
- Test code duplication > 20%
- Flaky test failure rate > 1%
- Test maintenance time > 10% of development time

### Continuous Integration

**CI Pipeline Integration**:
```bash
# CI test execution
make check  # Includes formatting, linting, and testing

# Quality gates
- Test coverage must be ≥ 85%
- All tests must pass
- No linting errors
- Code formatting must be consistent
```

**Test Result Reporting**:
- JUnit XML format for CI integration
- Coverage badges for repository
- Performance trend tracking
- Test failure notifications