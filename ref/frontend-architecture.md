# Frontend Architecture

## Technology Stack

### Core Technologies
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **JavaScript ES6+**: Modern JavaScript features and APIs
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive data visualization
- **Font Awesome**: Icon library for consistent iconography

### Build Tools and Dependencies
- **CDN Resources**: Bootstrap and Chart.js served from CDN
- **No Build Process**: Direct HTML/CSS/JS for simplicity
- **Progressive Enhancement**: Works without JavaScript

## Architecture Patterns

### Progressive Enhancement
The application follows a progressive enhancement approach:

1. **Base Layer**: HTML forms that work without JavaScript
2. **Enhanced Layer**: JavaScript adds interactivity and real-time updates
3. **Advanced Layer**: Chart visualizations and advanced UI features

### Component-Based Structure
```
app/static/
├── css/
│   └── style.css           # Custom component styles
├── js/
│   └── app.js             # Utility functions and enhancements
└── templates/
    ├── base.html          # Layout component
    └── index.html         # Main application component
```

### State Management
- **Local State**: JavaScript variables for current calculations
- **Persistent State**: localStorage for user preferences
- **Remote State**: API calls for cost calculations

## Template Architecture

### Base Template (base.html)
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <!-- Meta tags and title -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- External CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <!-- Navigation content -->
    </nav>
    
    <!-- Main content area -->
    <main class="container-fluid py-4">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-light mt-5 py-3">
        <!-- Footer content -->
    </footer>
    
    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Features:**
- Responsive meta viewport
- Japanese language declaration
- Bootstrap 5 integration
- Custom CSS and JavaScript injection points
- Structured content blocks

### Main Template (index.html)
```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <!-- Configuration Panel -->
    <div class="col-lg-4">
        {{ configuration_forms() }}
        {{ quick_results_panel() }}
    </div>
    
    <!-- Results Panel -->
    <div class="col-lg-8">
        {{ chart_visualization() }}
        {{ data_table() }}
        {{ breakeven_analysis() }}
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Embedded JavaScript for main application logic
</script>
{% endblock %}
```

**Architecture Benefits:**
- Clear separation of concerns
- Responsive grid layout
- Component-like organization
- Script isolation in blocks

## CSS Architecture

### Methodology
- **Custom Properties**: CSS variables for theming
- **BEM-like Naming**: Component-based class naming
- **Bootstrap Override**: Careful customization of Bootstrap defaults
- **Responsive Design**: Mobile-first approach

### CSS Structure
```css
/* CSS Custom Properties */
:root {
    --bs-primary: #0056b3;
    --bs-success: #28a745;
    --bs-warning: #ffc107;
    --bs-info: #17a2b8;
}

/* Global Styles */
body {
    background-color: #f8f9fa;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Component Styles */
.card {
    border: none;
    border-radius: 10px;
    transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

/* Responsive Utilities */
@media (max-width: 768px) {
    .card-body {
        padding: 1rem;
    }
}
```

### Component Organization
- **Base Styles**: Typography, colors, spacing
- **Layout Components**: Cards, forms, navigation
- **Interactive Elements**: Buttons, forms, hover states
- **Responsive Breakpoints**: Mobile, tablet, desktop variations

## JavaScript Architecture

### Module Pattern
```javascript
// Global namespace for utilities
window.CostSimulatorUtils = {
    formatNumber,
    formatCurrency,
    debounce,
    validators,
    storage,
    presets,
    analytics
};

// Main application logic in index.html
document.addEventListener('DOMContentLoaded', function() {
    initializeCostChart();
    setupEventListeners();
    loadUserPreferences();
    calculateCosts(); // Initial calculation
});
```

### Utility Functions
```javascript
// Number formatting
function formatNumber(number, locale = 'en-US') {
    return new Intl.NumberFormat(locale).format(number);
}

// Currency formatting
function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Debounced input handling
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
```

### Event Management
```javascript
// Centralized event listener setup
function setupEventListeners() {
    document.getElementById('costCalculatorForm')
        .addEventListener('submit', calculateCosts);
    
    document.getElementById('exportCSV')
        .addEventListener('click', exportToCSV);
    
    // Debounced form changes
    const debouncedCalculate = debounce(calculateCosts, 500);
    document.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('change', debouncedCalculate);
    });
}
```

### State Management
```javascript
// Application state
let costChart = null;
let comparisonData = [];
let currentConfiguration = {};

// Persistent storage
const storage = {
    save: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.warn('Failed to save to localStorage:', e);
        }
    },
    
    load: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            return defaultValue;
        }
    }
};
```

## Chart Integration

### Chart.js Configuration
```javascript
function initializeCostChart() {
    const ctx = document.getElementById('costChart').getContext('2d');
    
    costChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'AWS Lambda',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.1
                },
                {
                    label: 'AWS EC2 (t3.small)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'logarithmic',
                    title: {
                        display: true,
                        text: 'Monthly Executions'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Monthly Cost (USD)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}
```

### Chart Update Logic
```javascript
function updateChart(data) {
    const labels = data.comparison_data.map(d => d.executions_per_month);
    const lambdaData = data.comparison_data.map(d => d.lambda_cost_usd);
    const ec2Data = data.comparison_data.map(d => d.vm_costs.aws_ec2_t3_small || 0);
    
    costChart.data.labels = labels;
    costChart.data.datasets[0].data = lambdaData;
    costChart.data.datasets[1].data = ec2Data;
    
    costChart.update();
}
```

## API Integration

