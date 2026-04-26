/* ============================================
   UPVEST - Real-Time Market Data API
   Fetches live data from Yahoo Finance
   ============================================ */

const MarketAPI = {
    // Yahoo Finance API endpoints (free, no API key required)
    // Use the URL from config which includes the CORS proxy
    BASE_URL: CONFIG.API_ENDPOINTS.MARKET_DATA_URL,

    /**
     * Fetch real-time NIFTY 50 data
     */
    async getNiftyData(range = '1d') {
        try {
            const symbol = '^NSEI'; // NIFTY 50 symbol on Yahoo Finance

            // For 1D view, use intraday 5-minute data, otherwise use daily data
            let interval, dataRange;
            if (range === '1d') {
                interval = '5m';   // 5-minute intervals for intraday
                dataRange = '1d';  // Today's data
            } else if (range === '1w') {
                interval = '1h';   // 1-hour intervals for week
                dataRange = '5d';  // 5 days
            } else {
                interval = '1d';   // Daily intervals for month
                dataRange = '1mo'; // 1 month
            }

            const url = `${this.BASE_URL}${symbol}?interval=${interval}&range=${dataRange}`;

            console.log('Fetching NIFTY from:', url);

            const response = await fetch(url);
            const data = await response.json();

            if (data.chart && data.chart.result && data.chart.result[0]) {
                const result = data.chart.result[0];
                const quote = result.indicators.quote[0];
                const timestamps = result.timestamp;

                // Get current price (most recent price from data)
                const currentPrice = result.meta.regularMarketPrice || quote.close[quote.close.length - 1];
                const previousClose = result.meta.previousClose || result.meta.chartPreviousClose;
                const change = currentPrice - previousClose;
                const changePercent = (change / previousClose) * 100;

                console.log('NIFTY API Response:', {
                    currentPrice,
                    previousClose,
                    change,
                    changePercent
                });

                // Get historical prices for chart (filter out null values)
                const prices = quote.close.filter(p => p !== null);
                const dates = timestamps.slice(-prices.length);

                return {
                    symbol: 'NIFTY 50',
                    currentPrice: currentPrice,
                    previousClose: previousClose,
                    change: change,
                    changePercent: changePercent,
                    prices: prices,
                    timestamps: dates,
                    isPositive: change >= 0
                };
            }

            throw new Error('Invalid data format');
        } catch (error) {
            console.error('Error fetching NIFTY data:', error);
            return this.getFallbackNiftyData();
        }
    },

    /**
     * Fetch real-time SENSEX data
     */
    async getSensexData(range = '1d') {
        try {
            const symbol = '^BSESN'; // SENSEX symbol on Yahoo Finance

            // For 1D view, use intraday 5-minute data, otherwise use daily data
            let interval, dataRange;
            if (range === '1d') {
                interval = '5m';   // 5-minute intervals for intraday
                dataRange = '1d';  // Today's data
            } else if (range === '1w') {
                interval = '1h';   // 1-hour intervals for week
                dataRange = '5d';  // 5 days
            } else {
                interval = '1d';   // Daily intervals for month
                dataRange = '1mo'; // 1 month
            }

            const url = `${this.BASE_URL}${symbol}?interval=${interval}&range=${dataRange}`;

            console.log('Fetching SENSEX from:', url);

            const response = await fetch(url);
            const data = await response.json();

            if (data.chart && data.chart.result && data.chart.result[0]) {
                const result = data.chart.result[0];
                const quote = result.indicators.quote[0];
                const timestamps = result.timestamp;

                // Get current price (most recent price from data)
                const currentPrice = result.meta.regularMarketPrice || quote.close[quote.close.length - 1];
                const previousClose = result.meta.previousClose || result.meta.chartPreviousClose;
                const change = currentPrice - previousClose;
                const changePercent = (change / previousClose) * 100;

                console.log('SENSEX API Response:', {
                    currentPrice,
                    previousClose,
                    change,
                    changePercent
                });

                // Get historical prices for chart (filter out null values)
                const prices = quote.close.filter(p => p !== null);
                const dates = timestamps.slice(-prices.length);

                return {
                    symbol: 'SENSEX',
                    currentPrice: currentPrice,
                    previousClose: previousClose,
                    change: change,
                    changePercent: changePercent,
                    prices: prices,
                    timestamps: dates,
                    isPositive: change >= 0
                };
            }

            throw new Error('Invalid data format');
        } catch (error) {
            console.error('Error fetching SENSEX data:', error);
            return this.getFallbackSensexData();
        }
    },

    /**
     * Fetch stock quote data
     */
    async getStockQuote(symbol) {
        try {
            // Add .NS suffix for NSE stocks if not present
            const yahooSymbol = symbol.includes('.') ? symbol : `${symbol}.NS`;
            const url = `${this.BASE_URL}${yahooSymbol}?interval=1d&range=1d`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.chart && data.chart.result && data.chart.result[0]) {
                const result = data.chart.result[0];
                const currentPrice = result.meta.regularMarketPrice;
                const previousClose = result.meta.chartPreviousClose;
                const change = currentPrice - previousClose;
                const changePercent = (change / previousClose) * 100;

                return {
                    symbol: symbol,
                    price: currentPrice,
                    change: change,
                    changePercent: changePercent,
                    previousClose: previousClose
                };
            }

            throw new Error('Invalid data format');
        } catch (error) {
            console.error(`Error fetching stock data for ${symbol}:`, error);
            return this.getFallbackStockData(symbol);
        }
    },

    /**
     * Fetch intraday data for 1D chart
     */
    async getIntradayData(symbol) {
        try {
            const url = `${this.BASE_URL}${symbol}?interval=5m&range=1d`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.chart && data.chart.result && data.chart.result[0]) {
                const result = data.chart.result[0];
                const quote = result.indicators.quote[0];
                const timestamps = result.timestamp;

                const prices = quote.close.filter(p => p !== null);
                const dates = timestamps.slice(-prices.length);

                return {
                    prices: prices,
                    timestamps: dates
                };
            }

            throw new Error('Invalid data format');
        } catch (error) {
            console.error('Error fetching intraday data:', error);
            return null;
        }
    },

    /**
     * Fallback data if API fails (uses recent approximate values)
     */
    getFallbackNiftyData() {
        console.warn('⚠️ Using fallback NIFTY data (API failed)');
        return {
            symbol: 'NIFTY 50',
            currentPrice: 25722.10,
            previousClose: 25532.80,
            change: 189.30,
            changePercent: 0.74,
            prices: this.generateFallbackPrices(25722, 30),
            timestamps: this.generateFallbackDates(30),
            isPositive: true,
            isFallback: true
        };
    },

    getFallbackSensexData() {
        console.warn('⚠️ Using fallback SENSEX data (API failed)');
        return {
            symbol: 'SENSEX',
            currentPrice: 84500.00,
            previousClose: 83879.50,
            change: 620.50,
            changePercent: 0.74,
            prices: this.generateFallbackPrices(84500, 30),
            timestamps: this.generateFallbackDates(30),
            isPositive: true,
            isFallback: true
        };
    },

    getFallbackStockData(symbol) {
        console.warn(`⚠️ Using fallback data for ${symbol} (API failed)`);
        // Generate random but realistic price
        const basePrice = 1000 + Math.random() * 2000;
        const change = (Math.random() - 0.5) * 50;
        return {
            symbol: symbol,
            price: basePrice,
            change: change,
            changePercent: (change / basePrice) * 100,
            previousClose: basePrice - change,
            isFallback: true
        };
    },

    generateFallbackPrices(basePrice, count) {
        const prices = [];
        let price = basePrice;
        for (let i = 0; i < count; i++) {
            const change = (Math.random() - 0.48) * (basePrice * 0.015);
            price += change;
            prices.push(parseFloat(price.toFixed(2)));
        }
        return prices;
    },

    generateFallbackDates(count) {
        const dates = [];
        for (let i = count - 1; i >= 0; i--) {
            dates.push(Date.now() - (i * 24 * 60 * 60 * 1000));
        }
        return dates;
    },

    /**
     * Fetch Gold Rate (via GOLDBEES.NS ETF)
     */
    async getGoldData() {
        try {
            const data = await this.getStockQuote('GOLDBEES.NS');
            return {
                price: data.price,
                change: data.change,
                changePercent: data.changePercent,
                timestamp: new Date()
            };
        } catch (error) {
            console.error('Error fetching Gold data:', error);
            return { price: 58.50, change: 0.5, changePercent: 0.8, isFallback: true }; // Approx unit price
        }
    },

    /**
     * Fetch Mutual Fund NAV and Returns (via MFAPI.in)
     * @param {string} schemeCode - AMFI Scheme Code
     */
    async getMutualFundData(schemeCode) {
        try {
            const response = await fetch(`https://api.mfapi.in/mf/${schemeCode}`);
            const data = await response.json();

            if (data && data.data && data.data.length > 0) {
                const currentNAV = parseFloat(data.data[0].nav);
                const prevNAV = parseFloat(data.data[1].nav); // Yesterday
                const nav1YearAgo = parseFloat(data.data.find(d => {
                    const date = new Date(d.date.split('-').reverse().join('-')); // DD-MM-YYYY to Date
                    const oneYearAgo = new Date();
                    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
                    return date <= oneYearAgo;
                })?.nav || currentNAV);

                const returns1Y = ((currentNAV - nav1YearAgo) / nav1YearAgo) * 100;

                return {
                    name: data.meta.fund_house + ' - ' + data.meta.scheme_name,
                    nav: currentNAV,
                    change: currentNAV - prevNAV,
                    changePercent: ((currentNAV - prevNAV) / prevNAV) * 100,
                    returns1Y: returns1Y,
                    lastUpdated: data.data[0].date
                };
            }
            throw new Error('Invalid MF data');
        } catch (error) {
            console.error(`Error fetching MF data for ${schemeCode}:`, error);
            return null;
        }
    },

    /**
     * Get Comprehensive Market Context for AI
     * Aggregates Indices, Gold, and key Mutual Funds
     */
    async getMarketContext() {
        try {
            const [nifty, sensex, gold, mfLargeCap, mfMidCap, mfSmallCap] = await Promise.all([
                this.getNiftyData(),
                this.getSensexData(),
                this.getGoldData(),
                this.getMutualFundData('120503'), // SBI Bluechip (Large Cap)
                this.getMutualFundData('118989'), // HDFC Mid-Cap Opportunities (Mid Cap)
                this.getMutualFundData('118778')  // Nippon India Small Cap (Small Cap)
            ]);

            return {
                indices: {
                    nifty: nifty,
                    sensex: sensex
                },
                commodities: {
                    gold: gold
                },
                mutualFunds: {
                    largeCap: mfLargeCap,
                    midCap: mfMidCap,
                    smallCap: mfSmallCap
                },
                timestamp: new Date()
            };
        } catch (error) {
            console.error('Error fetching market context:', error);
            return null;
        }
    },

    /**
     * Format timestamp to readable date
     */
    formatDate(timestamp, format = 'short') {
        const date = new Date(timestamp * 1000);
        if (format === 'short') {
            return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
        } else if (format === 'time') {
            return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        }
        return date.toLocaleDateString('en-IN');
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarketAPI;
}
