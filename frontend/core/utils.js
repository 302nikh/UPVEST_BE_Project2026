/* ============================================
   UPVEST - Utility Functions
   Helper functions used across the application
   ============================================ */

const Utils = {
    
    // === LocalStorage Helpers ===
    
    /**
     * Save data to localStorage
     * @param {string} key - Storage key
     * @param {any} value - Data to store
     */
    saveToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },
    
    /**
     * Get data from localStorage
     * @param {string} key - Storage key
     * @returns {any} Parsed data or null
     */
    getFromStorage(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    /**
     * Remove item from localStorage
     * @param {string} key - Storage key
     */
    removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },
    
    /**
     * Clear all localStorage data
     */
    clearStorage() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    },
    
    // === Date & Time Helpers ===
    
    /**
     * Format date to readable string
     * @param {Date|string} date - Date to format
     * @param {string} format - Format type: 'short', 'long', 'time'
     * @returns {string} Formatted date
     */
    formatDate(date, format = 'short') {
        const d = new Date(date);
        
        if (format === 'short') {
            return d.toLocaleDateString('en-IN', { 
                day: '2-digit', 
                month: 'short', 
                year: 'numeric' 
            });
        } else if (format === 'long') {
            return d.toLocaleDateString('en-IN', { 
                weekday: 'long',
                day: 'numeric', 
                month: 'long', 
                year: 'numeric' 
            });
        } else if (format === 'time') {
            return d.toLocaleTimeString('en-IN', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } else if (format === 'datetime') {
            return `${this.formatDate(d, 'short')} ${this.formatDate(d, 'time')}`;
        }
        
        return d.toLocaleDateString('en-IN');
    },
    
    /**
     * Get relative time (e.g., "2 hours ago")
     * @param {Date|string} date - Date to compare
     * @returns {string} Relative time string
     */
    getRelativeTime(date) {
        const now = new Date();
        const past = new Date(date);
        const diffMs = now - past;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return this.formatDate(date, 'short');
    },
    
    // === Number Formatting ===
    
    /**
     * Format number to Indian currency
     * @param {number} amount - Amount to format
     * @returns {string} Formatted currency string
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(amount);
    },
    
    /**
     * Format number with commas (Indian system)
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        return new Intl.NumberFormat('en-IN').format(num);
    },
    
    /**
     * Format percentage
     * @param {number} value - Value to format
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted percentage
     */
    formatPercentage(value, decimals = 2) {
        const formatted = value.toFixed(decimals);
        return `${value >= 0 ? '+' : ''}${formatted}%`;
    },
    
    /**
     * Abbreviate large numbers (e.g., 1000 → 1K)
     * @param {number} num - Number to abbreviate
     * @returns {string} Abbreviated number
     */
    abbreviateNumber(num) {
        if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)}Cr`;
        if (num >= 100000) return `₹${(num / 100000).toFixed(2)}L`;
        if (num >= 1000) return `₹${(num / 1000).toFixed(2)}K`;
        return `₹${num}`;
    },
    
    // === Validation Helpers ===
    
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} True if valid
     */
    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    /**
     * Validate phone number (Indian format)
     * @param {string} phone - Phone number to validate
     * @returns {boolean} True if valid
     */
    isValidPhone(phone) {
        const regex = /^[6-9]\d{9}$/;
        return regex.test(phone);
    },
    
    /**
     * Validate password strength
     * @param {string} password - Password to validate
     * @returns {object} Validation result
     */
    validatePassword(password) {
        return {
            isValid: password.length >= 8,
            hasUpperCase: /[A-Z]/.test(password),
            hasLowerCase: /[a-z]/.test(password),
            hasNumber: /\d/.test(password),
            hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
            length: password.length
        };
    },
    
    /**
     * Sanitize input to prevent XSS
     * @param {string} input - Input to sanitize
     * @returns {string} Sanitized input
     */
    sanitizeInput(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    },
    
    // === Financial Calculations ===
    
    /**
     * Calculate compound interest
     * @param {number} principal - Initial amount
     * @param {number} rate - Annual interest rate (%)
     * @param {number} years - Investment period
     * @param {number} frequency - Compounding frequency per year
     * @returns {number} Future value
     */
    calculateCompoundInterest(principal, rate, years, frequency = 12) {
        const r = rate / 100;
        const n = frequency;
        const t = years;
        return principal * Math.pow((1 + r / n), n * t);
    },
    
    /**
     * Calculate SIP returns
     * @param {number} monthlyInvestment - Monthly SIP amount
     * @param {number} rate - Expected annual return (%)
     * @param {number} years - Investment period
     * @returns {object} Investment details
     */
    calculateSIP(monthlyInvestment, rate, years) {
        const r = rate / 100 / 12; // Monthly rate
        const n = years * 12; // Total months
        
        const futureValue = monthlyInvestment * 
            (Math.pow(1 + r, n) - 1) / r * (1 + r);
        
        const totalInvested = monthlyInvestment * n;
        const totalReturns = futureValue - totalInvested;
        
        return {
            futureValue: Math.round(futureValue),
            totalInvested: Math.round(totalInvested),
            totalReturns: Math.round(totalReturns),
            returnPercentage: ((totalReturns / totalInvested) * 100).toFixed(2)
        };
    },
    
    /**
     * Calculate CAGR (Compound Annual Growth Rate)
     * @param {number} initialValue - Starting value
     * @param {number} finalValue - Ending value
     * @param {number} years - Investment period
     * @returns {number} CAGR percentage
     */
    calculateCAGR(initialValue, finalValue, years) {
        return (Math.pow(finalValue / initialValue, 1 / years) - 1) * 100;
    },
    
    // === UI Helpers ===
    
    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - 'success', 'error', 'warning', 'info'
     * @param {number} duration - Display duration in ms
     */
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: ${type === 'success' ? '#28a745' : 
                         type === 'error' ? '#dc3545' : 
                         type === 'warning' ? '#ffc107' : '#17a2b8'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    /**
     * Show loading spinner
     * @param {string} message - Loading message
     * @returns {HTMLElement} Loader element
     */
    showLoader(message = 'Loading...') {
        const loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            z-index: 10000;
        `;
        loader.innerHTML = `
            <div class="spinner" style="
                border: 4px solid rgba(255,255,255,0.3);
                border-top-color: white;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
            "></div>
            <p style="color: white; margin-top: 20px; font-size: 16px;">${message}</p>
        `;
        document.body.appendChild(loader);
        return loader;
    },
    
    /**
     * Hide loading spinner
     */
    hideLoader() {
        const loader = document.getElementById('global-loader');
        if (loader) loader.remove();
    },
    
    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Generate random ID
     * @param {number} length - ID length
     * @returns {string} Random ID
     */
    generateId(length = 10) {
        return Math.random().toString(36).substring(2, length + 2);
    },
    
    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} Success status
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
            return true;
        } catch (error) {
            console.error('Failed to copy:', error);
            return false;
        }
    },
    
    /**
     * Scroll to element smoothly
     * @param {string|HTMLElement} element - Element or selector
     */
    scrollTo(element) {
        const el = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;
        
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
    
    // === Array Helpers ===
    
    /**
     * Shuffle array randomly
     * @param {Array} array - Array to shuffle
     * @returns {Array} Shuffled array
     */
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    },
    
    /**
     * Get unique values from array
     * @param {Array} array - Input array
     * @returns {Array} Unique values
     */
    uniqueArray(array) {
        return [...new Set(array)];
    }
};

// Add CSS animation for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}