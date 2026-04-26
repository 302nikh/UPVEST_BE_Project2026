/* ============================================
   AI Trading Agent Dashboard JavaScript
   Connects to Python backend via BackendAPI
   ============================================ */

// Current trading mode — updated by loadTradingMode()
let currentTradingMode = 'paper';

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (typeof Navigation !== 'undefined' && !Navigation.initProtectedPage()) return;

    // Load navbar
    await loadNavbar();

    // Initialize dashboard
    initAgentDashboard();
});

/**
 * Load navbar component
 */
async function loadNavbar() {
    try {
        const response = await fetch('../home/navbar.html');
        const html = await response.text();
        document.getElementById('navbar-container').innerHTML = html;

        if (typeof initNavbar === 'function') {
            initNavbar();
        }
    } catch (error) {
        console.error('Error loading navbar:', error);
    }
}

/**
 * Initialize agent dashboard
 */
async function initAgentDashboard() {
    // Setup event listeners
    setupEventListeners();

    // Check backend connection
    await checkConnection();

    // Load trading mode first (toggles warning banner, pill, Upstox badge)
    await loadTradingMode();

    // Load initial data
    await refreshAllData();

    // Setup auto-refresh
    setInterval(refreshAllData, 30000); // Refresh every 30 seconds
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Agent control buttons
    document.getElementById('startAgentBtn').addEventListener('click', startAgent);
    document.getElementById('stopAgentBtn').addEventListener('click', stopAgent);

    // Refresh trades button
    document.getElementById('refreshTradesBtn').addEventListener('click', loadTrades);

    // AI Prediction button
    document.getElementById('getPredictionBtn').addEventListener('click', getAIPrediction);
    // Note: pill option clicks are handled inline via onclick="handleModeToggle(...)" in HTML
}

/**
 * Check backend connection
 */
async function checkConnection() {
    const statusEl = document.getElementById('connectionStatus');
    const dotEl = statusEl.querySelector('.status-dot');
    const textEl = statusEl.querySelector('span:last-child');

    try {
        const isConnected = await BackendAPI.isConnected();

        if (isConnected) {
            dotEl.className = 'status-dot online';
            textEl.textContent = 'Backend Connected';
            enableAgentControls(true);
        } else {
            dotEl.className = 'status-dot offline';
            textEl.textContent = 'Backend Offline';
            showToast('Backend server is offline. Start it with: python backend_api.py', 'warning');
        }
    } catch (error) {
        dotEl.className = 'status-dot offline';
        textEl.textContent = 'Connection Error';
        showToast('Cannot connect to backend server', 'error');
    }
}

/**
 * Enable/disable agent controls
 */
function enableAgentControls(enabled) {
    document.getElementById('startAgentBtn').disabled = !enabled;
    document.getElementById('stopAgentBtn').disabled = !enabled;
}

/**
 * Refresh all dashboard data
 */
async function refreshAllData() {
    await Promise.all([
        loadAgentStatus(),
        loadPortfolioStats(),
        loadTrades(),
        loadDailySummary()
    ]);
}

/**
 * Load agent status
 */
async function loadAgentStatus() {
    try {
        const status = await BackendAPI.getAgentStatus();

        const iconEl = document.getElementById('agentIcon');
        const statusTextEl = document.getElementById('agentStatusText');
        const statusDescEl = document.getElementById('agentStatusDesc');
        const startBtn = document.getElementById('startAgentBtn');
        const stopBtn = document.getElementById('stopAgentBtn');

        if (status.running) {
            iconEl.textContent = '🟢';
            statusTextEl.textContent = 'Agent Status: RUNNING';
            statusDescEl.textContent = `Started at ${new Date(status.started_at).toLocaleTimeString()}`;
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            iconEl.textContent = '🤖';
            statusTextEl.textContent = 'Agent Status: STOPPED';
            statusDescEl.textContent = status.last_signal || 'Ready to start';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }

        // Update stats
        document.getElementById('tradesToday').textContent = status.trades_today;

        const pnl = status.pnl_today;
        const pnlEl = document.getElementById('todayPnL');
        pnlEl.textContent = `${pnl >= 0 ? '+' : ''}₹${pnl.toFixed(2)}`;
        pnlEl.style.color = pnl >= 0 ? '#10b981' : '#ef4444';

    } catch (error) {
        console.error('Error loading agent status:', error);
    }
}

/**
 * Load portfolio stats
 */
