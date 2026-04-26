/* ============================================
   UPVEST - Backend API Client
   Communicates with Python FastAPI backend
   ============================================ */

const BackendAPI = {
    // Base URL for the Python backend server (reads from central config)
    BASE_URL: (typeof CONFIG !== 'undefined' && CONFIG.BACKEND_API)
        ? CONFIG.BACKEND_API.BASE_URL
        : 'http://localhost:5000',

    // === Generic HTTP Request ===

    /**
     * Make HTTP request to backend
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Backend API Error:', error);
            throw error;
        }
    },

    // === Server Status ===

    /**
     * Check if backend server is online
     * @returns {Promise<object>} Server status
     */
    async getStatus() {
        try {
            return await this.request('/api/status');
        } catch (error) {
            return {
                status: 'offline',
                error: error.message
            };
        }
    },

    /**
     * Check backend connectivity
     * @returns {Promise<boolean>} True if connected
     */
    async isConnected() {
        const status = await this.getStatus();
        return status.status === 'online';
    },

    // === Portfolio Data ===

    /**
     * Get current portfolio data
     * @returns {Promise<object>} Portfolio data
     */
    async getPortfolio() {
        return await this.request('/api/portfolio');
    },

    // === Trade History ===

    /**
     * Get all trades
     * @param {number} limit - Max number of trades
     * @returns {Promise<Array>} Trade records
     */
    async getTrades(limit = 50) {
        return await this.request(`/api/trades?limit=${limit}`);
    },

    /**
     * Get today's trades
     * @returns {Promise<Array>} Today's trade records
     */
    async getTradesToday() {
        return await this.request('/api/trades/today');
    },

    // === Daily Summaries ===

    /**
     * Get daily P&L summaries
     * @param {number} days - Number of days to fetch
     * @returns {Promise<Array>} Daily summaries
     */
    async getDailySummary(days = 30) {
        return await this.request(`/api/daily-summary?days=${days}`);
    },

    // === Agent Control ===

    /**
     * Get trading agent status
     * @returns {Promise<object>} Agent status
     */
    async getAgentStatus() {
        return await this.request('/api/bot/status');
    },

    /**
     * Start the trading agent
     * @returns {Promise<object>} Start confirmation
     */
    async startAgent() {
        return await this.request('/api/bot/start', {
            method: 'POST'
        });
    },

    /**
     * Stop the trading agent
     * @returns {Promise<object>} Stop confirmation
     */
    async stopAgent() {
        return await this.request('/api/bot/stop', {
            method: 'POST'
        });
    },

    // Backward compatibility aliases
    async getBotStatus() { return this.getAgentStatus(); },
    async startBot() { return this.startAgent(); },
    async stopBot() { return this.stopAgent(); },

    // === AI Predictions ===

    /**
     * Get AI prediction for a stock
     * @param {string} symbol - Stock symbol (e.g., "NSE_EQ|INE467B01029")
     * @param {string} interval - Data interval ("day" or "30minute")
     * @returns {Promise<object>} AI prediction
     */
    async getAIPrediction(symbol, interval = 'day') {
        return await this.request('/api/ai/predict', {
            method: 'POST',
            body: JSON.stringify({ symbol, interval })
        });
    },

    // === Authentication ===

    /**
     * Check Upstox authentication status
     * @returns {Promise<object>} Auth status
     */
    async getAuthStatus() {
        return await this.request('/api/auth/status');
    },

    /**
     * Configure Upstox Auth with user credentials
     * @param {string} apiKey - Upstox API Key
     * @param {string} apiSecret - Upstox API Secret
     * @param {string} redirectUri - Redirect URI (optional)
     * @returns {Promise<object>} Auth URL
     */
    async configureAuth(apiKey, apiSecret, redirectUri) {
        return await this.request('/api/auth/configure', {
            method: 'POST',
            body: JSON.stringify({
                api_key: apiKey,
                api_secret: apiSecret,
                redirect_uri: redirectUri
            })
        });
    },

    // === Utility Functions ===

    /**
     * Format trade for display
     * @param {object} trade - Trade record
     * @returns {object} Formatted trade
     */
    formatTrade(trade) {
        return {
            ...trade,
            formattedPrice: `₹${parseFloat(trade.price).toFixed(2)}`,
            formattedTime: new Date(trade.timestamp).toLocaleString('en-IN'),
            signalClass: trade.signal === 'BUY' ? 'positive' : trade.signal === 'SELL' ? 'negative' : 'neutral',
            confidencePercent: trade.confidence ? `${(trade.confidence * 100).toFixed(0)}%` : 'N/A'
        };
    },

    /**
     * Format P&L for display
     * @param {number} pnl - P&L value
     * @returns {object} Formatted P&L
     */
    formatPnL(pnl) {
        const isPositive = pnl >= 0;
        return {
            value: pnl,
            formatted: `${isPositive ? '+' : ''}₹${pnl.toFixed(2)}`,
            class: isPositive ? 'positive' : 'negative',
            icon: isPositive ? '📈' : '📉'
        };
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackendAPI;
}
