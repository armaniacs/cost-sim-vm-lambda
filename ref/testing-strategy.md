# Testing Strategy

## Overview

This project implements a comprehensive testing strategy following **t_wada style Test-Driven Development** with emphasis on high-quality, maintainable tests.

## Testing Philosophy

### t_wada TDD Principles
1. **Red**: Write a failing test that describes desired behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

### Test Quality Standards
- **Descriptive Names**: Tests clearly describe what they verify
- **Arrange-Act-Assert**: Clear test structure
- **Single Responsibility**: Each test verifies one behavior
- **Fast Execution**: Unit tests complete in milliseconds
- **Isolated**: Tests don't depend on each other

## Test Architecture

### Test Structure
```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── unit/                          # Unit tests (isolated components)
│   ├── test_app_creation.py      # Flask app factory tests
│   ├── test_lambda_calculator.py # Lambda calculation logic
│   └── test_vm_calculator.py     # VM calculation logic
├── integration/                   # Integration tests (component interaction)
│   ├── test_api_endpoints.py     # API endpoint testing
│   └── test_data_flow.py         # End-to-end data flow
├── e2e/                          # End-to-end tests (full user workflows)
│   ├── test_user_workflows.py    # Complete user scenarios
│   └── test_browser_integration.py # Frontend integration
└── fixtures/                     # Test data and utilities
    ├── sample_data.py            # Standard test configurations
    └── mock_responses.py         # API response mocks
```

### Test Configuration (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90

markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interaction
    e2e: End-to-end tests for complete workflows
    slow: Tests that take longer than usual to run
