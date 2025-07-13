/* Global JavaScript utilities for Cost Simulator */

/* Additional utility functions that complement the main index.html JavaScript */

// Utility function to format numbers with locale
function formatNumber(number, locale = 'en-US') {
    return new Intl.NumberFormat(locale).format(number);
}

// Utility function to format currency
function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Debounce function for input handling
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

// Validation utilities
const validators = {
    isPositiveNumber: (value) => {
        const num = parseFloat(value);
        return !isNaN(num) && num > 0;
    },
    
    isInteger: (value) => {
        const num = parseInt(value);
        return !isNaN(num) && Number.isInteger(num);
    },
    
    isInRange: (value, min, max) => {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    }
};

// Local storage utilities for saving user preferences
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
            console.warn('Failed to load from localStorage:', e);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn('Failed to remove from localStorage:', e);
        }
    }
};

// Configuration presets
const presets = {
    'low_usage': {
        lambdaMemory: '128',
        executionTime: '1',
        executionFrequency: '100000',
        description: 'Low Usage (100K executions/month)'
    },
    'medium_usage': {
        lambdaMemory: '512',
        executionTime: '10',
        executionFrequency: '1000000',
        description: 'Medium Usage (1M executions/month)'
    },
    'high_usage': {
        lambdaMemory: '1024',
        executionTime: '30',
        executionFrequency: '10000000',
        description: 'High Usage (10M executions/month)'
    }
};

// Apply preset configuration
function applyPreset(presetName) {
    const preset = presets[presetName];
    if (!preset) return;
    
    document.getElementById('lambdaMemory').value = preset.lambdaMemory;
    document.getElementById('executionTime').value = preset.executionTime;
    document.getElementById('executionFrequency').value = preset.executionFrequency;
    
    // Trigger calculation after applying preset
    if (typeof calculateCosts === 'function') {
        calculateCosts();
    }
}

// Exchange rate fetching utility (mock implementation)
async function fetchExchangeRate() {
    // In a real implementation, this would fetch from an API
    // For now, return a reasonable default rate
    return 150.0;
}

// Chart theme utilities
const chartThemes = {
    light: {
        backgroundColor: '#ffffff',
        gridColor: '#e0e0e0',
        textColor: '#333333'
    },
    dark: {
        backgroundColor: '#2d3748',
        gridColor: '#4a5568',
        textColor: '#ffffff'
    }
};

// Apply chart theme
function applyChartTheme(chart, theme = 'light') {
    if (!chart || !chartThemes[theme]) return;
    
    const themeConfig = chartThemes[theme];
    
    chart.options.plugins = chart.options.plugins || {};
    chart.options.plugins.legend = chart.options.plugins.legend || {};
    chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
    chart.options.plugins.legend.labels.color = themeConfig.textColor;
    
    chart.options.scales = chart.options.scales || {};
    chart.options.scales.x = chart.options.scales.x || {};
    chart.options.scales.y = chart.options.scales.y || {};
    
    chart.options.scales.x.grid = chart.options.scales.x.grid || {};
    chart.options.scales.x.grid.color = themeConfig.gridColor;
    chart.options.scales.x.ticks = chart.options.scales.x.ticks || {};
    chart.options.scales.x.ticks.color = themeConfig.textColor;
    
    chart.options.scales.y.grid = chart.options.scales.y.grid || {};
    chart.options.scales.y.grid.color = themeConfig.gridColor;
    chart.options.scales.y.ticks = chart.options.scales.y.ticks || {};
    chart.options.scales.y.ticks.color = themeConfig.textColor;
    
    chart.update();
}

// Analytics tracking (placeholder)
const analytics = {
    trackCalculation: (config) => {
        console.log('Calculation performed:', config);
        // In production, this would send to analytics service
    },
    
    trackExport: (format) => {
        console.log('Data exported:', format);
        // In production, this would send to analytics service
    },
    
    trackError: (error) => {
        console.error('Error tracked:', error);
        // In production, this would send to error reporting service
    }
};

// Initialize utilities when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load saved user preferences
    const savedExchangeRate = storage.load('exchangeRate');
    if (savedExchangeRate && document.getElementById('exchangeRate')) {
        document.getElementById('exchangeRate').value = savedExchangeRate;
    }
    
    const savedCurrency = storage.load('displayCurrency');
    if (savedCurrency !== null && document.getElementById('displayCurrency')) {
        document.getElementById('displayCurrency').checked = savedCurrency;
    }
    
    // Add event listeners for saving preferences
    const exchangeRateInput = document.getElementById('exchangeRate');
    if (exchangeRateInput) {
        exchangeRateInput.addEventListener('change', debounce((e) => {
            storage.save('exchangeRate', e.target.value);
        }, 500));
    }
    
    const currencyToggle = document.getElementById('displayCurrency');
    if (currencyToggle) {
        currencyToggle.addEventListener('change', (e) => {
            storage.save('displayCurrency', e.target.checked);
        });
    }
});

// Export utilities for global use
window.CostSimulatorUtils = {
    formatNumber,
    formatCurrency,
    debounce,
    validators,
    storage,
    presets,
    applyPreset,
    fetchExchangeRate,
    applyChartTheme,
    analytics
};