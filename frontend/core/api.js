/* ============================================
   UPVEST - API Service
   Centralized API calls and data management
   ============================================ */

const API = {

    // === Generic HTTP Request ===

    /**
     * Make HTTP request
     * @param {string} url - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise} Response data
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },

    // === Gemini AI API ===

    /**
     * Generate AI investment recommendation using Gemini
     * @param {object} userData - User financial data
     * @returns {Promise<string>} AI recommendation
     */
    async generateInvestmentPlan(userData) {
        // Check if Gemini is configured
        if (!CONFIG.isGeminiConfigured()) {
            console.warn('Gemini API not configured. Using mock data.');
            return this.generateMockInvestmentPlan(userData);
        }

        // Fetch Real-Time Market Context
        Utils.showToast('Fetching real-time market data...', 'info');
        const marketContext = await MarketAPI.getMarketContext();

        const prompt = this.buildInvestmentPrompt(userData, marketContext);

        try {
            const response = await this.request(CONFIG.getGeminiUrl(), {
                method: 'POST',
                body: JSON.stringify({
                    contents: [{
                        parts: [{ text: prompt }]
                    }]
                })
            });

            let planText = response.candidates[0].content.parts[0].text;

            // Clean up Markdown code blocks if present
            planText = planText.replace(/```json\n?|```/g, '').trim();

            try {
                return JSON.parse(planText);
            } catch (e) {
                console.error('Failed to parse AI JSON response:', e);
                console.log('Raw output:', planText);
                throw new Error('AI response was not in valid JSON format');
            }
        } catch (error) {
            console.error('Gemini API Error:', error);
            console.log('Falling back to mock investment plan with real market data');
            return this.generateMockInvestmentPlan(userData);
        }
    },

    /**
     * Build investment recommendation prompt for Gemini
     * @param {object} userData - User financial data
     * @returns {string} Formatted prompt
     */
    buildInvestmentPrompt(userData, marketContext) {
        const { salary, expenses, savings, age, risk, currentSavings, durationYears } = userData;
        const years = durationYears || 10; // Default to 10 if not provided

        let marketDataStr = 'Market Data unavailable.';
        if (marketContext) {
            const { nifty, sensex } = marketContext.indices;
            const { largeCap, midCap, smallCap } = marketContext.mutualFunds;

            marketDataStr = `
REAL-TIME MARKET CONTEXT (Use this for planning):
- NIFTY 50: ${nifty.currentPrice} (${nifty.changePercent.toFixed(2)}%)
- SENSEX: ${sensex.currentPrice} (${sensex.changePercent.toFixed(2)}%)
- Gold ETF (GOLDBEES): ₹${marketContext.commodities.gold.price}
- Recent MF Returns (1Y):
  - Large Cap (SBI Bluechip): ${largeCap ? largeCap.returns1Y.toFixed(2) + '%' : 'N/A'}
  - Mid Cap (HDFC Mid-Cap): ${midCap ? midCap.returns1Y.toFixed(2) + '%' : 'N/A'}
  - Small Cap (Nippon): ${smallCap ? smallCap.returns1Y.toFixed(2) + '%' : 'N/A'}
`;
        }

        return `You are a professional investment banker and certified financial planner. Analyze this client profile and create a detailed, personalized investment plan based on REAL-TIME market conditions.

CLIENT PROFILE:
- Age: ${age} years
- Monthly Income: ₹${Utils.formatNumber(salary)}
- Monthly Expenses: ₹${Utils.formatNumber(expenses)}
- Monthly Surplus (for SIPs): ₹${Utils.formatNumber(savings)}
- Existing Lump Sum Savings: ₹${Utils.formatNumber(currentSavings || 0)}
- Age-based Risk Capacity: ${age < 35 ? 'High' : age < 50 ? 'Medium' : 'Low'}
- User Selected Risk Appetite: ${risk}

${marketDataStr}

REQUIREMENTS:
1. Create a TWO-PART strategy:
   - Part A: Monthly SIP Plan using the Monthly Surplus (₹${Utils.formatNumber(savings)}). Focus on wealth creation (Equity/Mutual Funds).
   - Part B: Lump Sum Allocation using Existing Savings (₹${Utils.formatNumber(currentSavings || 0)}). Focus on safety and stability (FD/Debt/Liquid/Gold).
2. The plan must be REALISTIC based on the current market levels provided above.
3. If NIFTY is at all-time highs, suggest a more staggered deployment (STP) for the lump sum.
4. Calculate ${years}-year wealth projection primarily based on the SIP inflows + conservative growth of lump sum.
5. Return the result strictly in JSON format.

FORMAT YOUR RESPONSE EXACTLY AS THIS JSON OBJECT (No Markdown, No Text outside JSON):
{
  "executive_summary": "Brief 2-sentence summary of the strategy covering both SIP and Lump Sum.",
  "risk_analysis": "Assessment of user risk profile vs market conditions.",
  "asset_allocation": {
    "equity": 50,
    "debt": 30,
    "gold": 10,
    "emergency": 10
  },
  "investment_strategy": [
    {
      "category": "Equity Mutual Funds (SIP)",
      "amount": 10000,
      "percentage": 50,
      "recommendation": "Start SIP in Nifty 50 Index Fund",
      "expected_return": "12-14% p.a.",
      "rationale": "High growth potential via monthly SIPs"
    },
    {
       "category": "Safe Lump Sum (FD/Debt)",
       "amount": 500000,
       "percentage": 100,
       "recommendation": "Deploy existing savings in Corporate Bond Fund or FD",
       "expected_return": "7-8% p.a.",
       "rationale": "Capital preservation for accumulated savings"
    }
  ],
  "projections": {
    "total_investment": 2400000,
    "expected_value": 4500000,
    "estimated_gains": 2100000,
    "cagr": 12.5,
    "duration_years": ${years}
  },
  "market_insight": "One impactful sentence about current market levels."
}`;
    },

    /**
     * Generate mock investment plan (fallback)
     * @param {object} userData - User financial data
     * @returns {string} Mock investment plan
     */
    generateMockInvestmentPlan(userData) {
        const { savings, age, risk, currentSavings, durationYears } = userData;
        const years = durationYears || 10; // Default to 10 years

        // Adjust allocation based on age and risk
        let allocation = { equity: 40, debt: 30, gold: 10, emergency: 20 };

        if (risk === 'low') {
            allocation = { equity: 25, debt: 45, gold: 15, emergency: 15 };
        } else if (risk === 'high') {
            allocation = { equity: 60, debt: 20, gold: 10, emergency: 10 };
        }

        // Calculate amounts
        const amounts = {
            equity: Math.round(savings * allocation.equity / 100),
            debt: Math.round(savings * allocation.debt / 100),
            gold: Math.round(savings * allocation.gold / 100),
            emergency: Math.round(savings * allocation.emergency / 100)
        };

        // Calculate projection for selected duration
        const totalInvested = (savings * 12 * years) + (currentSavings || 0);
        const avgReturn = risk === 'low' ? 0.09 : risk === 'high' ? 0.14 : 0.11;
        const sipFutureValue = Utils.calculateSIP(savings, avgReturn * 100, years).futureValue;
        const lumpSumFutureValue = (currentSavings || 0) * Math.pow(1.07, years); // 7% for safe investments
        const futureValue = sipFutureValue + lumpSumFutureValue;
        const gains = futureValue - totalInvested;
        const cagr = avgReturn * 100;

        return {
            "executive_summary": "Based on your risk profile, we recommend a balanced portfolio with a focus on long-term growth through equity SIPs, while maintaining safety with debt and gold allocations.",
            "risk_analysis": `Your profile suggests a ${risk} risk capacity. This plan balances growth potential with necessary stability.`,
            "asset_allocation": allocation,
            "investment_strategy": [
                {
                    "category": "Equity Mutual Funds (SIP)",
                    "amount": amounts.equity,
                    "percentage": allocation.equity,
                    "recommendation": "Start SIPs in Nifty 50 Index Fund and Flexi Cap Funds for long-term wealth creation.",
                    "expected_return": "12-14% p.a.",
                    "rationale": "High growth potential for long-term goals."
                },
                {
                    "category": "Debt & PPF (Tax Saving)",
                    "amount": amounts.debt,
                    "percentage": allocation.debt,
                    "recommendation": "Invest in PPF for tax saving and Corporate Bond Funds for stability.",
                    "expected_return": "7-8% p.a.",
                    "rationale": "Stability and tax benefits."
                },
                {
                    "category": "Gold (Sovereign/ETF)",
                    "amount": amounts.gold,
                    "percentage": allocation.gold,
                    "recommendation": "Sovereign Gold Bonds (SGB) or Gold ETFs as a hedge against inflation.",
                    "expected_return": "8-10% p.a.",
                    "rationale": "Portfolio diversification and hedge."
                },
                {
                    "category": "Emergency Fund",
                    "amount": amounts.emergency,
                    "percentage": allocation.emergency,
                    "recommendation": "Keep in Liquid Funds or High-Yield Savings Account for instant access.",
                    "expected_return": "5-7% p.a.",
                    "rationale": "Safety net for unforeseen expenses."
                }
            ],
            "projections": {
                "total_investment": totalInvested,
                "expected_value": Math.round(futureValue),
                "estimated_gains": Math.round(gains),
                "cagr": parseFloat(cagr.toFixed(1)),
                "duration_years": years
            },
            "market_insight": "Current market valuations suggest a disciplined SIP approach is better than lump-sum investments."
        };
    },

    /**
     * Get chatbot response using Gemini
     * @param {string} message - User message
     * @returns {Promise<string>} Bot response
     */
    async getChatbotResponse(message) {
        if (!CONFIG.isGeminiConfigured()) {
            return this.getMockChatbotResponse(message);
        }

        const prompt = `You are UPVEST's helpful investment assistant. Answer this question professionally and concisely (max 100 words):

User: ${message}

Provide helpful, accurate information about investments, stock markets, and the UPVEST platform.`;

        try {
            const response = await this.request(CONFIG.getGeminiUrl(), {
                method: 'POST',
                body: JSON.stringify({
                    contents: [{
                        parts: [{ text: prompt }]
                    }]
                })
            });

            return response.candidates[0].content.parts[0].text;
        } catch (error) {
            return this.getMockChatbotResponse(message);
        }
    },

    /**
     * Mock chatbot responses (fallback)
     * @param {string} message - User message
     * @returns {string} Mock response
     */
    getMockChatbotResponse(message) {
        const msg = message.toLowerCase();

        // 1. Stock Market Basics
        if (msg.includes('basic') || msg.includes('stock market') || msg.includes('begin')) {
            return "Investing in the stock market means buying a small piece of a company (a share). When the company grows, the value of your share increases. \n\n**To start:** \n1. Open a DEMAT account. \n2. Decide your budget. \n3. Choose between Stocks (high risk/reward) or Mutual Funds (professionally managed). \n4. Start with an SIP (Systematic Investment Plan) for disciplined investing.";
        }

        // 2. DEMAT Account
        if (msg.includes('demat') || msg.includes('account') || msg.includes('open')) {
            return "A DEMAT account is like a bank account for your shares. You can connect or open one directly through UPVEST. \n\nWe support integration with top brokers like **Zerodha, Upstox, Angel One, and Groww**. \n\nGo to your Profile > Linked Accounts to get started.";
        }

        // 3. Investment Definition
        if (msg.includes('what is investment') || msg.includes('define investment') || msg.includes('meaning')) {
            return "Investment is the act of putting your money to work to generate returns over time. \n\nInstead of keeping cash idle, you buy assets like Stocks, Mutual Funds, Gold, or Real Estate. The goal is to beat inflation and grow your wealth. \n\n*Example:* Investing ₹5,000/month in an SIP can grow significantly over 10 years due to compounding.";
        }

        // 4. Risk Management
        if (msg.includes('risk') || msg.includes('safe') || msg.includes('loss')) {
            return "Risk management is about protecting your capital. \n\n**Key Strategies:** \n1. **Diversification:** Don't put all eggs in one basket. Mix Equity, Debt, and Gold. \n2. **Long-term View:** Markets are volatile in the short term but tend to grow over 5+ years. \n3. **Asset Allocation:** UPVEST analyzes your profile to suggest the right mix based on your age and goals.";
        }

        // 5. SIP vs Lump Sum
        if (msg.includes('sip') || msg.includes('lump sum') || msg.includes('monthly')) {
            return "**SIP (Systematic Investment Plan)** is best for salaried individuals. It averages out market volatility (Rupee Cost Averaging). \n\n**Lump Sum** is good when markets are low or you have a large bonus. \n\n*UPVEST Recommendation:* Use SIPs for your monthly surplus and Lump Sum for existing savings.";
        }

        // 6. Returns
        if (msg.includes('return') || msg.includes('profit') || msg.includes('how much')) {
            return "Returns depend on the asset class: \n- **FD/Debt:** 6-8% (Safe) \n- **Gold:** 8-10% (Hedge against inflation) \n- **Equity Mutual Funds:** 12-15% (Growth) \n- **Direct Stocks:** 15%+ (High Risk) \n\n*Note:* Equity returns are volatile and best realized over 5+ years.";
        }

        // Default Fallback
        return "That's a great question! However, I'm currently in 'Offline Mode' and can only answer basic queries about Stock Basics, DEMAT Accounts, SIPs, and Risk. \n\nPlease check your internet connection or try asking: \n- 'What is stock market investing?' \n- 'How to open a DEMAT account?'";
    },

    // === Market Data API ===

    /**
     * Fetch real-time stock quote (Yahoo Finance)
     * @param {string} symbol - Stock symbol (e.g., 'RELIANCE.NS')
     * @returns {Promise<object>} Stock data
     */
    async getStockQuote(symbol) {
        try {
            const url = `${CONFIG.API_ENDPOINTS.MARKET_DATA_URL}${symbol}?interval=1d&range=1d`;
            const response = await this.request(url);

            const result = response.chart.result[0];
            const quote = result.meta;
            const prices = result.indicators.quote[0];

            return {
                symbol: result.meta.symbol,
                price: quote.regularMarketPrice,
                change: quote.regularMarketPrice - quote.previousClose,
                changePercent: ((quote.regularMarketPrice - quote.previousClose) / quote.previousClose) * 100,
                open: prices.open[0],
                high: prices.high[0],
                low: prices.low[0],
                volume: prices.volume[0],
                timestamp: new Date(quote.regularMarketTime * 1000)
            };
        } catch (error) {
            console.error('Stock quote error:', error);
            return this.getMockStockQuote(symbol);
        }
    },

    /**
     * Generate mock stock data (fallback)
     * @param {string} symbol - Stock symbol
     * @returns {object} Mock stock data
     */
    getMockStockQuote(symbol) {
        const basePrice = Math.random() * 2000 + 500;
        const change = (Math.random() - 0.5) * 50;

        return {
            symbol: symbol,
            price: basePrice,
            change: change,
            changePercent: (change / basePrice) * 100,
            open: basePrice - 10,
            high: basePrice + 20,
            low: basePrice - 15,
            volume: Math.floor(Math.random() * 10000000),
            timestamp: new Date()
        };
    },

    /**
     * Fetch historical stock data
     * @param {string} symbol - Stock symbol
     * @param {string} range - Time range ('1d', '5d', '1mo', '1y')
     * @returns {Promise<Array>} Historical prices
     */
    async getHistoricalData(symbol, range = '1mo') {
        try {
            const url = `${CONFIG.API_ENDPOINTS.MARKET_DATA_URL}${symbol}?interval=1d&range=${range}`;
            const response = await this.request(url);

            const result = response.chart.result[0];
            const timestamps = result.timestamp;
            const prices = result.indicators.quote[0].close;

            return timestamps.map((time, index) => ({
                date: new Date(time * 1000),
                price: prices[index]
            }));
        } catch (error) {
            console.error('Historical data error:', error);
            return this.generateMockHistoricalData(50);
        }
    },

    /**
     * Generate mock historical data
     * @param {number} points - Number of data points
     * @returns {Array} Mock historical data
     */
    generateMockHistoricalData(points = 50) {
        const data = [];
        let price = 18000 + Math.random() * 2000;

        for (let i = 0; i < points; i++) {
            price += (Math.random() - 0.5) * 200;
            data.push({
                date: new Date(Date.now() - (points - i) * 86400000),
                price: price
            });
        }

        return data;
    },

    // === Upstox API (DEMAT Integration) ===

    /**
     * Initialize Upstox OAuth login
     * @returns {string} Login URL
     */
    getUpstoxLoginUrl() {
        return CONFIG.getUpstoxLoginUrl();
    },

    /**
     * Exchange auth code for access token
     * @param {string} authCode - Authorization code from callback
     * @returns {Promise<object>} Access token data
     */
    async getUpstoxAccessToken(authCode) {
        const { API_KEY, API_SECRET, REDIRECT_URI } = CONFIG.API_KEYS.UPSTOX;

        try {
            const response = await this.request(
                CONFIG.getApiUrl(CONFIG.API_ENDPOINTS.UPSTOX_TOKEN),
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: new URLSearchParams({
                        code: authCode,
                        client_id: API_KEY,
                        client_secret: API_SECRET,
                        redirect_uri: REDIRECT_URI,
                        grant_type: 'authorization_code'
                    })
                }
            );

            return response;
        } catch (error) {
            console.error('Upstox token error:', error);
            throw error;
        }
    },

    /**
     * Get Upstox user profile
     * @param {string} accessToken - Access token
     * @returns {Promise<object>} User profile
     */
    async getUpstoxProfile(accessToken) {
        try {
            const response = await this.request(
                CONFIG.getApiUrl(CONFIG.API_ENDPOINTS.UPSTOX_PROFILE),
                {
                    headers: {
                        'Authorization': `Bearer ${accessToken} `
                    }
                }
            );

            return response.data;
        } catch (error) {
            console.error('Upstox profile error:', error);
            throw error;
        }
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}