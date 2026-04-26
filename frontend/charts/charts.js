/* ============================================
   UPVEST - Charts JavaScript
   Market charts with Chart.js
   ============================================ */

let niftyChart = null;
let sensexChart = null;

/**
 * Initialize all market charts
 */
function initMarketCharts() {
    initNiftyChart();
    initSensexChart();
    setupChartRangeButtons();
}

/**
 * Initialize NIFTY 50 chart
 */
async function initNiftyChart() {
    const canvas = document.getElementById('niftyChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    console.log('📊 Fetching real-time NIFTY 50 data...');
    
    // Fetch real-time intraday data (1D view by default)
    const marketData = await MarketAPI.getNiftyData('1d');
    
    if (marketData.isFallback) {
        console.warn('⚠️ Using fallback data for NIFTY');
    } else {
        console.log('✅ Live NIFTY data loaded:', marketData.currentPrice);
    }
    
    // Prepare chart data with time labels for intraday
    const data = marketData.prices;
    const labels = marketData.timestamps.map(ts => 
        MarketAPI.formatDate(ts, 'time')
    );
    
    // Create chart
    niftyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [ChartConfig.getLineDataset('NIFTY 50', data, marketData.isPositive)]
        },
        options: ChartConfig.defaultOptions
    });
    
    // Update price display with real-time data
    updatePriceDisplayFromAPI('nifty', marketData);
}

/**
 * Initialize SENSEX chart
 */
async function initSensexChart() {
    const canvas = document.getElementById('sensexChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    console.log('📊 Fetching real-time SENSEX data...');
    
    // Fetch real-time intraday data (1D view by default)
    const marketData = await MarketAPI.getSensexData('1d');
    
    if (marketData.isFallback) {
        console.warn('⚠️ Using fallback data for SENSEX');
    } else {
        console.log('✅ Live SENSEX data loaded:', marketData.currentPrice);
    }
    
    // Prepare chart data with time labels for intraday
    const data = marketData.prices;
    const labels = marketData.timestamps.map(ts => 
        MarketAPI.formatDate(ts, 'time')
    );
    
    // Create chart
    sensexChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [ChartConfig.getLineDataset('SENSEX', data, marketData.isPositive)]
        },
        options: ChartConfig.defaultOptions
    });
    
    // Update price display with real-time data
    updatePriceDisplayFromAPI('sensex', marketData);
}

/**
 * Generate mock chart data
 */
function generateMockChartData(basePrice, points) {
    const data = [];
    let price = basePrice;
    
    for (let i = 0; i < points; i++) {
        // Random walk with slight upward bias
        const change = (Math.random() - 0.48) * (basePrice * 0.02);
        price += change;
        data.push(parseFloat(price.toFixed(2)));
    }
    
    return data;
}

/**
 * Update price display for a chart (legacy - for fallback)
 */
function updatePriceDisplay(chartType, data) {
    const currentPrice = data[data.length - 1];
    const previousPrice = data[0];
    const change = currentPrice - previousPrice;
    const changePercent = (change / previousPrice) * 100;
    
    const priceEl = document.getElementById(`${chartType}Price`);
    const changeEl = document.getElementById(`${chartType}Change`);
    
    if (priceEl) {
        priceEl.textContent = currentPrice.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    if (changeEl) {
        const sign = change >= 0 ? '+' : '';
        changeEl.textContent = `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
        changeEl.className = `chart-change ${change >= 0 ? 'positive' : 'negative'}`;
    }
}

/**
 * Update price display from API data (real-time)
 */
function updatePriceDisplayFromAPI(chartType, marketData) {
    const priceEl = document.getElementById(`${chartType}Price`);
    const changeEl = document.getElementById(`${chartType}Change`);
    
    if (priceEl) {
        priceEl.textContent = marketData.currentPrice.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    if (changeEl) {
        const sign = marketData.change >= 0 ? '+' : '';
        changeEl.textContent = `${sign}${marketData.change.toFixed(2)} (${sign}${marketData.changePercent.toFixed(2)}%)`;
        changeEl.className = `chart-change ${marketData.isPositive ? 'positive' : 'negative'}`;
    }
}

/**
 * Setup chart range buttons (1D, 1W, 1M)
 */
function setupChartRangeButtons() {
    const chartButtons = document.querySelectorAll('.chart-btn');
    
    chartButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const range = this.getAttribute('data-range');
            const chartCard = this.closest('.chart-card');
            const chartCanvas = chartCard.querySelector('canvas');
            
            // Update active state
            chartCard.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update chart based on range
            await updateChartRange(chartCanvas.id, range);
        });
    });
}

/**
 * Update chart data based on selected range
 */
async function updateChartRange(chartId, range) {
    console.log(`📊 Updating ${chartId} for range: ${range}`);
    
    // Determine which API to call
    const isNifty = chartId === 'niftyChart';
    const chartType = isNifty ? 'nifty' : 'sensex';
    
    // Map button range to API range
    const apiRange = range === '1D' ? '1d' : range === '1W' ? '1w' : '1m';
    
    // Fetch new data from API
    const marketData = isNifty 
        ? await MarketAPI.getNiftyData(apiRange)
        : await MarketAPI.getSensexData(apiRange);
    
    if (marketData.isFallback) {
        console.warn(`⚠️ Using fallback data for ${isNifty ? 'NIFTY' : 'SENSEX'}`);
    }
    
    // Prepare chart data
    const data = marketData.prices;
    const labels = marketData.timestamps.map(ts => {
        if (range === '1D') {
            return MarketAPI.formatDate(ts, 'time');  // Time format for intraday
        } else {
            return MarketAPI.formatDate(ts, 'short'); // Date format for daily
        }
    });
    
    // Update chart
    const chart = isNifty ? niftyChart : sensexChart;
    if (chart) {
        chart.data.labels = labels;
        chart.data.datasets[0] = ChartConfig.getLineDataset(
            isNifty ? 'NIFTY 50' : 'SENSEX',
            data,
            marketData.isPositive
        );
        chart.update('none'); // Update without animation for faster response
        
        // Update price display with real-time data
        updatePriceDisplayFromAPI(chartType, marketData);
    }
    
    console.log(`✅ Chart updated for ${range}`);
}

/**
 * Refresh all charts with new data
 */
function refreshCharts() {
    if (niftyChart) {
        const activeBtn = document.querySelector('#niftyChart').closest('.chart-card').querySelector('.chart-btn.active');
        const range = activeBtn ? activeBtn.getAttribute('data-range') : '1D';
        updateChartRange('niftyChart', range);
    }
    
    if (sensexChart) {
        const activeBtn = document.querySelector('#sensexChart').closest('.chart-card').querySelector('.chart-btn.active');
        const range = activeBtn ? activeBtn.getAttribute('data-range') : '1D';
        updateChartRange('sensexChart', range);
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initMarketCharts, refreshCharts };
}