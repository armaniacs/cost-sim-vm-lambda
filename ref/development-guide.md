# Development Guide

## Getting Started

### Prerequisites
- **Python 3.11+**: Required for type hints and modern Python features
- **Node.js 20+**: For npm dependencies and frontend tooling
- **mise**: Modern development tool manager for unified environment
- **Git**: Version control with pre-commit hooks

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cost-sim-vm-lambda
   ```

2. **Install mise** (if not already installed):
   ```bash
   curl https://mise.run | sh
   exec "$SHELL"
   ```

3. **Install all dependencies**:
   ```bash
   make setup
   ```

4. **Verify installation**:
   ```bash
   make test
   ```

5. **Start development server**:
   ```bash
   make dev
   ```

The application will be available at `http://localhost:5000`.

## Development Workflow

### Daily Development Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `make setup` | - | Complete environment setup |
| `make test` | `make t` | Run tests with coverage |
| `make lint` | `make l` | Run all linting checks |
| `make format` | `make f` | Format code automatically |
| `make dev` | `make d` | Start development server |
| `make clean` | `make c` | Clean generated files |

### Test-Driven Development Process

This project follows **t_wada style TDD**:

#### 1. Red Phase: Write Failing Test
```python
def test_new_feature(self):
    """Test description of what should work"""
    # Arrange
    config = create_test_configuration()
    
    # Act
    result = function_under_test(config)
    
    # Assert
    assert result.is_valid()
    assert result.value == expected_value
```

#### 2. Green Phase: Minimum Implementation
```python
def function_under_test(config):
    """Minimum code to make test pass"""
    return MockResult(is_valid=True, value=expected_value)
```

#### 3. Refactor Phase: Improve Implementation
```python
def function_under_test(config):
    """Proper implementation with all edge cases"""
    validator = ConfigValidator()
    if not validator.is_valid(config):
        raise ValueError("Invalid configuration")
    
    calculator = Calculator(config)
    return calculator.compute_result()
```

### Code Quality Standards

#### Formatting (Black)
- **Line Length**: 88 characters maximum
- **String Quotes**: Double quotes preferred
- **Trailing Commas**: Required in multi-line structures

Example:
```python
# Good
function_call(
    parameter_one="value",
    parameter_two="another_value",
)

# Bad
function_call(parameter_one='value', parameter_two='another_value')
```

#### Import Organization (isort)
```python
# Standard library imports
import os
import sys
from typing import Dict, List

# Third-party imports
from flask import Flask, request
import pytest

# Local application imports
from app.models.calculator import Calculator
from app.config import Config
```

#### Type Hints (mypy)
```python
def calculate_cost(
    memory_mb: int, 
    execution_time: int, 
    monthly_executions: int
) -> Dict[str, float]:
    """Calculate cost with proper type annotations"""
    return {
        "request_charges": 0.0,
        "compute_charges": 0.0,
        "total_cost": 0.0,
    }
```

#### Linting (flake8)
- **Max Line Length**: 88 characters
- **Ignored Rules**: E203 (whitespace before ':'), W503 (line break before binary operator)
- **Docstring Requirements**: All public functions must have docstrings

### Git Workflow

#### Pre-commit Hooks
Automatically run on each commit:
```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8
```

#### Commit Message Format
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes
- refactor: code refactoring
- test: adding or updating tests
- chore: maintenance tasks
```

Examples:
```
feat(calculator): add Sakura Cloud pricing support
fix(api): handle missing parameters gracefully
docs(readme): update setup instructions
test(lambda): add edge case for zero executions
```

## Project Structure

### Application Architecture
```
app/
├── __init__.py              # Package initialization
├── main.py                  # Flask application factory
├── config.py                # Environment configurations
├── models/                  # Business logic layer
│   ├── __init__.py
│   ├── lambda_calculator.py # Lambda cost calculations
│   └── vm_calculator.py     # VM cost calculations
├── api/                     # REST API layer
│   ├── __init__.py
│   └── calculator_api.py    # API endpoints
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template
│   └── index.html          # Main application page
└── static/                 # Static assets
    ├── css/
    │   └── style.css       # Custom styles
    └── js/
        └── app.js          # JavaScript utilities