### Fetch-based API Calls
```javascript
async function calculateCosts(event) {
    if (event) event.preventDefault();
    
    // Show loading state
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    loadingModal.show();
    
    try {
        const formData = getFormData();
        
        const response = await fetch('/api/v1/calculator/comparison', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lambda_config: {
                    memory_mb: parseInt(formData.lambdaMemory),
                    execution_time_seconds: parseInt(formData.executionTime),
                    include_free_tier: formData.includeFreeTier
                },
                vm_configs: [
                    { provider: 'aws_ec2', instance_type: 't3.small' },
                    { provider: 'sakura_cloud', instance_type: '2core_4gb' }
                ],
                execution_range: {
                    min: 0,
                    max: 10000000,
                    steps: 50
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            comparisonData = result.data.comparison_data;
            updateChart(result.data);
            updateQuickResults(formData);
            updateDataTable(result.data);
            updateBreakEvenAnalysis(result.data.break_even_points);
        } else {
            showError(result.error || 'Calculation failed');
        }
        
    } catch (error) {
        console.error('Calculation error:', error);
        showError('Failed to calculate costs. Please try again.');
    } finally {
        loadingModal.hide();
    }
}
```

### Error Handling
```javascript
function showError(message) {
    const errorTemplate = document.getElementById('errorTemplate');
    const errorClone = errorTemplate.cloneNode(true);
    errorClone.id = '';
    errorClone.classList.remove('d-none');
    errorClone.querySelector('#errorMessage').textContent = message;
    
    document.querySelector('main').insertBefore(
        errorClone, 
        document.querySelector('main').firstChild
    );
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorClone.remove();
    }, 5000);
}
```

## Data Export Functionality

### CSV Export Implementation
```javascript
function exportToCSV() {
    if (comparisonData.length === 0) {
        showError('No data to export. Please calculate first.');
        return;
    }
    
    let csv = 'Executions per Month,Lambda Cost (USD),EC2 Cost (USD),Sakura Cost (USD)\\n';
    
    comparisonData.forEach(row => {
        csv += `${row.executions_per_month},${row.lambda_cost_usd.toFixed(2)},${(row.vm_costs.aws_ec2_t3_small || 0).toFixed(2)},${(row.vm_costs.sakura_cloud_2core_4gb || 0).toFixed(2)}\\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cost_comparison_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}
```

## Performance Optimization

### Frontend Performance
- **Debounced Input**: Form changes trigger calculations after 500ms delay
- **Efficient DOM Updates**: Minimal reflow and repaint operations
- **Lazy Loading**: Chart.js loaded only when needed
- **Local Caching**: User preferences stored in localStorage

### Memory Management
```javascript
// Clean up chart resources
function destroyChart() {
    if (costChart) {
        costChart.destroy();
        costChart = null;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', destroyChart);
```

### Bundle Size Optimization
- **CDN Usage**: External libraries served from CDN
- **No Build Tools**: Direct file serving for simplicity
- **Minimal Custom JS**: Core functionality only
- **Tree Shaking**: Only necessary Chart.js components

## Accessibility Features

### Keyboard Navigation
```javascript
// Ensure all interactive elements are keyboard accessible
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && event.target.matches('button, [role="button"]')) {
        event.target.click();
    }
});
```

### Screen Reader Support
```html
<!-- ARIA labels and descriptions -->
<div id="costChart" 
     role="img" 
     aria-label="Cost comparison chart showing Lambda vs VM costs"
     aria-describedby="chart-description">
</div>

<div id="chart-description" class="sr-only">
    Interactive line chart comparing AWS Lambda costs with VM costs 
    across different execution volumes.
</div>
```

### Form Accessibility
```html
<label for="lambdaMemory" class="form-label">Memory Size</label>
<select id="lambdaMemory" 
        class="form-select" 
        required
        aria-describedby="memory-help">
    <option value="128">128 MB</option>
    <option value="512" selected>512 MB</option>
</select>
<div id="memory-help" class="form-text">
    Select the Lambda memory allocation size.
</div>
```

## Browser Compatibility

### Feature Detection
```javascript
// Check for required features
function checkBrowserSupport() {
    const hasLocalStorage = typeof(Storage) !== "undefined";
    const hasFetch = typeof(fetch) !== "undefined";
    const hasPromises = typeof(Promise) !== "undefined";
    
    if (!hasLocalStorage) {
        console.warn('localStorage not supported, preferences will not persist');
    }
    
    if (!hasFetch) {
        console.error('Fetch API not supported');
        // Fallback to XMLHttpRequest
    }
    
    return hasPromises && (hasFetch || typeof(XMLHttpRequest) !== "undefined");
}
```

### Polyfills and Fallbacks
```javascript
// Fetch polyfill for older browsers
if (!window.fetch) {
    // Load fetch polyfill or implement XMLHttpRequest fallback
}

// Chart.js fallback
if (!window.Chart) {
    console.error('Chart.js failed to load');
    // Show data table only
    document.getElementById('costChart').style.display = 'none';
}
```

## Testing Strategy

### Frontend Testing
```javascript
// Unit tests for utility functions
describe('CostSimulatorUtils', () => {
    test('formatNumber should format numbers correctly', () => {
        expect(formatNumber(1234.56)).toBe('1,234.56');
    });
    
    test('debounce should delay function execution', (done) => {
        let called = false;
        const debouncedFn = debounce(() => { called = true; }, 100);
        
        debouncedFn();
        expect(called).toBe(false);
        
        setTimeout(() => {
            expect(called).toBe(true);
            done();
        }, 150);
    });
});
```

### Integration Testing
```javascript
// Test API integration
describe('API Integration', () => {
    test('should calculate costs successfully', async () => {
        const response = await fetch('/api/v1/calculator/lambda', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                memory_mb: 512,
                execution_time_seconds: 10,
                monthly_executions: 1000000,
                include_free_tier: true
            })
        });
        
        const result = await response.json();
        expect(result.success).toBe(true);
        expect(result.data.total_cost).toBeGreaterThan(0);
    });
});
```