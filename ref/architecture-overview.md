# Architecture Overview

## Project Structure

The AWS Lambda vs VM Cost Simulator follows a modular Flask architecture with clear separation of concerns:

```
cost-sim-vm-lambda/
├── app/                          # Main application package
│   ├── api/                      # REST API endpoints
│   ├── models/                   # Business logic and calculators
│   ├── static/                   # Frontend assets (CSS, JS, images)
│   ├── templates/                # Jinja2 HTML templates
│   └── pricing_config/           # Static pricing data files
├── tests/                        # Comprehensive test suite
│   ├── unit/                     # Unit tests for models
│   ├── integration/              # API integration tests
│   └── e2e/                      # End-to-end BDD tests
├── Design/                       # Project specifications and PBI documentation
├── ref/                          # Reference documentation
└── docs/                         # Development guides
```

## Core Components

### Application Layer (`app/`)

#### Main Application (`main.py`)
- **Flask Application Factory**: Creates and configures Flask app instances
- **Blueprint Registration**: Registers API blueprints with URL prefixes
- **Route Handlers**: Serves frontend and provides health endpoints
- **CORS Configuration**: Enables cross-origin requests for frontend integration

#### Configuration (`config.py`)
- **Environment-based Configuration**: Development, testing, production configs
- **Configuration Management**: Centralized settings for host, port, debug mode

#### API Layer (`api/calculator_api.py`)
- **REST API Endpoints**: 7 main endpoints for cost calculations
- **Request Validation**: Input validation and error handling
- **Response Formatting**: Consistent JSON response structure
- **Multi-provider Support**: Handles AWS Lambda, EC2, Google Cloud, Azure, OCI, Sakura Cloud

### Business Logic Layer (`models/`)

#### Lambda Calculator (`lambda_calculator.py`)
- **AWS Lambda Pricing**: Request charges, compute charges, egress fees
- **Free Tier Handling**: 1M requests/month + 400,000 GB-seconds/month
- **Memory Scaling**: 128MB to 2048MB memory configurations
- **Internet Transfer Ratio**: Configurable egress percentage (PBI10)

#### VM Calculator (`vm_calculator.py`) 
- **Multi-Cloud Support**: 6 cloud providers with detailed pricing
  - AWS EC2: t3.micro to c5.xlarge instances
  - Google Cloud: e2-micro to c2-standard-4 instances  
  - Azure: B1ls to D4 instances (including Always Free options)
  - Oracle Cloud: E2.1.Micro to E4.Flex (including Always Free)
  - Sakura Cloud: 1core/1GB to 6core/12GB configurations
- **Instance Recommendations**: Lambda-equivalent VM suggestions
- **Currency Conversion**: USD/JPY exchange rate handling

#### Egress Calculator (`egress_calculator.py`)
- **Transfer Cost Calculation**: Internet egress fees by provider
- **Free Tier Integration**: 100GB/month free allowances
- **Flexible Rate Configuration**: Custom egress rates support
- **Multi-currency Support**: USD for cloud providers, JPY for Sakura

### Frontend Layer

#### Templates (`templates/`)
- **Base Template (`base.html`)**: Shared layout with Bootstrap 5
- **Main Interface (`index.html`)**: Interactive cost comparison form
- **Responsive Design**: Mobile-friendly responsive layout
- **Chart.js Integration**: Real-time cost visualization

#### Static Assets (`static/`)
- **JavaScript (`js/app.js`)**: Frontend application logic
  - API communication with fetch()
  - Chart.js graph rendering
  - Form validation and interaction
  - CSV export functionality
- **CSS (`css/style.css`)**: Custom styling and responsive design
- **Images (`images/`)**: Static image assets

### Testing Architecture (`tests/`)

#### Test Hierarchy
1. **Unit Tests**: Individual component testing (38 tests)
   - `test_lambda_calculator.py`: Lambda pricing logic
   - `test_vm_calculator.py`: VM pricing and recommendations
   - `test_egress_calculator.py`: Egress cost calculations
   - `test_app_creation.py`: Flask app initialization

2. **Integration Tests**: API endpoint testing (32 tests)
   - `test_egress_api.py`: Complete API integration with egress
   - `test_google_cloud_api.py`: Google Cloud provider integration

3. **E2E Tests**: Complete user workflow testing (13 tests)
   - `test_egress_feature.py`: Egress cost calculation workflows
   - `test_internet_transfer_ratio_feature.py`: Transfer ratio features

#### Test Configuration
- **pytest.ini**: Test runner configuration
- **conftest.py**: Shared test fixtures and Flask test client
- **Coverage Reporting**: 88% code coverage with HTML reports

## Data Flow Architecture

### Request Processing Flow
1. **Frontend Form Submission** → JavaScript validation
2. **API Request** → Flask route handler
3. **Input Validation** → Parameter checking and sanitization
4. **Business Logic** → Calculator models process pricing
5. **Response Formatting** → JSON structure with results
6. **Frontend Rendering** → Chart.js visualization + table display

### Cost Calculation Pipeline
1. **Configuration Parsing** → Extract user parameters
2. **Lambda Cost Calculation** → Request + compute + egress fees
3. **VM Cost Calculation** → Instance costs + egress fees for each provider
4. **Break-even Analysis** → Find intersection points
5. **Currency Conversion** → USD/JPY conversion if requested
6. **Data Aggregation** → Combine results for comparison

## Technology Stack

### Backend
- **Flask 2.3+**: Web framework with application factory pattern
- **Python 3.11**: Modern Python with type hints
- **JSON**: Data exchange format for API communication

### Frontend  
- **Bootstrap 5**: Responsive CSS framework
- **Chart.js 3.9+**: Interactive chart visualization
- **Vanilla JavaScript**: No framework dependencies
- **Jinja2**: Server-side templating

### Development Tools
- **pytest**: Testing framework with coverage
- **Black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking
- **mise**: Python environment management

### Deployment
- **Docker**: Containerization with multi-stage builds
- **Makefile**: Standardized development commands
- **Requirements.txt**: Python dependency management

## Design Patterns

### Application Factory Pattern
- Clean separation of app creation and configuration
- Support for multiple environments (dev, test, prod)
- Easy testing with different configurations

### Calculator Pattern
- Each calculator handles specific pricing logic
- Consistent interface across different providers
- Extensible for adding new cloud providers

### Repository Pattern
- Static pricing data in JSON configuration files
- Centralized pricing management
- Easy updating of pricing information

### Builder Pattern
- Configuration objects for complex calculations
- Type-safe parameter handling
- Clear API for different calculation scenarios

## Security Considerations

### Input Validation
- Parameter type checking and range validation
- SQL injection prevention (no database queries)
- XSS prevention through template escaping

### API Security
- CORS configuration for controlled frontend access
- Input sanitization for all API endpoints
- Error handling without information disclosure

### Deployment Security
- Multi-stage Docker builds for minimal attack surface
- No sensitive data in configuration files
- Environment-based configuration management