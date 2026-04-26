/* ============================================
   UPVEST - Configuration File
   Central configuration for the entire app
   ============================================
*/

const CONFIG = {
    // === App Information ===
    APP_NAME: 'UPVEST',
    APP_VERSION: '1.0.0',
    APP_DESCRIPTION: 'AI-Powered Investment Platform',

    // === API Keys ===
    // IMPORTANT: Replace these with your actual API keys
    // === API Keys ===
    API_KEYS: {
        // Gemini AI API Key
        GEMINI_API_KEY: 'GEMINI_KEY_REMOVED',

        // Upstox API Credentials
        UPSTOX: {
            API_KEY: 'UPSTOX_KEY_REMOVED',
            API_SECRET: 'UPSTOX_SECRET_REMOVED',
            REDIRECT_URI: 'https://www.unofficed.com/', // Change in production
            CLIENT_ID: '9658986525'
        }
    },

    // === API Endpoints ===
    API_ENDPOINTS: {
        // Gemini AI
        GEMINI_BASE_URL: 'https://generativelanguage.googleapis.com/v1beta',
        GEMINI_GENERATE: '/models/gemini-2.0-flash:generateContent',

        // Upstox API
        UPSTOX_BASE_URL: 'https://api-v2.upstox.com',
        UPSTOX_LOGIN: '/login/authorization/dialog',
        UPSTOX_TOKEN: '/login/authorization/token',
        UPSTOX_PROFILE: '/user/profile',
        UPSTOX_FUNDS: '/user/get-funds-and-margin',
        UPSTOX_POSITIONS: '/portfolio/short-term-positions',
        UPSTOX_ORDERS: '/order/retrieve-all',
        UPSTOX_MARKET_QUOTE: '/market-quote/quotes',

        // Market Data (Yahoo Finance Alternative API)
        // Using corsproxy.io to bypass CORS restrictions in browser
        MARKET_DATA_URL: 'https://corsproxy.io/?https://query1.finance.yahoo.com/v8/finance/chart/',

        // Backup: Alpha Vantage (Free tier: 5 calls/min, 500 calls/day)
        ALPHA_VANTAGE_URL: 'https://www.alphavantage.co/query',
        ALPHA_VANTAGE_KEY: 'demo' // Replace with your key
    },

    // === Backend API (Python FastAPI Server) ===
    BACKEND_API: {
        BASE_URL: 'http://localhost:5000',
        ENDPOINTS: {
            STATUS: '/api/status',
            PORTFOLIO: '/api/portfolio',
            TRADES: '/api/trades',
            TRADES_TODAY: '/api/trades/today',
            DAILY_SUMMARY: '/api/daily-summary',
            BOT_STATUS: '/api/bot/status',
            BOT_START: '/api/bot/start',
            BOT_STOP: '/api/bot/stop',
            AI_PREDICT: '/api/ai/predict',
            AUTH_STATUS: '/api/auth/status'
        }
    },

    // === Stock Symbols ===
    STOCKS: {
        INDIAN_INDICES: {
            NIFTY50: 'NIFTY 50',
            SENSEX: 'SENSEX',
            BANKNIFTY: 'BANK NIFTY'
        },
        POPULAR_STOCKS: [
            { symbol: 'RELIANCE.NS', name: 'Reliance Industries' },
            { symbol: 'TCS.NS', name: 'Tata Consultancy Services' },
            { symbol: 'INFY.NS', name: 'Infosys' },
            { symbol: 'HDFCBANK.NS', name: 'HDFC Bank' },
            { symbol: 'ICICIBANK.NS', name: 'ICICI Bank' },
            { symbol: 'SBIN.NS', name: 'State Bank of India' },
            { symbol: 'BHARTIARTL.NS', name: 'Bharti Airtel' },
            { symbol: 'ITC.NS', name: 'ITC Limited' },
            { symbol: 'KOTAKBANK.NS', name: 'Kotak Mahindra Bank' },
            { symbol: 'LT.NS', name: 'Larsen & Toubro' }
        ]
    },

    // === Investment Plans ===
    PLANS: {
        SAFE: {
            name: 'Safe Plan',
            risk: 'Low',
            returns: '5-8%',
            allocation: {
                ppf: 30,
                fixedDeposit: 25,
                liquidFunds: 20,
                goldBonds: 15,
                largeCap: 10
            }
        },
        BALANCED: {
            name: 'Balanced Plan',
            risk: 'Medium',
            returns: '10-15%',
            allocation: {
                largeCap: 30,
                midCap: 20,
                debt: 25,
                gold: 10,
                ppf: 15
            }
        },
        GROWTH: {
            name: 'Growth Plan',
            risk: 'High',
            returns: '15-25%',
            allocation: {
                largeCap: 35,
                midCap: 30,
                smallCap: 20,
                debt: 10,
                gold: 5
            }
        }
    },

    // === App Settings ===
    SETTINGS: {
        // Market data refresh interval (milliseconds)
        MARKET_REFRESH_INTERVAL: 30000, // 30 seconds

        // Chart update interval
        CHART_UPDATE_INTERVAL: 5000, // 5 seconds

        // Session timeout (milliseconds)
        SESSION_TIMEOUT: 3600000, // 1 hour

        // LocalStorage keys
        STORAGE_KEYS: {
            USER: 'upvest_user',
            AUTH_TOKEN: 'upvest_auth_token',
            FINANCIAL_PROFILE: 'upvest_financial_profile',
            INVESTMENT_PLAN: 'upvest_investment_plan',
            DEMAT_CONNECTION: 'upvest_demat_connection',
            QUIZ_SCORES: 'upvest_quiz_scores',
            BOT_TRANSACTIONS: 'upvest_bot_transactions',
            PREFERENCES: 'upvest_preferences'
        },

        // Pagination
        ITEMS_PER_PAGE: 10,

        // File upload limits
        MAX_FILE_SIZE: 5242880, // 5MB in bytes

        // Chatbot settings
        CHATBOT_MAX_MESSAGES: 50,
        CHATBOT_RESPONSE_DELAY: 1000 // 1 second
    },

    // === YouTube Video IDs for Learning Section ===
    LEARNING_VIDEOS: {
        BASICS: {
            id: 'p7HKvqRI_Bo', // Stock Market Basics
            title: 'Stock Market for Beginners',
            duration: '15:30'
        },
        TECHNICAL_ANALYSIS: {
            id: 'H6CM3l0WmvE', // Technical Analysis
            title: 'Technical Analysis Tutorial',
            duration: '20:45'
        },
        FUNDAMENTAL_ANALYSIS: {
            id: 'mYF2_FBCvXw', // Fundamental Analysis
            title: 'Fundamental Analysis Explained',
            duration: '18:20'
        },
        RISK_MANAGEMENT: {
            id: 'r-m5F6hCt9Y', // Risk Management
            title: 'Risk Management Strategies',
            duration: '12:15'
        },
        PORTFOLIO_DIVERSIFICATION: {
            id: 'M3MkHMEWkF4', // Portfolio Management
            title: 'Portfolio Diversification',
            duration: '16:40'
        },
        MUTUAL_FUNDS: {
            id: 'DXR4x8pk4tU', // Mutual Funds
            title: 'Mutual Funds Explained',
            duration: '14:25'
        }
    },

    // === Feature Flags ===
    FEATURES: {
        ENABLE_REAL_TRADING: false, // Set to true for live trading
        ENABLE_AI_BOT: true,
        ENABLE_CHATBOT: true,
        ENABLE_LEARNING: true,
        ENABLE_QUIZ: true,
        DEMO_MODE: true // Shows mock data when APIs are not configured
    },

    // === Error Messages ===
    ERRORS: {
        NETWORK_ERROR: 'Network error. Please check your internet connection.',
        API_ERROR: 'API request failed. Please try again later.',
        AUTH_REQUIRED: 'Please login to access this feature.',
        INVALID_INPUT: 'Please check your input and try again.',
        SESSION_EXPIRED: 'Your session has expired. Please login again.',
        DEMAT_NOT_CONNECTED: 'Please connect your DEMAT account first.'
    },

    // === Success Messages ===
    SUCCESS: {
        LOGIN: 'Login successful! Welcome back.',
        SIGNUP: 'Account created successfully!',
        PLAN_GENERATED: 'Investment plan generated successfully!',
        DEMAT_CONNECTED: 'DEMAT account connected successfully!',
        QUIZ_COMPLETED: 'Quiz completed! Check your score.',
        MESSAGE_SENT: 'Message sent successfully!'
    }
};