async function loadPortfolioStats() {
    try {
        const portfolio = await BackendAPI.getPortfolio();

        document.getElementById('accountBalance').textContent =
            `₹${portfolio.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById('openPositions').textContent = portfolio.open_positions;

    } catch (error) {
        console.error('Error loading portfolio:', error);
        document.getElementById('accountBalance').textContent = '₹0.00';
    }
}

/**
 * Load trade history
 */
async function loadTrades() {
    const tbody = document.getElementById('tradesTableBody');

    try {
        const trades = await BackendAPI.getTradesToday();

        if (trades.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="loading-text">No trades today</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = trades.map(trade => {
            const formatted = BackendAPI.formatTrade(trade);
            return `
                <tr>
                    <td>${formatted.formattedTime}</td>
                    <td><strong>${trade.stock_name}</strong></td>
                    <td class="${trade.signal === 'BUY' ? 'signal-buy' : 'signal-sell'}">${trade.signal}</td>
                    <td>${trade.quantity}</td>
                    <td>${formatted.formattedPrice}</td>
                    <td>${trade.strategy}</td>
                    <td>${formatted.confidencePercent}</td>
                    <td class="${trade.status === 'SUCCESS' ? 'status-success' : 'status-failed'}">${trade.status}</td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading trades:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="loading-text">Error loading trades</td>
            </tr>
        `;
    }
}

/**
 * Load daily summary and render chart
 */
async function loadDailySummary() {
    try {
        const summaries = await BackendAPI.getDailySummary(14); // Last 14 days

        if (summaries.length > 0) {
            renderPnLChart(summaries);
        }

    } catch (error) {
        console.error('Error loading daily summary:', error);
    }
}

/**
 * Render P&L chart
 */
let pnlChart = null;
function renderPnLChart(summaries) {
    const ctx = document.getElementById('pnlChart');
    if (!ctx) return;

    // Prepare data
    const labels = summaries.map(s => s.date).reverse();
    const data = summaries.map(s => s.total_pnl).reverse();

    // Destroy existing chart
    if (pnlChart) {
        pnlChart.destroy();
    }

    // Create new chart
    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily P&L',
                data: data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)',
                        callback: function (value) {
                            return '₹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * Load current trading mode from backend and update UI.
 */
async function loadTradingMode() {
    try {
        const resp = await fetch(`${BackendAPI.BASE_URL}/api/trading-mode`);
        if (!resp.ok) return;
        const data = await resp.json();
        currentTradingMode = data.mode || 'paper';
        applyModeUI(currentTradingMode);
    } catch (e) {
        console.warn('Could not load trading mode:', e);
    }
    // Always refresh Upstox connection badge
    await checkUpstoxConnection();
}

/**
 * Update pill, warning banner, and Upstox badge to reflect the given mode.
 */
function applyModeUI(mode) {
    const pillPaper = document.getElementById('pillPaper');
    const pillLive  = document.getElementById('pillLive');
    const banner    = document.getElementById('liveWarningBanner');

    if (!pillPaper || !pillLive || !banner) return;

    if (mode === 'live') {
        pillPaper.className = 'pill-option';
        pillLive.className  = 'pill-option active-live';
        banner.classList.add('visible');
    } else {
        pillPaper.className = 'pill-option active-paper';
        pillLive.className  = 'pill-option';
        banner.classList.remove('visible');
    }
}

/**
 * Check Upstox connection status and update the badge.
 */
async function checkUpstoxConnection() {
    const badge    = document.getElementById('upstoxBadge');
    const badgeTxt = document.getElementById('upstoxBadgeText');
    if (!badge || !badgeTxt) return false;

    try {
        const resp = await fetch(`${BackendAPI.BASE_URL}/api/auth/status`);
        if (!resp.ok) throw new Error('Status endpoint error');
        const data = await resp.json();
        const connected = data.connected === true;

        if (connected) {
            badge.className = 'upstox-status-badge connected';
            badgeTxt.textContent = 'Upstox Connected';
        } else {
            badge.className = 'upstox-status-badge disconnected';
            badgeTxt.textContent = 'Upstox Not Connected';
        }
        return connected;
    } catch (e) {
        badge.className = 'upstox-status-badge disconnected';
        badgeTxt.textContent = 'Upstox Not Connected';
        return false;
    }
}

/**
 * Handle trading mode toggle (called from pill onclick in HTML).
 */
async function handleModeToggle(requestedMode) {
    if (requestedMode === currentTradingMode) return; // already in this mode

    if (requestedMode === 'live') {
        // Step 1: Verify Upstox is connected before even asking to confirm
        const connected = await checkUpstoxConnection();
        if (!connected) {
            showToast('Connect your Upstox Demat account first before enabling Live trading.', 'warning');
            return;
        }

        // Step 2: Require explicit confirmation — REAL money warning
        const confirmed = confirm(
            '⚠️  LIVE TRADING WARNING\n\n' +
            'You are about to switch to LIVE mode.\n' +
            'The agent will place REAL orders on your Upstox Demat account\n' +
            'using REAL money.\n\n' +
            'Make sure your Upstox account has sufficient margin.\n\n' +
            'Click OK to confirm and switch to LIVE mode.'
        );
        if (!confirmed) return;
    }

    try {
        const resp = await fetch(
            `${BackendAPI.BASE_URL}/api/trading-mode/switch?mode=${requestedMode}&confirmed=true`,
            { method: 'POST' }
        );
        const data = await resp.json();

        if (resp.ok && data.success) {
            currentTradingMode = requestedMode;
            applyModeUI(requestedMode);
            const label = requestedMode === 'live' ? '🔴 LIVE' : '📝 Paper';
            showToast(`Switched to ${label} trading mode`, requestedMode === 'live' ? 'warning' : 'success');
        } else {
            const msg = data.detail || data.message || 'Failed to switch mode';
            showToast(`Mode switch failed: ${msg}`, 'error');
        }
    } catch (e) {
        showToast(`Mode switch error: ${e.message}`, 'error');
    }
}

/**
 * Start the trading agent
 */
async function startAgent() {
    const modeLabel = currentTradingMode === 'live' ? 'LIVE (real money)' : 'PAPER (virtual)';
    const msg = currentTradingMode === 'live'
        ? 'Start LIVE trading agent?\n\n⚠️ This will place REAL orders on Upstox with REAL money.'
        : 'Start the AI Paper Trading Agent?\nVirtual money will be used — no real orders.';

    if (!confirm(msg)) {
        return;
    }

    const btn = document.getElementById('startAgentBtn');
    btn.disabled = true;
    btn.textContent = `⏳ Starting ${modeLabel}...`;

    try {
        // Pass the current mode so the backend launches the right type of agent
        const result = await fetch(`${BackendAPI.BASE_URL}/api/agent/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: currentTradingMode })
        });
        if (!result.ok) {
            const err = await result.json();
            throw new Error(err.detail || 'Failed to start');
        }
        showToast(`Trading agent started in ${modeLabel} mode!`, 'success');
        await loadAgentStatus();

    } catch (error) {
        showToast(`Failed to start agent: ${error.message}`, 'error');
        btn.disabled = false;
    }

    btn.textContent = '▶️ Start Agent';
}