```

## Unit Testing

### Current Coverage: 100% for Business Logic

#### Lambda Calculator Tests
```python
class TestLambdaCalculator:
    """Test AWS Lambda cost calculation logic"""

    def test_vm_calculator_initialization(self):
        """Test LambdaCalculator can be initialized"""
        calculator = LambdaCalculator()
        assert calculator is not None

    def test_lambda_config_creation(self):
        """Test LambdaConfig data class creation"""
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10, 
            monthly_executions=1_000_000,
            include_free_tier=True
        )
        
        assert config.memory_mb == 512
        assert config.execution_time_seconds == 10
        assert config.monthly_executions == 1_000_000
        assert config.include_free_tier is True

    def test_request_charges_with_free_tier(self):
        """Test request charges include free tier deduction"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,  # Exceeds free tier
            include_free_tier=True
        )
        
        charges = calculator.calculate_request_charges(config)
        
        # Should charge for 1M executions after free tier deduction
        expected = 1_000_000 * 0.20 / 1_000_000  # $0.20
        assert charges == expected

    def test_compute_charges_calculation(self):
        """Test compute charges based on GB-seconds"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=1_000_000,
            include_free_tier=False  # No free tier for clear calculation
        )
        
        gb_seconds = calculator.calculate_gb_seconds(config)
        expected_gb_seconds = (512 / 1024) * 10 * 1_000_000  # 5M GB-seconds
        assert gb_seconds == expected_gb_seconds
        
        charges = calculator.calculate_compute_charges(config)
        expected_charges = expected_gb_seconds * 0.0000166667
        assert abs(charges - expected_charges) < 0.01  # Allow small floating point differences

    def test_total_cost_calculation(self):
        """Test complete cost calculation with all components"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=1_000_000,
            include_free_tier=True
        )
        
        result = calculator.calculate_total_cost(config)
        
        # Verify result structure
        assert "request_charges" in result
        assert "compute_charges" in result
        assert "total_cost" in result
        assert "gb_seconds" in result
        assert "configuration" in result
        
        # Verify calculation accuracy
        expected_total = result["request_charges"] + result["compute_charges"]
        assert result["total_cost"] == expected_total
```

#### VM Calculator Tests
```python
class TestVMCalculator:
    """Test VM cost calculation logic"""

    def test_get_ec2_cost_valid_instance(self):
        """Test EC2 cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_ec2_cost("t3.small")
        
        assert result is not None
        assert result["provider"] == "aws_ec2"
        assert result["instance_type"] == "t3.small"
        assert result["hourly_cost_usd"] == 0.0272
        assert result["monthly_cost_usd"] == pytest.approx(19.856, rel=1e-3)
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 2

    def test_get_sakura_cost_valid_instance(self):
        """Test Sakura Cloud cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_sakura_cost("2core_4gb")
        
        assert result is not None
        assert result["provider"] == "sakura_cloud"
        assert result["instance_type"] == "2core_4gb"
        assert result["monthly_cost_jpy"] == 4180
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 4

    def test_recommend_instance_for_lambda_512mb(self):
        """Test instance recommendation for 512MB Lambda"""
        calculator = VMCalculator()
        recommendations = calculator.recommend_instance_for_lambda(512)
        
        # Should recommend instances with >= 0.5GB memory
        assert "aws_ec2" in recommendations
        assert "sakura_cloud" in recommendations
        
        # EC2 recommendations should be sorted by memory ratio
        ec2_recs = recommendations["aws_ec2"]
        assert len(ec2_recs) > 0
        assert ec2_recs[0]["memory_ratio"] >= 1.0
        
        # Should have t3.micro (1GB) as closest match
        ec2_types = [rec["instance_type"] for rec in ec2_recs]
        assert "t3.micro" in ec2_types
```

### Test Fixtures (conftest.py)
```python
import pytest
from app.main import create_app
from app.models.lambda_calculator import LambdaConfig
from app.models.vm_calculator import VMConfig

@pytest.fixture
def app():
    """Create Flask application for testing"""
    app = create_app("testing")
    return app

@pytest.fixture
def client(app):
    """Create test client for API testing"""
    return app.test_client()

@pytest.fixture
def sample_lambda_config():
    """Standard Lambda configuration for testing"""
    return LambdaConfig(
        memory_mb=512,
        execution_time_seconds=10,
        monthly_executions=1_000_000,
        include_free_tier=True
    )

@pytest.fixture
def sample_vm_config():
    """Standard VM configuration for testing"""
    return VMConfig(
        provider="aws_ec2",
        instance_type="t3.small",
        region="ap-northeast-1"
    )

@pytest.fixture
def sample_api_response():
    """Mock API response for testing"""
    return {
        "success": True,
        "data": {
            "comparison_data": [
                {
                    "executions_per_month": 1000000,
                    "lambda_cost_usd": 8.33,
                    "vm_costs": {
                        "aws_ec2_t3_small": 19.86
                    }
                }
            ],
            "break_even_points": [
                {
                    "vm_provider": "aws_ec2",
                    "vm_instance": "t3_small",
                    "executions_per_month": 2380952,
                    "executions_per_second": 0.92
                }
            ]
        }
    }
```

## Integration Testing

### API Endpoint Testing
```python
class TestCalculatorAPI:
    """Test REST API endpoints"""

    def test_lambda_cost_calculation_endpoint(self, client):
        """Test Lambda cost calculation API"""
        response = client.post('/api/v1/calculator/lambda', json={
            'memory_mb': 512,
            'execution_time_seconds': 10,
            'monthly_executions': 1_000_000,
            'include_free_tier': True
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'total_cost' in data['data']
        assert data['data']['total_cost'] > 0

    def test_vm_cost_calculation_endpoint(self, client):
        """Test VM cost calculation API"""
        response = client.post('/api/v1/calculator/vm', json={
            'provider': 'aws_ec2',
            'instance_type': 't3.small'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['monthly_cost_usd'] > 0

    def test_comparison_endpoint(self, client):
        """Test cost comparison API"""
        response = client.post('/api/v1/calculator/comparison', json={
            'lambda_config': {
                'memory_mb': 512,
                'execution_time_seconds': 10,
                'include_free_tier': True
            },
            'vm_configs': [
                {'provider': 'aws_ec2', 'instance_type': 't3.small'}
            ],
            'execution_range': {
                'min': 0,
                'max': 10000000,
                'steps': 10
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'comparison_data' in data['data']
        assert len(data['data']['comparison_data']) == 10

    def test_invalid_input_handling(self, client):
        """Test API error handling for invalid inputs"""
        response = client.post('/api/v1/calculator/lambda', json={
            'memory_mb': 'invalid',  # Should be integer
            'execution_time_seconds': 10
            # Missing required fields
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
```

### Data Flow Testing
```python
class TestDataFlow:
    """Test complete data flow from input to output"""

    def test_lambda_to_vm_comparison_flow(self, client):
        """Test complete comparison calculation flow"""
        # Step 1: Calculate Lambda cost
        lambda_response = client.post('/api/v1/calculator/lambda', json={
            'memory_mb': 512,
            'execution_time_seconds': 10,
            'monthly_executions': 2_000_000,
            'include_free_tier': True
        })
        
        lambda_cost = lambda_response.get_json()['data']['total_cost']
        
        # Step 2: Calculate VM cost
        vm_response = client.post('/api/v1/calculator/vm', json={
            'provider': 'aws_ec2',
            'instance_type': 't3.small'
        })
        
        vm_cost = vm_response.get_json()['data']['monthly_cost_usd']
        
        # Step 3: Verify comparison logic
        comparison_response = client.post('/api/v1/calculator/comparison', json={
            'lambda_config': {
                'memory_mb': 512,
                'execution_time_seconds': 10,
                'include_free_tier': True
            },
            'vm_configs': [
                {'provider': 'aws_ec2', 'instance_type': 't3.small'}
            ],
            'execution_range': {
                'min': 2_000_000,
                'max': 2_000_000,
                'steps': 1
            }
        })
        
        comparison_data = comparison_response.get_json()['data']
        comparison_point = comparison_data['comparison_data'][0]
        
        # Verify consistency between individual and comparison calculations
        assert abs(comparison_point['lambda_cost_usd'] - lambda_cost) < 0.01
        assert abs(comparison_point['vm_costs']['aws_ec2_t3_small'] - vm_cost) < 0.01

    def test_currency_conversion_integration(self, client):
        """Test currency conversion integration"""
        # Calculate cost in USD
        response = client.post('/api/v1/calculator/vm', json={
            'provider': 'aws_ec2',
            'instance_type': 't3.small'
        })
        
        usd_cost = response.get_json()['data']['monthly_cost_usd']
        
        # Convert to JPY
        conversion_response = client.post('/api/v1/calculator/currency/convert', json={
            'amount': usd_cost,
            'from_currency': 'USD',
            'to_currency': 'JPY',
            'exchange_rate': 150
        })
        
        conversion_data = conversion_response.get_json()['data']
        expected_jpy = usd_cost * 150
        
        assert abs(conversion_data['converted_amount'] - expected_jpy) < 0.01
```

## End-to-End Testing

### User Workflow Testing
```python
class TestUserWorkflows:
    """Test complete user workflows"""

    def test_cost_comparison_workflow(self, client):
        """Test complete cost comparison user workflow"""
        # User configures Lambda parameters
        lambda_config = {
            'memory_mb': 1024,
            'execution_time_seconds': 30,
            'monthly_executions': 5_000_000,
            'include_free_tier': True
        }
        
        # User selects VM options for comparison
        vm_configs = [
            {'provider': 'aws_ec2', 'instance_type': 't3.medium'},
            {'provider': 'sakura_cloud', 'instance_type': '4core_8gb'}
        ]
        
        # User requests comparison analysis
        response = client.post('/api/v1/calculator/comparison', json={
            'lambda_config': lambda_config,
            'vm_configs': vm_configs,
            'execution_range': {
                'min': 0,
                'max': 10_000_000,
                'steps': 20
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()['data']
        
        # Verify comprehensive comparison data
        assert len(data['comparison_data']) == 20
        assert len(data['break_even_points']) >= 0  # May have break-even points
        
        # Verify user gets actionable insights
        comparison_points = data['comparison_data']
        lambda_costs = [point['lambda_cost_usd'] for point in comparison_points]
        vm_costs_ec2 = [point['vm_costs'].get('aws_ec2_t3_medium', 0) for point in comparison_points]
        
        # Should show cost progression
        assert max(lambda_costs) > min(lambda_costs)  # Lambda costs increase with usage
        assert len(set(vm_costs_ec2)) == 1  # VM costs are constant

    def test_export_functionality_workflow(self, client):
        """Test data export workflow"""
        # User performs calculation
        response = client.post('/api/v1/calculator/comparison', json={
            'lambda_config': {
                'memory_mb': 512,
                'execution_time_seconds': 10,
                'include_free_tier': True
            },
            'vm_configs': [
                {'provider': 'aws_ec2', 'instance_type': 't3.small'}
            ]
        })
        
        data = response.get_json()['data']
        
        # Verify exportable data structure
        assert 'comparison_data' in data
        for point in data['comparison_data']:
            assert 'executions_per_month' in point
            assert 'lambda_cost_usd' in point
            assert 'vm_costs' in point
            
        # Verify data is suitable for CSV export
        assert len(data['comparison_data']) > 0
        assert all(isinstance(point['executions_per_month'], int) for point in data['comparison_data'])
        assert all(isinstance(point['lambda_cost_usd'], (int, float)) for point in data['comparison_data'])
```

### Browser Integration Testing (Future)
```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.e2e
class TestBrowserIntegration:
    """Test browser-based user interactions"""

    @pytest.fixture
    def browser(self):
        """Setup browser for testing"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_form_interaction(self, browser):
        """Test form-based user interaction"""
        browser.get('http://localhost:5000')
        
        # User selects Lambda memory
        memory_select = browser.find_element(By.ID, 'lambdaMemory')
        memory_select.send_keys('1024')
        
        # User sets execution time
        time_select = browser.find_element(By.ID, 'executionTime')
        time_select.send_keys('30')
        
        # User triggers calculation
        form = browser.find_element(By.ID, 'costCalculatorForm')
        form.submit()
        
        # Wait for results
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'costChart'))
        )
        
        # Verify chart is displayed
        chart = browser.find_element(By.ID, 'costChart')
        assert chart.is_displayed()

    def test_chart_interaction(self, browser):
        """Test chart interactivity"""
        browser.get('http://localhost:5000')
        
        # Wait for initial calculation
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'costChart'))
        )
        
        # Test chart hover (requires more advanced Selenium setup)
        chart_canvas = browser.find_element(By.ID, 'costChart')
        
        # Verify chart is interactive
        assert chart_canvas.is_displayed()
        assert chart_canvas.tag_name == 'canvas'