// === Helper Functions ===

// Check if API keys are configured
CONFIG.isGeminiConfigured = () => {
    return CONFIG.API_KEYS.GEMINI_API_KEY !== 'YOUR_GEMINI_API_KEY_HERE';
};

CONFIG.isUpstoxConfigured = () => {
    return CONFIG.API_KEYS.UPSTOX.API_KEY && CONFIG.API_KEYS.UPSTOX.API_SECRET;
};

// Get full API URL
CONFIG.getApiUrl = (endpoint) => {
    if (endpoint.startsWith('/login') || endpoint.startsWith('/user') ||
        endpoint.startsWith('/portfolio') || endpoint.startsWith('/order')) {
        return CONFIG.API_ENDPOINTS.UPSTOX_BASE_URL + endpoint;
    }
    return endpoint;
};

// Get Gemini API URL
CONFIG.getGeminiUrl = () => {
    return `${CONFIG.API_ENDPOINTS.GEMINI_BASE_URL}${CONFIG.API_ENDPOINTS.GEMINI_GENERATE}?key=${CONFIG.API_KEYS.GEMINI_API_KEY}`;
};

// Get Upstox Login URL
CONFIG.getUpstoxLoginUrl = () => {
    const { API_KEY, REDIRECT_URI } = CONFIG.API_KEYS.UPSTOX;
    return `${CONFIG.API_ENDPOINTS.UPSTOX_BASE_URL}${CONFIG.API_ENDPOINTS.UPSTOX_LOGIN}?response_type=code&client_id=${API_KEY}&redirect_uri=${REDIRECT_URI}`;
};

// Format currency (Indian Rupee)
CONFIG.formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
};

// Format percentage
CONFIG.formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}