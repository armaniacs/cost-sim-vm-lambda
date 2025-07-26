# UI Requirements and Frontend Architecture Reference

## Table of Contents
1. [Frontend Technology Stack](#frontend-technology-stack)
2. [UI Component Architecture](#ui-component-architecture)
3. [Internationalization System](#internationalization-system)
4. [Chart Visualization Requirements](#chart-visualization-requirements)
5. [Form Input Validation](#form-input-validation)
6. [Responsive Design](#responsive-design)
7. [Frontend-Backend API Integration](#frontend-backend-api-integration)
8. [User Experience Requirements](#user-experience-requirements)
9. [Frontend Testing Approach](#frontend-testing-approach)
10. [Build and Deployment Process](#build-and-deployment-process)

## Frontend Technology Stack

### Core Technologies
- **HTML5**: Semantic markup with modern web standards
- **CSS3**: Custom styles with Bootstrap 5.3.0 framework
- **Vanilla JavaScript**: ES6+ syntax, no additional frameworks
- **Bootstrap 5.3.0**: Responsive UI framework for layout and components
- **Chart.js 4.4.0**: Interactive data visualization library
- **Bootstrap Icons**: Comprehensive icon library

### External Dependencies
```html
<!-- Bootstrap CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>

<!-- Bootstrap JS Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

### File Structure
```
app/static/
├── css/
│   └── style.css           # Custom CSS overrides and styles
├── js/
│   └── app.js              # Utility functions and helpers
├── i18n/
│   ├── en/
│   │   └── common.json     # English translations
│   └── ja/
│       └── common.json     # Japanese translations
└── images/                 # Static image assets

app/templates/
├── base.html              # Base template with navigation
└── index.html             # Main application interface
```

## UI Component Architecture

### Base Template Structure
The application uses a template inheritance pattern with `base.html` providing the core layout:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <!-- Meta tags, CSS, and JavaScript includes -->
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <!-- Navigation with language switcher -->
    </nav>
    
    <main class="container-fluid py-4">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Scripts -->
</body>
</html>
```

### Main Layout Components

#### 1. Configuration Panel (Left Column)
```html
<div class="col-lg-4">
    <div class="card shadow-sm">
        <div class="card-header bg-primary text-white">
            <h5>Configuration</h5>
        </div>
        <div class="card-body">
            <!-- Form inputs and controls -->
        </div>
    </div>
</div>
```

**Features:**
- Lambda configuration (memory, execution time, frequency)
- Serverless provider selection
- Egress and transfer settings
- Currency and exchange rate controls
- Quick calculate button

#### 2. Results Panel (Right Column)
```html
<div class="col-lg-8">
    <!-- Quick Results Card -->
    <div class="card mb-4">
        <div class="card-header">
            <h5>Quick Results</h5>
        </div>
        <div class="card-body">
            <!-- Summary metrics -->
        </div>
    </div>
    
    <!-- Chart Visualization -->
    <div class="card mb-4">
        <div class="card-body">
            <canvas id="costChart"></canvas>
        </div>
    </div>
    
    <!-- Detailed Data Table -->
    <div class="card">
        <div class="card-body">
            <!-- Data table with export functionality -->
        </div>
    </div>
</div>
```

### Input Components Design Patterns

#### Preset-Custom Input Pattern
Used for Lambda memory, execution time, and frequency:

```html
<div class="input-group">
    <select id="lambdaMemoryPreset" class="form-select">
        <option value="128">128 MB</option>
        <option value="512" selected>512 MB</option>
        <option value="1024">1024 MB</option>
        <option value="custom">Custom</option>
    </select>
    <input type="number" id="lambdaMemoryCustom" class="form-control" 
           placeholder="Enter MB" min="128" max="10240" step="1" value="512">
    <span class="input-group-text">MB</span>
</div>
```

#### Provider Selection Pattern
Multi-provider checkbox selection with "Select All" functionality:

```html
<div class="mb-3">
    <div class="d-flex justify-content-between mb-2">
        <button type="button" class="btn btn-outline-primary btn-sm" onclick="selectAllProviders()">
            Select All
        </button>
        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="deselectAllProviders()">
            Deselect All
        </button>
    </div>
    <div class="form-check-group">
        <!-- Provider checkboxes -->
    </div>
</div>
```

### CSS Design System

#### Color Palette
```css
:root {
    --bs-primary: #0056b3;
    --bs-success: #28a745;
    --bs-warning: #ffc107;
    --bs-info: #17a2b8;
    --bs-danger: #dc3545;
}
```

#### Component Styling
```css
/* Card styling with hover effects */
.card {
    border: none;
    border-radius: 10px;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

/* Form controls with focus states */
.form-select, .form-control {
    border-radius: 8px;
    border: 1px solid #ced4da;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-select:focus, .form-control:focus {
    border-color: #0056b3;
    box-shadow: 0 0 0 0.2rem rgba(0, 86, 179, 0.25);
}
```

## Internationalization System

### Structure and Implementation
The i18n system supports English and Japanese with complete UI translation coverage.

#### Translation File Structure
```json
{
  "app": {
    "title": "AWS Lambda vs VM Cost Simulator"
  },
  "ui": {
    "buttons": {
      "calculate": "Calculate",
      "reset": "Reset",
      "export_csv": "Export CSV"
    }
  },
  "lambda": {
    "section_title": "AWS Lambda Configuration",
    "memory_size": "Memory Size",
    "placeholders": {
      "memory_mb": "Enter MB"
    }
  }
}
```

#### Language Switching Implementation
```javascript
// Language detection and switching
function detectLanguage() {
    const savedLang = localStorage.getItem('preferred-language');
    const browserLang = navigator.language.startsWith('ja') ? 'ja' : 'en';
    return savedLang || browserLang;
}

async function loadTranslations(lang) {
    try {
        const response = await fetch(`/static/i18n/${lang}/common.json`);
        const translations = await response.json();
        return translations;
    } catch (error) {
        console.error('Failed to load translations:', error);
        return null;
    }
}

function updateUI(translations) {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = getNestedValue(translations, key);
        if (translation) {
            element.textContent = translation;
        }
    });
}
```

#### Translation Key Patterns
- **Hierarchical structure**: `section.subsection.key`
- **UI elements**: `ui.buttons.calculate`
- **Form labels**: `lambda.memory_size`
- **Validation messages**: `validation.memory_range`
- **Placeholders**: Use `data-i18n-placeholder` attribute

## Chart Visualization Requirements

### Chart.js Integration
The application uses Chart.js 4.4.0 for interactive cost comparison visualization.

#### Chart Configuration
```javascript
const chartConfig = {
    type: 'line',
    data: {
        labels: [], // Execution frequency values
        datasets: [
            {
                label: 'AWS Lambda',
                data: [],
                borderColor: '#ff6384',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.4
            },
            {
                label: 'AWS EC2',
                data: [],
                borderColor: '#36a2eb',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.4
            }
            // Additional provider datasets
        ]
    },
    options: {
        responsive: true,
        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            title: {
                display: true,
                text: 'Cost Comparison Chart'
            },
            legend: {
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                    }
                }
            }
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Monthly Executions'
                },
                type: 'logarithmic'
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Monthly Cost'
                }
            }
        }
    }
};
```

#### Chart Data Management
```javascript
function updateChart(calculations) {
    const chart = Chart.getChart('costChart');
    if (!chart) return;
    
    // Update datasets with new calculation results
    chart.data.labels = calculations.map(calc => calc.executions);
    chart.data.datasets.forEach((dataset, index) => {
        const providerKey = getProviderKey(index);
        dataset.data = calculations.map(calc => calc.costs[providerKey]);
    });
    
    chart.update('active');
}
```

#### Responsive Chart Behavior
- **Desktop**: Full-width chart with detailed tooltips
- **Tablet**: Optimized legend placement
- **Mobile**: Simplified chart with essential data points only

## Form Input Validation

### Validation Framework
The application implements comprehensive client-side validation with real-time feedback.

#### Validation Rules
```javascript
const validationRules = {
    lambdaMemory: {
        min: 128,
        max: 10240,
        step: 1,
        required: true,
        message: 'Memory size must be between 128 and 10,240 MB'
    },
    executionTime: {
        min: 0.1,
        max: 900,
        step: 0.1,
        required: true,
        message: 'Execution time must be between 0.1 and 900 seconds'
    },
    executionFrequency: {
        min: 1,
        max: 1000000000,
        step: 1,
        required: true,
        message: 'Execution frequency must be between 1 and 1,000,000,000 per month'
    },
    egressTransfer: {
        min: 0,
        max: 1000000,
        step: 0.1,
        required: false,
        message: 'Transfer amount must be 0 or positive'
    },
    transferRatio: {
        min: 0,
        max: 100,
        step: 1,
        required: false,
        message: 'Transfer ratio must be between 0-100%'
    },
    exchangeRate: {
        min: 100,
        max: 300,
        step: 0.01,
        required: true,
        message: 'Exchange rate must be between 100-300'
    }
};
```

#### Real-time Validation Implementation
```javascript
function validateInput(element) {
    const fieldName = element.id;
    const value = parseFloat(element.value);
    const rules = validationRules[fieldName];
    
    if (!rules) return true;
    
    let isValid = true;
    let errorMessage = '';
    
    if (rules.required && (!element.value || isNaN(value))) {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (value < rules.min || value > rules.max) {
        isValid = false;
        errorMessage = rules.message;
    }
    
    // Update UI feedback
    const errorElement = document.getElementById(`${fieldName}Error`);
    if (errorElement) {
        errorElement.style.display = isValid ? 'none' : 'block';
        errorElement.textContent = errorMessage;
    }
    
    element.classList.toggle('is-invalid', !isValid);
    element.classList.toggle('is-valid', isValid && element.value);
    
    return isValid;
}

// Debounced validation for better UX
function addValidationListeners() {
    Object.keys(validationRules).forEach(fieldName => {
        const element = document.getElementById(fieldName);
        if (element) {
            element.addEventListener('input', debounce((e) => {
                validateInput(e.target);
            }, 300));
        }
    });
}
```

### User Interaction Flows

#### Primary User Journey
1. **Landing**: User sees default configuration
2. **Configuration**: User adjusts Lambda parameters
3. **Provider Selection**: User selects cloud providers to compare
4. **Calculation**: User clicks "Calculate" button
5. **Results**: User reviews chart and table data
6. **Export**: User exports results to CSV (optional)

#### Secondary Flows
- **Language Switching**: Toggle between English/Japanese
- **Preset Application**: Quick configuration using presets
- **Custom Input**: Switch from presets to custom values
- **Currency Toggle**: Switch between USD and JPY display

## Responsive Design

### Breakpoint Strategy
```css
/* Mobile First Approach */
/* xs: <576px */
/* sm: ≥576px */
/* md: ≥768px */
/* lg: ≥992px */
/* xl: ≥1200px */
/* xxl: ≥1400px */
```

### Layout Adaptations

#### Desktop (≥992px)
- **Two-column layout**: Configuration panel (33%) + Results panel (67%)
- **Full chart visibility**: Complete Chart.js visualization
- **Detailed table**: All columns visible
- **Hover interactions**: Enhanced tooltips and feedback

#### Tablet (768px - 991px)
- **Stacked layout**: Configuration above results
- **Simplified chart**: Reduced legend, optimized for touch
- **Scrollable table**: Horizontal scroll for detailed data
- **Touch-friendly controls**: Larger buttons and inputs

#### Mobile (<768px)
- **Single column**: Full-width components
- **Collapsible sections**: Accordion-style configuration
- **Essential chart**: Simplified view with key providers only
- **Swipe interactions**: Touch-optimized navigation

### Mobile-Specific Features
```css
@media (max-width: 767px) {
    .navbar-brand {
        font-size: 1rem;
    }
    
    .card {
        margin-bottom: 1rem;
    }
    
    .input-group {
        flex-direction: column;
    }
    
    .input-group .form-select,
    .input-group .form-control {
        border-radius: 8px !important;
        margin-bottom: 0.5rem;
    }
    
    .btn-group {
        flex-direction: column;
    }
    
    .table-responsive {
        font-size: 0.875rem;
    }
}
```

## Frontend-Backend API Integration

### API Communication Pattern
The frontend uses RESTful API calls with JSON data exchange.

#### API Endpoint Structure
```javascript
const API_BASE = '/api/v1';
const endpoints = {
    calculate: `${API_BASE}/calculator`,
    serverlessProviders: `${API_BASE}/serverless-providers`,
    exchangeRate: `${API_BASE}/exchange-rate`
};
```

#### Request/Response Handling
```javascript
async function calculateCosts() {
    showLoadingState();
    
    try {
        const requestData = gatherFormData();
        
        const response = await fetch(endpoints.calculate, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        updateResults(data);
        
    } catch (error) {
        handleError(error);
    } finally {
        hideLoadingState();
    }
}
```

#### Error Handling Strategy
```javascript
function handleError(error) {
    console.error('API Error:', error);
    
    let userMessage = 'An unexpected error occurred. Please try again.';
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        userMessage = 'Failed to connect to server. Please check your network connection.';
    } else if (error.status === 400) {
        userMessage = 'Please check your input values.';
    } else if (error.status >= 500) {
        userMessage = 'Server error occurred. Please try again later.';
    }
    
    showErrorMessage(userMessage);
    analytics.trackError(error);
}
```

### Data Flow Architecture

#### Request Data Structure
```javascript
const requestPayload = {
    lambda: {
        memory_mb: 512,
        execution_time_seconds: 1.0,
        executions_per_month: 2592000
    },
    serverless_provider: 'aws',
    egress: {
        transfer_per_request_kb: 10,
        internet_transfer_ratio_percent: 50
    },
    vm_providers: ['aws_ec2', 'sakura_cloud', 'google_cloud'],
    currency: {
        exchange_rate_jpy_usd: 150.0,
        display_in_jpy: false
    }
};
```

#### Response Data Structure
```javascript
const responseData = {
    calculations: [
        {
            executions_per_month: 1000000,
            costs: {
                aws_lambda: 45.50,
                aws_ec2: 70.20,
                sakura_cloud: 65.80
            }
        }
    ],
    breakeven_analysis: {
        aws_ec2: {
            executions: 1500000,
            monthly_cost: 55.75
        }
    },
    recommendations: {
        optimal_provider: 'aws_lambda',
        cost_savings: 24.70
    }
};
```

## User Experience Requirements

### Performance Requirements
- **Initial Load**: Page must load within 2 seconds
- **Calculation Response**: Results displayed within 1 second
- **Chart Rendering**: Interactive chart ready within 500ms
- **Language Switch**: UI translation completed within 200ms

### Accessibility Standards
Following WCAG 2.1 AA guidelines:

#### Keyboard Navigation
```html
<!-- Tab order optimization -->
<form id="costCalculatorForm" tabindex="0">
    <input type="number" id="lambdaMemory" tabindex="1" aria-describedby="lambdaMemoryHelp">
    <div id="lambdaMemoryHelp" class="form-text">Lambda memory allocation</div>
</form>
```

#### Screen Reader Support
```html
<!-- ARIA labels and descriptions -->
<button onclick="calculateCosts()" aria-describedby="calculateHelp">
    Calculate
</button>
<div id="calculateHelp" class="sr-only">
    Calculate cost comparison for current configuration
</div>
```

#### Color Accessibility
- **Contrast ratios**: Minimum 4.5:1 for normal text
- **Chart colors**: Colorblind-friendly palette
- **Error states**: Icons + color + text for validation

### Loading States and Feedback
```javascript
function showLoadingState() {
    const button = document.querySelector('#calculateButton');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Calculating...';
    
    document.querySelector('#results').classList.add('opacity-50');
}

function hideLoadingState() {
    const button = document.querySelector('#calculateButton');
    button.disabled = false;
    button.innerHTML = '<i class="bi bi-calculator me-2"></i>Calculate';
    
    document.querySelector('#results').classList.remove('opacity-50');
}
```

### User Preferences Persistence
```javascript
const preferences = {
    save: (key, value) => {
        localStorage.setItem(`costsim_${key}`, JSON.stringify(value));
    },
    
    load: (key, defaultValue) => {
        const stored = localStorage.getItem(`costsim_${key}`);
        return stored ? JSON.parse(stored) : defaultValue;
    },
    
    // Saved preferences
    savedSettings: [
        'language',
        'exchangeRate',
        'displayCurrency',
        'selectedProviders',
        'lastConfiguration'
    ]
};
```

## Frontend Testing Approach

### Testing Strategy
Following the project's TDD approach with frontend-specific testing patterns.

#### Unit Testing for JavaScript Functions
```javascript
// Using Jest-style testing (conceptual)
describe('Cost Calculator Utils', () => {
    test('formatCurrency should format USD correctly', () => {
        expect(formatCurrency(123.45, 'USD')).toBe('$123.45');
    });
    
    test('validateInput should reject invalid memory values', () => {
        const element = { id: 'lambdaMemory', value: '50' };
        expect(validateInput(element)).toBe(false);
    });
    
    test('debounce should delay function execution', (done) => {
        let called = false;
        const fn = debounce(() => { called = true; }, 100);
        
        fn();
        expect(called).toBe(false);
        
        setTimeout(() => {
            expect(called).toBe(true);
            done();
        }, 150);
    });
});
```

#### Integration Testing with Backend
```python
# Python integration tests for API endpoints
def test_frontend_api_integration():
    """Test that frontend receives expected data structure"""
    response = client.post('/api/v1/calculator', json={
        'lambda': {'memory_mb': 512, 'execution_time_seconds': 1.0}
    })
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify frontend-expected structure
    assert 'calculations' in data
    assert 'breakeven_analysis' in data
    assert isinstance(data['calculations'], list)
```

#### Visual Regression Testing
```javascript
// Playwright-style visual testing (conceptual)
test('chart rendering matches baseline', async ({ page }) => {
    await page.goto('/');
    await page.fill('#lambdaMemory', '512');
    await page.click('#calculateButton');
    await page.waitForSelector('#costChart');
    
    await expect(page.locator('#costChart')).toHaveScreenshot('cost-chart.png');
});
```

### Manual Testing Checklist

#### Cross-Browser Compatibility
- [ ] Chrome (latest 2 versions)
- [ ] Firefox (latest 2 versions)
- [ ] Safari (latest 2 versions)
- [ ] Edge (latest 2 versions)

#### Device Testing
- [ ] Desktop (1920x1080, 1366x768)
- [ ] Tablet (768x1024, 1024x768)
- [ ] Mobile (375x667, 414x896)

#### Functionality Testing
- [ ] Form validation (all input types)
- [ ] Chart interaction (zoom, hover, legend)
- [ ] Language switching (complete UI translation)
- [ ] CSV export (data accuracy)
- [ ] Error handling (network issues, invalid responses)

## Build and Deployment Process

### Development Workflow
```bash
# Development server with hot reload
make dev

# Asset optimization for development
make lint    # CSS and JS linting
make format  # Code formatting
```

### Production Build Process

#### Asset Optimization
The application uses Flask's static file serving with cache busting:

```python
# In Flask app
@app.context_processor
def inject_timestamp():
    return {'timestamp': int(time.time())}
```

```html
<!-- Cache-busted static files -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}?v={{ timestamp }}">
<script src="{{ url_for('static', filename='js/app.js') }}?v={{ timestamp }}"></script>
```

#### Docker Integration
```dockerfile
# Frontend assets copied to container
COPY app/static /app/static
COPY app/templates /app/templates

# Production optimizations
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
```

### Performance Optimization

#### CSS Optimization
```css
/* Critical CSS inlined in head */
/* Non-critical CSS loaded asynchronously */

/* Optimized asset loading */
.chart-container {
    min-height: 400px; /* Prevent layout shift */
}

/* Efficient animations */
.transition-all {
    transition: all 0.15s ease-in-out;
}
```

#### JavaScript Performance
```javascript
// Lazy loading for non-critical features
const loadChartModule = async () => {
    if (!window.Chart) {
        await import('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js');
    }
    return window.Chart;
};

// Efficient DOM queries
const elements = {
    form: document.getElementById('costCalculatorForm'),
    chart: document.getElementById('costChart'),
    results: document.getElementById('results')
};

// Debounced resize handler
window.addEventListener('resize', debounce(() => {
    if (window.costChart) {
        window.costChart.resize();
    }
}, 250));
```

### CDN and Caching Strategy

#### Static Asset Caching
```nginx
# Nginx configuration for static assets
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
    
    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json;
}
```

#### API Response Caching
```javascript
// Frontend cache for API responses
const apiCache = new Map();

async function cachedApiCall(endpoint, data, ttl = 300000) { // 5 minutes
    const cacheKey = `${endpoint}_${JSON.stringify(data)}`;
    const cached = apiCache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < ttl) {
        return cached.data;
    }
    
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    apiCache.set(cacheKey, { data: result, timestamp: Date.now() });
    
    return result;
}
```

## Summary

This comprehensive UI requirements and frontend architecture document provides:

1. **Complete technology stack** with specific versions and integration patterns
2. **Detailed component architecture** following Bootstrap and modern CSS practices  
3. **Robust internationalization system** supporting English and Japanese
4. **Advanced Chart.js integration** with responsive and interactive visualizations
5. **Comprehensive form validation** with real-time feedback and error handling
6. **Mobile-first responsive design** with touch-optimized interactions
7. **Efficient API integration patterns** with error handling and caching
8. **Accessibility-focused UX** following WCAG 2.1 AA standards
9. **Testing methodology** covering unit, integration, and visual regression testing
10. **Production-ready build process** with optimization and caching strategies

The frontend architecture supports the project's goal of providing a comprehensive, user-friendly cost comparison tool while maintaining high performance, accessibility, and maintainability standards.