```

## Performance Testing

### Load Testing
```python
import time
import asyncio
import aiohttp

async def test_api_performance():
    """Test API performance under load"""
    async def make_request(session):
        async with session.post('/api/v1/calculator/lambda', json={
            'memory_mb': 512,
            'execution_time_seconds': 10,
            'monthly_executions': 1_000_000,
            'include_free_tier': True
        }) as response:
            return await response.json()
    
    async with aiohttp.ClientSession('http://localhost:5000') as session:
        start_time = time.time()
        
        # Simulate 100 concurrent requests
        tasks = [make_request(session) for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance criteria
        assert duration < 5.0  # Should complete within 5 seconds
        assert all(result['success'] for result in results)
        
        # Verify average response time
        avg_response_time = duration / 100
        assert avg_response_time < 0.1  # Average under 100ms per request
```

### Memory Usage Testing
```python
import psutil
import gc

def test_memory_usage():
    """Test memory usage during calculations"""
    from app.models.lambda_calculator import LambdaCalculator, LambdaConfig
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    calculator = LambdaCalculator()
    
    # Perform many calculations
    for i in range(1000):
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=i * 1000,
            include_free_tier=True
        )
        result = calculator.calculate_total_cost(config)
        
        # Verify no memory leaks
        if i % 100 == 0:
            gc.collect()
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory
            
            # Memory growth should be minimal (< 10MB)
            assert memory_growth < 10 * 1024 * 1024
