/**
 * Lightweight Internationalization (i18n) Library for Vanilla JavaScript
 * Supports English and Japanese language switching
 */

class SimpleI18n {
    constructor() {
        this.currentLanguage = this.detectLanguage();
        this.translations = {};
        this.fallbackLanguage = 'en';
        this.onLanguageChangeCallbacks = [];
    }

    /**
     * Detect user's preferred language
     * Priority: localStorage > browser language > fallback
     */
    detectLanguage() {
        // Check localStorage first
        const saved = localStorage.getItem('preferred_language');
        if (saved && ['en', 'ja'].includes(saved)) {
            return saved;
        }

        // Check browser language
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang.startsWith('ja')) {
            return 'ja';
        }

        return 'en'; // Default fallback
    }

    /**
     * Load translations for a specific language
     */
    async loadLanguage(lang) {
        if (this.translations[lang]) {
            return this.translations[lang];
        }

        try {
            const response = await fetch(`/static/i18n/${lang}/common.json`);
            if (!response.ok) {
                throw new Error(`Failed to load ${lang} translations`);
            }
            
            const translations = await response.json();
            this.translations[lang] = translations;
            return translations;
        } catch (error) {
            console.error(`Error loading ${lang} translations:`, error);
            
            // If not fallback language, try to load fallback
            if (lang !== this.fallbackLanguage) {
                console.log(`Falling back to ${this.fallbackLanguage}`);
                return await this.loadLanguage(this.fallbackLanguage);
            }
            
            return {};
        }
    }

    /**
     * Initialize i18n system
     */
    async init() {
        console.log('🌐 Initializing i18n system...');
        
        // Load current language
        await this.loadLanguage(this.currentLanguage);
        
        // Load fallback language if different
        if (this.currentLanguage !== this.fallbackLanguage) {
            await this.loadLanguage(this.fallbackLanguage);
        }
        
        console.log(`🌐 i18n initialized with language: ${this.currentLanguage}`);
        
        // Apply translations to the page
        this.translatePage();
        
        // Set up language switcher
        this.setupLanguageSwitcher();
    }

    /**
     * Get translation for a key using dot notation
     * @param {string} key - Translation key (e.g., 'lambda.memory_size')
     * @param {object} params - Parameters for interpolation
     * @returns {string} - Translated text
     */
    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLanguage];
        
        // Navigate through the translation object
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                // Try fallback language
                value = this.translations[this.fallbackLanguage];
                for (const fallbackKey of keys) {
                    if (value && typeof value === 'object' && fallbackKey in value) {
                        value = value[fallbackKey];
                    } else {
                        console.warn(`Translation key not found: ${key}`);
                        return key; // Return key as fallback
                    }
                }
                break;
            }
        }
        
        if (typeof value !== 'string') {
            console.warn(`Translation key "${key}" did not resolve to a string`);
            return key;
        }
        
        // Simple parameter interpolation
        return this.interpolate(value, params);
    }

    /**
     * Simple parameter interpolation
     */
    interpolate(text, params) {
        return text.replace(/\\{\\{(\\w+)\\}\\}/g, (match, key) => {
            return key in params ? params[key] : match;
        });
    }

    /**
     * Change language
     */
    async changeLanguage(newLang) {
        if (newLang === this.currentLanguage) {
            return;
        }

        console.log(`🌐 Changing language to: ${newLang}`);
        
        // Load new language if not already loaded
        await this.loadLanguage(newLang);
        
        const oldLang = this.currentLanguage;
        this.currentLanguage = newLang;
        
        // Save to localStorage
        localStorage.setItem('preferred_language', newLang);
        
        // Update page title
        document.title = this.t('app.title');
        
        // Retranslate the page
        this.translatePage();
        
        // Update chart if it exists
        if (window.costChart) {
            this.updateChartLanguage();
        }
        
        // Update currency formatting
        this.updateCurrencyFormat();
        
        // Notify callbacks
        this.onLanguageChangeCallbacks.forEach(callback => {
            try {
                callback(newLang, oldLang);
            } catch (error) {
                console.error('Error in language change callback:', error);
            }
        });
        
        console.log(`🌐 Language changed to: ${newLang}`);
    }

    /**
     * Add callback for language change events
     */
    onLanguageChange(callback) {
        this.onLanguageChangeCallbacks.push(callback);
    }

    /**
     * Translate all elements with data-i18n attribute
     */
    translatePage() {
        console.log('🌐 Translating page elements...');
        
        // Translate elements with data-i18n attribute
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName.toLowerCase() === 'input' && element.type === 'text') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Translate elements with data-i18n-placeholder attribute
        const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
        placeholderElements.forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // Translate elements with data-i18n-title attribute
        const titleElements = document.querySelectorAll('[data-i18n-title]');
        titleElements.forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
        
        console.log(`🌐 Translated ${elements.length + placeholderElements.length + titleElements.length} elements`);
    }

    /**
     * Update Chart.js language
     */
    updateChartLanguage() {
        if (!window.costChart) return;
        
        console.log('🌐 Updating chart language...');
        
        // Update chart title
        if (window.costChart.options.plugins.title) {
            window.costChart.options.plugins.title.text = this.t('chart.title');
        }
        
        // Update axis labels
        if (window.costChart.options.scales.x && window.costChart.options.scales.x.title) {
            window.costChart.options.scales.x.title.text = this.t('chart.x_axis');
        }
        
        if (window.costChart.options.scales.y && window.costChart.options.scales.y.title) {
            // Preserve currency symbol if already set
            const currentYTitle = window.costChart.options.scales.y.title.text;
            const currencyMatch = currentYTitle.match(/\(([¥$])\)$/);
            const currencySymbol = currencyMatch ? currencyMatch[1] : '$';
            window.costChart.options.scales.y.title.text = `${this.t('chart.y_axis')} (${currencySymbol})`;
        }
        
        // Update dataset labels with current instance types if available
        if (window.costChart.data.datasets.length >= 6) {
            // Try to get current form data to preserve instance types
            const getFormData = window.getFormData;
            if (getFormData) {
                try {
                    const formData = getFormData();
                    
                    window.costChart.data.datasets[0].label = this.t('chart.legend.aws_lambda');
                    window.costChart.data.datasets[1].label = `${this.t('chart.legend.aws_ec2')} (${formData.ec2InstanceType || 't3.small'})`;
                    window.costChart.data.datasets[2].label = `${this.t('chart.legend.sakura_cloud')} (${formData.sakuraInstanceType || '2core/4GB'})`;
                    window.costChart.data.datasets[3].label = `${this.t('chart.legend.google_cloud')} (${formData.gcpInstanceType || 'e2-micro'})`;
                    window.costChart.data.datasets[4].label = `${this.t('chart.legend.azure')} (${formData.azureInstanceType || 'B2ms'})`;
                    window.costChart.data.datasets[5].label = `${this.t('chart.legend.oci')} (${formData.ociInstanceType || 'VM.Standard.E2.1.Micro'})`;
                } catch (error) {
                    console.warn('Could not get form data for chart labels, using defaults');
                    // Fallback to basic labels
                    window.costChart.data.datasets[0].label = this.t('chart.legend.aws_lambda');
                    window.costChart.data.datasets[1].label = this.t('chart.legend.aws_ec2');
                    window.costChart.data.datasets[2].label = this.t('chart.legend.sakura_cloud');
                    window.costChart.data.datasets[3].label = this.t('chart.legend.google_cloud');
                    window.costChart.data.datasets[4].label = this.t('chart.legend.azure');
                    window.costChart.data.datasets[5].label = this.t('chart.legend.oci');
                }
            }
        }
        
        // Update chart
        window.costChart.update();
        
        console.log('🌐 Chart language updated');
    }

    /**
     * Update currency formatting based on language
     */
    updateCurrencyFormat() {
        // This will be used by other parts of the application
        window.currentLocale = this.currentLanguage === 'ja' ? 'ja-JP' : 'en-US';
        window.currentCurrency = this.currentLanguage === 'ja' ? 'JPY' : 'USD';
        
        console.log(`🌐 Currency format updated: ${window.currentCurrency} (${window.currentLocale})`);
    }

    /**
     * Setup language switcher UI
     */
    setupLanguageSwitcher() {
        // Find or create language switcher container
        let switcherContainer = document.getElementById('languageSwitcher');
        
        if (!switcherContainer) {
            // Create language switcher in header
            switcherContainer = document.createElement('div');
            switcherContainer.id = 'languageSwitcher';
            switcherContainer.className = 'language-switcher';
            
            // Insert in navbar or header
            const navbar = document.querySelector('.navbar') || document.querySelector('header') || document.body;
            navbar.appendChild(switcherContainer);
        }
        
        // Create language switcher HTML
        switcherContainer.innerHTML = `
            <div class="btn-group btn-group-sm">
                <button type="button" class="btn btn-outline-light ${this.currentLanguage === 'en' ? 'active' : ''}" 
                        data-lang="en" data-i18n="app.language_switcher.english">English</button>
                <button type="button" class="btn btn-outline-light ${this.currentLanguage === 'ja' ? 'active' : ''}" 
                        data-lang="ja" data-i18n="app.language_switcher.japanese">日本語</button>
            </div>
        `;
        
        // Add event listeners
        const buttons = switcherContainer.querySelectorAll('[data-lang]');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const lang = e.target.getAttribute('data-lang');
                this.changeLanguage(lang);
                
                // Update active state
                buttons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        console.log('🌐 Language switcher setup complete');
    }

    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Format number based on current locale
     */
    formatNumber(number, options = {}) {
        const locale = this.currentLanguage === 'ja' ? 'ja-JP' : 'en-US';
        return new Intl.NumberFormat(locale, options).format(number);
    }

    /**
     * Format currency based on current locale
     */
    formatCurrency(amount, currency = null) {
        const locale = this.currentLanguage === 'ja' ? 'ja-JP' : 'en-US';
        const currencyCode = currency || (this.currentLanguage === 'ja' ? 'JPY' : 'USD');
        
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currencyCode,
            maximumFractionDigits: 0
        }).format(amount);
    }

    /**
     * Format date based on current locale
     */
    formatDate(date, options = {}) {
        const locale = this.currentLanguage === 'ja' ? 'ja-JP' : 'en-US';
        return new Intl.DateTimeFormat(locale, options).format(date);
    }
}

// Create global i18n instance
window.i18n = new SimpleI18n();

// Expose translation function globally for convenience
window.t = (key, params) => window.i18n.t(key, params);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.i18n.init();
});

console.log('🌐 i18n.js loaded successfully');