/**
 * Stop the trading agent
 */
async function stopAgent() {
    if (!confirm('Are you sure you want to stop the AI Trading Agent?')) {
        return;
    }

    const btn = document.getElementById('stopAgentBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Stopping...';

    try {
        const result = await BackendAPI.stopAgent();
        showToast('Trading agent stopped', 'info');
        await loadAgentStatus();

    } catch (error) {
        showToast(`Failed to stop agent: ${error.message}`, 'error');
    }

    btn.textContent = '⏹️ Stop Agent';
    btn.disabled = true;
}

/**
 * Get AI prediction for selected stock
 */
async function getAIPrediction() {
    const select = document.getElementById('stockSelect');
    const symbol = select.value;
    const btn = document.getElementById('getPredictionBtn');
    const resultDiv = document.getElementById('predictionResult');

    btn.disabled = true;
    btn.textContent = '⏳ Analyzing...';

    try {
        const prediction = await BackendAPI.getAIPrediction(symbol);

        // Display result
        resultDiv.style.display = 'flex';

        const signalEl = document.getElementById('predictionSignal');
        signalEl.textContent = prediction.signal;
        signalEl.className = `prediction-signal ${prediction.signal.toLowerCase()}`;

        document.getElementById('predictionConfidence').textContent =
            `${(prediction.confidence * 100).toFixed(0)}%`;

        document.getElementById('predictedPrice').textContent =
            prediction.predicted_price ? `₹${prediction.predicted_price.toFixed(2)}` : 'N/A';

        document.getElementById('predictionModels').textContent =
            prediction.models_used.join(', ') || 'Strategy Ensemble';

        document.getElementById('predictionReason').textContent = prediction.reason;

        showToast('AI prediction generated!', 'success');

    } catch (error) {
        showToast(`Prediction failed: ${error.message}`, 'error');
        resultDiv.style.display = 'none';
    }

    btn.disabled = false;
    btn.textContent = 'Get AI Prediction';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}