```

## Test Data Management

### Sample Data Generation
```python
def generate_test_configurations():
    """Generate comprehensive test configurations"""
    memory_sizes = [128, 512, 1024, 2048]
    execution_times = [1, 10, 30, 60]
    execution_volumes = [100_000, 1_000_000, 10_000_000, 100_000_000]
    
    configurations = []
    for memory in memory_sizes:
        for time in execution_times:
            for volume in execution_volumes:
                configurations.append(LambdaConfig(
                    memory_mb=memory,
                    execution_time_seconds=time,
                    monthly_executions=volume,
                    include_free_tier=True
                ))
    
    return configurations

def test_all_configurations():
    """Test calculator with all valid configurations"""
    calculator = LambdaCalculator()
    configurations = generate_test_configurations()
    
    for config in configurations:
        result = calculator.calculate_total_cost(config)
        
        # Basic validation for all configurations
        assert result['total_cost'] >= 0
        assert result['request_charges'] >= 0
        assert result['compute_charges'] >= 0
        assert result['gb_seconds'] > 0
```

## Continuous Integration Testing

### GitHub Actions Integration
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Install mise
      run: curl https://mise.run | sh
    - name: Setup environment
      run: mise install
    - name: Run tests
      run: make test
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Coverage Requirements
- **Overall Coverage**: Minimum 90%
- **Business Logic**: 100% coverage required
- **API Endpoints**: Minimum 80% coverage
- **Frontend**: Manual testing and future automated testing

### Quality Gates
- All tests must pass
- Coverage thresholds must be met
- No linting violations
- Type checking must pass
- Security scan must pass

## Future Testing Enhancements

### Planned Additions
1. **Frontend Testing**: Jest/Cypress for JavaScript testing
2. **Visual Regression**: Screenshot comparison testing
3. **Accessibility Testing**: Automated a11y validation
4. **Security Testing**: OWASP ZAP integration
5. **Database Testing**: When database is added

### Testing Tools Roadmap
- **Jest**: JavaScript unit testing
- **Cypress**: End-to-end browser testing
- **Percy**: Visual regression testing
- **axe-core**: Accessibility testing
- **Lighthouse CI**: Performance testing