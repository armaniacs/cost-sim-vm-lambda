/**
 * Modern API client for the Cost Simulator
 * Provides standardized HTTP requests and error handling
 */

class APIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Make a standardized HTTP request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Object>} API response
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new APIError(data.error?.message || 'Request failed', response.status, data.error);
            }

            return data;
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError('Network error or invalid response', 0, { originalError: error.message });
        }
    }

    /**
     * Calculate Lambda costs
     * @param {Object} config - Lambda configuration
     * @returns {Promise<Object>} Calculation result
     */
    async calculateLambdaCost(config) {
        return this.request('/calculator/lambda', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    /**
     * Calculate VM costs
     * @param {Object} config - VM configuration
     * @returns {Promise<Object>} Calculation result
     */
    async calculateVMCost(config) {
        return this.request('/calculator/vm', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    /**
     * Calculate serverless costs
     * @param {Object} config - Serverless configuration
     * @returns {Promise<Object>} Calculation result
     */
    async calculateServerlessCost(config) {
        return this.request('/calculator/serverless', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    /**
     * Get cost comparison
     * @param {Object} lambdaConfig - Lambda configuration
     * @param {Object} vmConfig - VM configuration
     * @returns {Promise<Object>} Comparison result
     */
    async getComparison(lambdaConfig, vmConfig) {
        return this.request('/calculator/comparison', {
            method: 'POST',
            body: JSON.stringify({ lambda: lambdaConfig, vm: vmConfig })
        });
    }

    /**
     * Export data to CSV
     * @param {Object} data - Data to export
     * @returns {Promise<Blob>} CSV blob
     */
    async exportCSV(data) {
        const response = await fetch(`${this.baseURL}/calculator/export-csv`, {
            method: 'POST',
            headers: this.defaultHeaders,
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new APIError(errorData.error?.message || 'Export failed', response.status);
        }

        return response.blob();
    }
}

/**
 * Custom error class for API errors
 */
class APIError extends Error {
    constructor(message, status = 0, errorData = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.errorData = errorData;
    }

    /**
     * Get user-friendly error message
     * @returns {string} Formatted error message
     */
    getUserMessage() {
        if (this.status === 400 && this.errorData?.code === 'VALIDATION_ERROR') {
            const fieldErrors = this.errorData.details?.field_errors;
            if (fieldErrors) {
                const errorList = Object.entries(fieldErrors)
                    .map(([field, error]) => `${field}: ${error}`)
                    .join(', ');
                return `Validation errors: ${errorList}`;
            }
        }
        
        return this.message;
    }

    /**
     * Check if error is recoverable
     * @returns {boolean} True if user can retry
     */
    isRecoverable() {
        return this.status >= 400 && this.status < 500 && this.status !== 404;
    }
}

// Global API client instance
const apiClient = new APIClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError, apiClient };
}