```

### Test Structure
```
tests/
├── conftest.py             # Pytest configuration and fixtures
├── unit/                   # Unit tests
│   ├── test_app_creation.py
│   ├── test_lambda_calculator.py
│   └── test_vm_calculator.py
├── integration/            # Integration tests (future)
└── e2e/                   # End-to-end tests (future)
```

### Configuration Structure
```
config/
├── development.py          # Development settings
├── testing.py             # Test environment settings
├── production.py          # Production settings
└── __init__.py            # Configuration factory
```

## Testing Strategy

### Unit Testing
**Target**: 100% coverage for business logic

Example test structure:
```python
class TestLambdaCalculator:
    """Test AWS Lambda cost calculation logic"""

    def test_request_charges_with_free_tier(self):
        """Test request charges include free tier deduction"""
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,  # Exceeds free tier
            include_free_tier=True
        )
        calculator = LambdaCalculator()
        
        charges = calculator.calculate_request_charges(config)
        
        # Should charge for 1M executions after free tier
        expected = 1_000_000 * 0.20 / 1_000_000  # $0.20
        assert charges == expected

    def test_request_charges_without_free_tier(self):
        """Test request charges without free tier deduction"""
        # Similar test structure...
```

### Integration Testing
**Target**: API endpoints and data flow

```python
def test_lambda_cost_api_endpoint(client):
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
```

### Test Data Management
```python
# conftest.py
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
```

## Environment Management

### mise Configuration
```toml
# .mise.toml
[tools]
python = "3.11.8"
node = "20.11.0"

[tasks.install]
run = "pip install -r requirements.txt && npm install"

[tasks.test]
run = "pytest tests/ --cov=app --cov-report=term-missing"

[tasks.lint]
run = ["black --check app/ tests/", "isort --check-only app/ tests/", 
      "flake8 app/ tests/", "mypy app/"]

[tasks.dev]
run = "python -m flask --app app.main run --debug --host 0.0.0.0 --port 5000"
```

### Environment Variables
```bash
# Development
export FLASK_ENV=development
export FLASK_DEBUG=1

# Testing
export FLASK_ENV=testing
export TESTING=True

# Production
export FLASK_ENV=production
export FLASK_DEBUG=0
```

### Virtual Environment (Alternative)
If not using mise:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

## Debugging and Development Tools

### Flask Development Server
```bash
# Run with debug mode
make dev

# Custom host/port
python -m flask --app app.main run --host 0.0.0.0 --port 8000 --debug
```

### Interactive Debugging
```python
# Use breakpoint() for debugging
def calculate_total_cost(config):
    breakpoint()  # Python 3.7+ built-in debugger
    result = perform_calculation(config)
    return result

# Or use pdb
import pdb; pdb.set_trace()
```

### Log Configuration
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

## Performance Optimization

### Backend Performance
```python
# Cache expensive calculations
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_ec2_monthly_cost(instance_type: str) -> float:
    """Cache EC2 cost calculations"""
    return EC2_PRICING[instance_type]["hourly_usd"] * 730
```

### Frontend Performance
```javascript
// Debounce user input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Use for form input handlers
const debouncedCalculate = debounce(calculateCosts, 500);
```

### Database Optimization (Future)
```python
# When adding database support
class CostCalculationCache:
    """Cache calculation results in database"""
    
    def get_cached_result(self, config_hash: str):
        """Retrieve cached calculation"""
        return db.session.query(CalculationResult).filter_by(
            config_hash=config_hash
        ).first()
    
    def cache_result(self, config_hash: str, result: dict):
        """Store calculation result"""
        cached_result = CalculationResult(
            config_hash=config_hash,
            result_data=json.dumps(result),
            created_at=datetime.utcnow()
        )
        db.session.add(cached_result)
        db.session.commit()
```

## Troubleshooting Common Issues

### Installation Problems
```bash
# mise not found
curl https://mise.run | sh
exec "$SHELL"

# Python version issues
mise install python@3.11.8
mise use python@3.11.8

# Permission errors
sudo chown -R $(whoami) ~/.local/share/mise
```

### Test Failures
```bash
# Run specific test
pytest tests/unit/test_lambda_calculator.py::test_specific_function -v

# Run with detailed output
pytest -v -s

# Run with debugger on failure
pytest --pdb
```

### Linting Issues
```bash
# Auto-fix formatting
make format

# Check specific files
black --check app/models/lambda_calculator.py
flake8 app/models/lambda_calculator.py
mypy app/models/lambda_calculator.py
```

### Development Server Issues
```bash
# Check port availability
lsof -i :5000

# Kill existing process
kill -9 $(lsof -t -i:5000)

# Run on different port
python -m flask --app app.main run --port 8000
```

## Contributing Guidelines

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass: `make test`
4. Ensure code quality: `make lint`
5. Update documentation if needed
6. Submit pull request with description

### Code Review Checklist
- [ ] Tests cover new functionality
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes without migration plan
- [ ] Performance impact considered
- [ ] Security implications reviewed

### Release Process
1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Create release tag
4. Deploy to production environment
5. Monitor for issues