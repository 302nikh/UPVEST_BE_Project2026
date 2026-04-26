/* ============================================
   UPV EST - AI Investment Agent Dashboard JavaScript
   Handles agent controls, portfolio updates, and transactions
   ============================================ */

// Backend URL — single source of truth
const BACKEND_URL = (typeof CONFIG !== 'undefined' && CONFIG.BACKEND_API && CONFIG.BACKEND_API.BASE_URL)
    ? CONFIG.BACKEND_API.BASE_URL
    : 'http://localhost:5000';

// Global state
let isConnected = false;
let isAgentRunning = false;  // renamed from isBotRunning
let isBotRunning = false;    // backward-compat alias (kept for safety)
let isPaperTrading = true;
let statusPollInterval = null;
let transactionRefreshInterval = null;

/**
 * Initialize Dashboard
 */
async function init() {
    console.log('Initializing AI Investment Agent Dashboard...');

    // Set up event listeners safely
    try {
        const form = document.getElementById('dematForm');
        if (form) form.addEventListener('submit', handleConnect);
        const toggle = document.getElementById('tradingModeToggle');
        if (toggle) toggle.addEventListener('change', handleModeToggle);
    } catch (e) { console.error('Event listener setup error:', e); }

    // Each step is wrapped in try-catch so one failure doesn't break others
    try { await checkConnection(); } catch (e) { console.log('checkConnection skipped:', e.message); }
    try { await checkAgentStatus(); } catch (e) { console.log('checkAgentStatus skipped:', e.message); }
    try { await loadTradingMode(); } catch (e) { console.log('loadTradingMode skipped:', e.message); }
    try { await loadPortfolioData(); } catch (e) { console.log('loadPortfolioData skipped:', e.message); }
    try { await loadTransactions(); } catch (e) { console.log('loadTransactions skipped:', e.message); }
    try { await loadRiskStatus(); } catch (e) { console.log('loadRiskStatus skipped:', e.message); }
    try { await loadTelegramConfig(); } catch (e) { console.log('loadTelegramConfig skipped:', e.message); }

    // Start status polling
    startStatusPolling();

    // Check token expiry after a short delay (backend needs to be ready)
    setTimeout(checkTokenExpiry, 2500);

    console.log('Dashboard initialized');
}

/**
 * Handle account connection
 */
async function handleConnect(e) {
    console.log('[CONNECT] Function started, event:', e);
    if (e) e.preventDefault();

    const apiKey = document.getElementById('apiKey')?.value.trim();
    const apiSecret = document.getElementById('apiSecret')?.value.trim();
    const broker = document.getElementById('brokerSelect')?.value;

    console.log('[CONNECT] Form values - API Key:', apiKey ? 'present' : 'missing', 'Secret:', apiSecret ? 'present' : 'missing', 'Broker:', broker);

    if (!apiKey || !apiSecret || !broker) {
        alert('Please enter API Key, API Secret and select broker');
        return;
    }

    if (broker !== 'upstox') {
        alert('Only Upstox is supported currently');
        return;
    }

    const connectBtn = document.getElementById('connectBtn');
    connectBtn.disabled = true;
    connectBtn.innerHTML = '<span>Connecting...</span>';
    console.log('[CONNECT] Button disabled, starting connection process');

    try {
        // Save credentials to localStorage
        localStorage.setItem('upstox_api_key', apiKey);
        localStorage.setItem('upstox_api_secret', apiSecret);
        console.log('[CONNECT] Saved to localStorage');

        // Call backend configure endpoint
        const redirectUri = BACKEND_URL + '/api/auth/callback';
        const configUrl = BACKEND_URL + '/api/auth/configure';

        console.log('[CONNECT] Calling:', configUrl);

        const configResponse = await fetch(configUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKey,
                api_secret: apiSecret,
                redirect_uri: redirectUri
            })
        });

        console.log('[CONNECT] Response received, status:', configResponse.status, 'OK?', configResponse.ok);

        if (!configResponse.ok) {
            const errData = await configResponse.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('[CONNECT] Error response:', errData);
            throw new Error(errData.detail || 'Failed to configure authentication');
        }

        const configData = await configResponse.json();
        console.log('[CONNECT] Success! Response data:', configData);

        if (!configData.auth_url) {
            console.error('[CONNECT] No auth_url in response!');
            throw new Error('No authentication URL received from server');
        }

        console.log('[CONNECT] Auth URL received:', configData.auth_url);
        console.log('[CONNECT] Opening Upstox in new tab...');

        // Open in new tab instead of redirecting same tab
        window.open(configData.auth_url, '_blank');

        // Show success message since page stays open
        alert('Upstox login opened in a new tab. Please complete the authentication there. After logging in, you can close that tab and refresh this page.');

    } catch (error) {
        console.error('[CONNECT] ERROR:', error);
        alert('Connection failed: ' + error.message);
        connectBtn.disabled = false;
        connectBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="white" stroke-width="2" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="white" stroke-width="2" />
            </svg>
            Connect Demat Account
        `;
    }
}

/**
 * Update connection status UI
 */
function updateConnectionStatus(connected, broker = 'Upstox') {
    const statusEl = document.getElementById('connectionStatus');
    const formEl = document.getElementById('dematForm');
    const connectedEl = document.getElementById('connectedState');

    if (connected) {
        statusEl.innerHTML = `
            <span class="status-dot status-connected"></span>
            <span class="status-text">Connected</span>
        `;
        formEl.style.display = 'none';
        connectedEl.style.display = 'block';
        document.getElementById('connectedBroker').textContent = `${broker} Account Linked`;

        if (!document.getElementById('reloginBtn')) {
            const reloginBtn = document.createElement('button');
            reloginBtn.id = 'reloginBtn';
            reloginBtn.className = 'btn-relogin';
            reloginBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="10 17 15 12 10 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Open Upstox Login
            `;
            reloginBtn.onclick = () => {
                const apiKey = localStorage.getItem('upstox_api_key');
                if (apiKey) {
                    const getRedirectUri = () => {
                        if (typeof CONFIG !== 'undefined' && CONFIG.UPSTOX_REDIRECT_URI) {
                            return CONFIG.UPSTOX_REDIRECT_URI;
                        }
                        return 'http://localhost:5000/api/auth/callback';
                    };
                    const redirectUri = getRedirectUri();
                    window.open(`https://api-v2.upstox.com/login/authorization/dialog?response_type=code&client_id=${apiKey}&redirect_uri=${redirectUri}`, '_blank');
                } else {
                    alert('Please disconnect and reconnect to update credentials.');
                }
            };
            connectedEl.appendChild(reloginBtn);
        }

        startTransactionAutoRefresh();
    } else {
        statusEl.innerHTML = `
            <span class="status-dot status-disconnected"></span>
            <span class="status-text">Not Connected</span>
        `;
        formEl.style.display = 'flex';
        connectedEl.style.display = 'none';
    }
}

/**
 * Disconnect account
 */
async function disconnectAccount() {
    if (!confirm('Are you sure you want to disconnect your account?')) {
        return;
    }

    try {
        // Call backend disconnect endpoint
        const response = await fetch(`${BACKEND_URL}/api/auth/disconnect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to disconnect account');
        }

        const data = await response.json();

        if (data.success) {
            // Stop agent if running
            if (isAgentRunning) {
                await stopAgent();
            }

            // Clear saved credentials
            localStorage.removeItem('upstox_api_key');
            localStorage.removeItem('upstox_api_secret');

            isConnected = false;
            updateConnectionStatus(false);
            const agentBtn = document.getElementById('botControlBtn') || document.getElementById('agentControlBtn');
            if (agentBtn) agentBtn.disabled = true;

            // Hide transaction section
            const transactionSection = document.getElementById('transactionSection');
            if (transactionSection) {
                transactionSection.style.display = 'none';
            }

            showNotification('Account disconnected successfully', 'success');
        } else {
            throw new Error(data.message || 'Disconnect failed');
        }
    } catch (error) {
        console.error('Disconnect error:', error);
        showNotification('Failed to disconnect: ' + error.message, 'error');
    }
}

/**
 * Open Upstox dashboard in new tab
 */
function openUpstox() {
    window.open('https://pro.upstox.com', '_blank');
    console.log('[UPSTOX] Opening Upstox Pro dashboard in new tab');
}

/**
 * Handle trading mode toggle — calls backend to switch mode
 */
async function handleModeToggle(e) {
    const wantLive = !e.target.checked; // checked = paper, unchecked = live
    const toggle = e.target;

    // Revert toggle visually while we process
    toggle.disabled = true;

    try {
        if (wantLive) {
            // Require confirmation before going live
            const confirmed = confirm(
                'WARNING: You are switching to LIVE TRADING mode.\n\n' +
                'Real money from your Upstox account will be used for trades.\n\n' +
                'Are you sure you want to continue?'
            );
            if (!confirmed) {
                toggle.checked = true; // revert to paper
                toggle.disabled = false;
                return;
            }

            // Call backend with confirmed=true
            const res = await fetch(`${BACKEND_URL}/api/trading-mode/switch?mode=live&confirmed=true`, {
                method: 'POST'
            });
            const data = await res.json();

            if (!res.ok) {
                alert('Cannot switch to Live mode:\n' + (data.detail || data.message || 'Unknown error'));
                toggle.checked = true; // revert
                toggle.disabled = false;
                return;
            }

            isPaperTrading = false;
            updateModeUI('live');
            await loadPortfolioData();
            await loadTransactions();
            showNotification('Switched to LIVE TRADING — Real money active!', 'warning');

        } else {
            // Switch back to paper
            const res = await fetch(`${BACKEND_URL}/api/trading-mode/switch?mode=paper&confirmed=true`, {
                method: 'POST'
            });
            if (res.ok) {
                isPaperTrading = true;
                updateModeUI('paper');
                await loadPortfolioData();
                await loadTransactions();
                showNotification('Switched to Paper Trading (Virtual Money)', 'info');
            }
        }
    } catch (err) {
        console.error('[MODE TOGGLE] Error:', err);
        showNotification('Failed to switch mode: ' + err.message, 'error');
        // Revert toggle
        toggle.checked = !wantLive;
    } finally {
        toggle.disabled = false;
    }
}

/**
 * Update UI elements based on trading mode
 */
function updateModeUI(mode) {
    const modeText = document.getElementById('modeText');
    const liveWarning = document.getElementById('liveWarning');
    const riskPanel = document.getElementById('riskStatusPanel');

    const transactionSection = document.getElementById('transactionSection');

    if (mode === 'live') {
        if (modeText) {
            modeText.textContent = 'Live Trading';
            modeText.style.color = '#ef4444';
        }
        if (liveWarning) liveWarning.style.display = 'flex';
        if (riskPanel) riskPanel.style.display = 'block';
        if (transactionSection) transactionSection.style.display = 'none';
    } else {
        if (modeText) {
            modeText.textContent = 'Paper Trading';
            modeText.style.color = '#667eea';
        }
        if (liveWarning) liveWarning.style.display = 'none';
        if (riskPanel) riskPanel.style.display = 'none';
        if (transactionSection) transactionSection.style.display = 'block';
    }
}

/**
 * Update capital allocation label in real-time as slider moves
 */
function updateCapitalLabel(value) {
    const label = document.getElementById('capitalLabel');
    if (label) label.textContent = value + '%';
}

/**
 * Save capital allocation to backend
 */
async function saveCapitalAllocation() {
    const slider = document.getElementById('capitalSlider');
    const btn = document.getElementById('saveCapitalBtn');
    if (!slider) return;

    const pct = parseFloat(slider.value);
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const res = await fetch(`${BACKEND_URL}/api/trading-mode/capital?pct=${pct}`, {
            method: 'POST'
        });
        const data = await res.json();

        if (res.ok && data.success) {
            showNotification(`Capital allocation set to ${pct}%`, 'success');
        } else {
            showNotification('Failed to save: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (err) {
        showNotification('Error saving capital allocation: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save';
    }
}

/**
 * Load trading mode and capital allocation from backend on page init
 */
async function loadTradingMode() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/trading-mode`);
        if (!res.ok) return;
        const data = await res.json();

        const mode = data.mode || 'paper';
        const capitalPct = data.capital_allocation_pct || 100;

        // Update toggle
        const toggle = document.getElementById('tradingModeToggle');
        if (toggle) toggle.checked = (mode === 'paper');

        // Update slider
        const slider = document.getElementById('capitalSlider');
        if (slider) slider.value = capitalPct;
        updateCapitalLabel(capitalPct);

        // Update mode UI
        isPaperTrading = (mode === 'paper');
        updateModeUI(mode);

        console.log(`[MODE] Loaded: ${mode.toUpperCase()} | Capital: ${capitalPct}%`);
    } catch (err) {
        console.warn('[MODE] Could not load trading mode:', err.message);
    }
}

/**
 * Load and display risk status
 */
async function loadRiskStatus() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/risk/status`);
        if (!res.ok) return;
        const data = await res.json();

        const tradesToday = document.getElementById('riskTradesToday');
        const circuitBreaker = document.getElementById('riskCircuitBreaker');

        if (tradesToday) tradesToday.textContent = `${data.trades_today || 0}/20`;
        if (circuitBreaker) {
            const active = data.circuit_breaker_active;
            circuitBreaker.textContent = active ? 'TRIGGERED' : 'OK';
            circuitBreaker.className = 'risk-value ' + (active ? 'risk-danger' : 'risk-ok');
        }
    } catch (err) {
        // Silently fail — risk status is non-critical
    }
}

/**
 * Toggle agent (Start/Stop)
 */
// toggleAgent is defined below as toggleBot (they are the same function)

/**
 * Start trading agent
 */
async function startAgent() {
    if (!isConnected) {
        showNotification('Please connect your account first', 'error');
        return;
    }

    try {
        const response = await BackendAPI.request('/api/agent/start', {
            method: 'POST',
            body: JSON.stringify({
                mode: isPaperTrading ? 'paper' : 'live'
            })
        });

        if (response.success !== false) {
            isAgentRunning = true;
            isBotRunning = true;  // keep alias in sync
            updateBotStatus(true);
            showNotification('AI Agent started successfully!', 'success');

            // Immediately begin polling/refreshing
            loadPortfolioData();
            loadTransactions();
        } else {
            throw new Error(response.message || 'Failed to start AI Agent');
        }
    } catch (error) {
        console.error('Failed to start AI Agent:', error);
        showNotification('Failed to start AI Agent: ' + error.message, 'error');
    }
}

/**
 * Stop trading agent
 */
async function stopAgent() {
    if (!confirm('Are you sure you want to stop the AI Agent?')) {
        return;
    }

    try {
        const response = await BackendAPI.request('/api/agent/stop', {
            method: 'POST'
        });

        if (response.success !== false) {
            isAgentRunning = false;
            isBotRunning = false;  // keep alias in sync
            updateBotStatus(false);

            if (response.status === 'stopping') {
                showNotification('Stop signal sent. Squares off positions & exiting...', 'info');
            } else {
                showNotification('AI Agent stopped successfully', 'info');
            }

            // Refresh data one last time after a short delay to show final state
            setTimeout(() => {
                loadPortfolioData();
                loadTransactions();
            }, 3000);

        } else {
            // handle case where agent was already stopped
            if (response.message && response.message.toLowerCase().includes('not currently running')) {
                isAgentRunning = false;
                isBotRunning = false;
                updateBotStatus(false);
                showNotification(response.message, 'info');
            } else {
                throw new Error(response.message || 'Failed to stop AI Agent');
            }
        }
    } catch (error) {
        console.error('Failed to stop AI Agent:', error);
        showNotification('Failed to stop AI Agent: ' + error.message, 'error');
    }
}

/**
 * Toggle agent start/stop — called by botControlBtn onclick="toggleBot()"
 * Delegates to startAgent() or stopAgent() based on current state.
 */
async function toggleBot() {
    if (isAgentRunning) {
        await stopAgent();
    } else {
        await startAgent();
    }
}

// Alias for forward-compat
var toggleAgent = toggleBot;

/**
 * Update agent status UI
 */
function updateBotStatus(running) {
    const btn = document.getElementById('botControlBtn');
    const status = document.getElementById('botStatus');

    if (running) {
        btn.className = 'btn-bot-stop';
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="white" />
                <rect x="14" y="4" width="4" height="16" fill="white" />
            </svg>
            STOP TRADING
        `;
        status.innerHTML = `
            <span class="status-dot status-running"></span>
            <span>Agent Running</span>
        `;
    } else {
        btn.className = 'btn-bot-start';
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <polygon points="5 3 19 12 5 21 5 3" fill="white" />
            </svg>
            START TRADING
        `;
        status.innerHTML = `
            <span class="status-dot status-stopped"></span>
            <span>Agent Stopped</span>
        `;
    }
}

/**
 * Check agent status from backend
 */
async function checkAgentStatus() {
    try {
        const response = await BackendAPI.request('/api/agent/status');
        if (response.success !== false) {
            isAgentRunning = response.running || false;
            isBotRunning = isAgentRunning;  // keep alias in sync
            updateBotStatus(isAgentRunning);
        }
    } catch (error) {
        console.log('Agent status check failed (backend may not be running)');
    }
}

/**
 * Load portfolio data
 */
async function loadPortfolioData() {
    try {
        // Paper mode should show paper portfolio values, while live mode shows the connected Upstox account.
        const endpoint = isPaperTrading ? '/api/paper/portfolio' : '/api/portfolio';
        const response = await BackendAPI.request(endpoint);

        if (response && response.balance !== undefined) {
            updatePortfolioUI(response);
        } else if (response.success) {
            // some other endpoints might still use success: true wrapper
            updatePortfolioUI(response);
        } else {
            // directly pass response as it contains the fields
            updatePortfolioUI(response);
        }
    } catch (error) {
        console.log('Portfolio data not available:', error);
        // Set default values
        updatePortfolioUI({
            total_invested: 0,
            current_value: 0,
            total_returns: 0
        });
    }
}

/**
 * Update portfolio UI
 */
function updatePortfolioUI(data) {
    const totalInvested = (data.total_invested !== undefined && data.total_invested !== null && data.total_invested !== 0)
        ? data.total_invested
        : data.initial_capital || 0;
    const currentValue = data.current_value ?? data.cash ?? data.initial_capital ?? 0;
    const returns = data.total_returns ?? data.pnl ?? (currentValue - totalInvested);

    document.getElementById('totalInvested').textContent = `₹${formatNumber(totalInvested)}`;
    document.getElementById('currentValue').textContent = `₹${formatNumber(currentValue)}`;

    const returnsEl = document.getElementById('totalReturns');
    returnsEl.textContent = `₹${returns >= 0 ? '+' : ''}${formatNumber(returns)}`;
    returnsEl.style.color = returns >= 0 ? '#10b981' : '#ef4444';
}

/**
 * Load recent transactions
 */
async function loadTransactions() {
    try {
        // Show paper trading transactions for now.
        // The toggle only changes the dashboard display mode, not the transaction history source.
        const response = await BackendAPI.request('/api/paper/trades?limit=10');

        if (response.success) {
            updateTransactionsTable(response.trades || []);
        } else {
            updateTransactionsTable([]);
        }
    } catch (error) {
        console.log('Transactions not available:', error);
        updateTransactionsTable([]);
    }
}

/**
 * Update transactions table with P&L support
 */
function updateTransactionsTable(trades, portfolio = null) {
    const tbody = document.getElementById('recentTransactionsBody');

    if (!tbody) {
        return;
    }

    if (!trades || trades.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="7">
                    <div class="empty-message">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                            <rect x="3" y="3" width="18" height="18" rx="2" stroke="#cbd5e1" stroke-width="2" />
                            <path d="M9 12h6M12 9v6" stroke="#cbd5e1" stroke-width="2" />
                        </svg>
                        <p>No transactions yet. Start trading to see activity.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = trades.map(trade => {
        const timestamp = new Date(trade.timestamp);
        const dateStr = timestamp.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
        const timeStr = timestamp.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        
        const side = (trade.side || trade.signal || '?').toUpperCase();
        const sideClass = side === 'BUY' ? 'buy' : 'sell';
        
        // Calculate amount
        const amount = trade.cost || trade.proceeds || (trade.qty * trade.price) || (trade.quantity * trade.price);
        const qty = trade.qty || trade.quantity || 0;

        // P&L Logic
        let displayPnl = trade.pnl;
        
        // Live P&L for open BUY positions (Paper Trading)
        if (side === 'BUY' && displayPnl == null && portfolio && portfolio.positions) {
            const currentPos = portfolio.positions.find(p => p.symbol === (trade.symbol || trade.ticker));
            if (currentPos) {
                displayPnl = (currentPos.current_price - trade.price) * qty;
            }
        }

        const pnlText = displayPnl != null ?
            `₹${Math.abs(displayPnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` :
            '-';
        const pnlClass = displayPnl > 0 ? 'positive' : displayPnl < 0 ? 'negative' : '';

        return `
            <tr>
                <td>${dateStr} ${timeStr}</td>
                <td><strong>${trade.stock_name || trade.symbol || trade.ticker}</strong></td>
                <td><span class="side ${sideClass}">${side}</span></td>
                <td>${qty}</td>
                <td>₹${trade.price?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}</td>
                <td>₹${amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}</td>
                <td><span class="pnl ${pnlClass}">${pnlText}</span></td>
            </tr>
        `;
    }).join('');
}

/**
 * Check connection status
 */
async function checkConnection() {
    try {
        // Check backend auth status first (real source of truth)
        const res = await fetch(`${BACKEND_URL}/api/auth/status`);
        if (res.ok) {
            const data = await res.json();
            if (data.connected) {
                isConnected = true;
                updateConnectionStatus(true, data.broker || 'Upstox');
                const agentBtn = document.getElementById('botControlBtn');
                if (agentBtn) agentBtn.disabled = false;
                return;
            }
        }
    } catch (e) {
        console.log('Backend auth check failed, falling back to localStorage');
    }

    // Fallback: check localStorage for saved connection
    try {
        const savedConnection = Utils.loadFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION);
        if (savedConnection && savedConnection.connected) {
            isConnected = true;
            updateConnectionStatus(true, savedConnection.broker || 'Upstox');
            const agentBtn = document.getElementById('botControlBtn');
            if (agentBtn) agentBtn.disabled = false;
        }
    } catch (e) {
        console.log('localStorage check failed:', e.message);
    }
}

/**
 * Start status polling
 */
function startStatusPolling() {
    // Poll every 5 seconds
    statusPollInterval = setInterval(async () => {
        if (isBotRunning) {
            // previous versions used an undefined helper; use the real one
            await checkAgentStatus();
            await loadPortfolioData();
            if (isPaperTrading) {
                await loadPaperTradingTransactions();
            } else if (isConnected) {
                await loadTransactions();
            }
        }
    }, 5000);
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(num);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#667eea'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Load Trading Data (Paper or Live)
 */
async function loadTradingData() {
    try {
        if (isPaperTrading) {
            const response = await fetch(`${BACKEND_URL}/api/paper-trading/transactions?limit=20`);
            const data = await response.json();

            if (data.success) {
                // Update portfolio summary cards
                if (data.portfolio) {
                    const portfolio = data.portfolio;
                    document.getElementById('totalValue').textContent = `₹${portfolio.total_value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`;
                    document.getElementById('cashBalance').textContent = `₹${portfolio.cash?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`;

                    const pnlElement = document.getElementById('totalPnL');
                    const pnl = portfolio.total_pnl || 0;
                    pnlElement.textContent = `₹${pnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    pnlElement.className = `card-value pnl ${pnl >= 0 ? 'positive' : 'negative'}`;

                    const todaysPnlEl = document.getElementById('todaysPnL');
                    if (todaysPnlEl) {
                        const tpnl = portfolio.todays_pnl || 0;
                        todaysPnlEl.textContent = `₹${tpnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    }

                    // Update main stats if they exist
                    const totalTradesEl = document.getElementById('totalTrades');
                    if (totalTradesEl) totalTradesEl.textContent = portfolio.total_trades || 0;
                }

                // Update unified transactions table
                updateTransactionsTable(data.transactions || [], data.portfolio);
                
                // Update last update time
                const now = new Date();
                const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                const lastUpdateEl = document.getElementById('lastTransactionUpdate');
                if (lastUpdateEl) lastUpdateEl.textContent = timeStr;
            }
        } else if (isConnected) {
            await loadTransactions();
        }
    } catch (error) {
        console.error('Error loading trading data:', error);
    }
}

/**
 * Refresh transactions manually
 */
async function refreshTransactions() {
    const btn = event.target.closest('.btn-refresh');
    if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.6';
    }

    await loadTradingData();

    if (btn) {
        setTimeout(() => {
            btn.disabled = false;
            btn.style.opacity = '1';
        }, 1000);
    }
}

/**
 * Start auto-refresh for transactions when connected
 */
function startTransactionAutoRefresh() {
    if (transactionRefreshInterval) {
        return;
    }

    transactionRefreshInterval = setInterval(async () => {
        if (!isConnected && !isPaperTrading) {
            return;
        }

        await loadTradingData();
    }, 15000);

    loadTradingData();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await init();

    // Start auto-refresh if connected
    startTransactionAutoRefresh();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    if (transactionRefreshInterval) {
        clearInterval(transactionRefreshInterval);
    }
});

/**
 * Load saved Telegram config from backend on init
 */
async function loadTelegramConfig() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/telegram/config`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.bot_token) {
            document.getElementById('telegramBotToken').value = data.bot_token;
        }
        if (data.chat_id) {
            document.getElementById('telegramChatId').value = data.chat_id;
        }
        if (data.telegram_username) {
            document.getElementById('telegramUsername').value = data.telegram_username;
        }

        const statusEl = document.getElementById('telegramStatus');
        const summaryEl = document.getElementById('telegramSummary');
        const formEl = document.getElementById('telegramFormContainer');

        if (data.enabled) {
            statusEl.textContent = 'Enabled';
            statusEl.className = 'status-badge status-badge-on';
            if (summaryEl && formEl) {
                summaryEl.style.display = 'block';
                formEl.style.display = 'none';
                const details = [];
                if (data.telegram_username) {
                    details.push(`Receiver: ${data.telegram_username}`);
                }
                if (data.chat_id) {
                    details.push(`Chat ID: ${data.chat_id}`);
                }
                document.getElementById('telegramConfigDetails').textContent = details.join(' • ');

                const openBtn = document.getElementById('openTelegramChatBtn');
                if (openBtn) {
                    if (data.telegram_username) {
                        openBtn.style.display = 'inline-flex';
                    } else {
                        openBtn.style.display = 'none';
                    }
                }
            }
        } else {
            if (summaryEl && formEl) {
                summaryEl.style.display = 'none';
                formEl.style.display = 'block';
            }
        }
    } catch (e) {
        // Silently fail — Telegram config is optional
    }
}

function showTelegramConfigForm() {
    const summaryEl = document.getElementById('telegramSummary');
    const formEl = document.getElementById('telegramFormContainer');
    if (summaryEl && formEl) {
        summaryEl.style.display = 'none';
        formEl.style.display = 'block';
    }
}

function openTelegramChat() {
    const username = document.getElementById('telegramUsername')?.value?.trim();
    if (!username) {
        showTelegramMsg('No Telegram username configured to open.', 'error');
        return;
    }
    const normalized = username.startsWith('@') ? username.slice(1) : username;
    window.open(`https://t.me/${normalized}`, '_blank');
}

/**
 * Save Telegram bot token and chat ID to backend
 */
async function saveTelegramConfig() {
    const token = document.getElementById('telegramBotToken')?.value.trim();
    const chatId = document.getElementById('telegramChatId')?.value.trim();
    const msgEl = document.getElementById('telegramMsg');
    const btn = document.getElementById('saveTelegramBtn');

    if (!token || !chatId) {
        showTelegramMsg('Please enter both Bot Token and Chat ID.', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
        const telegramUsername = document.getElementById('telegramUsername')?.value.trim();
        const res = await fetch(`${BACKEND_URL}/api/telegram/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bot_token: token, chat_id: chatId, telegram_username: telegramUsername })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            showTelegramMsg('✅ Telegram config saved!', 'success');
            document.getElementById('telegramStatus').textContent = 'Enabled';
            document.getElementById('telegramStatus').className = 'status-badge status-badge-on';
            await loadTelegramConfig();
        } else {
            showTelegramMsg('❌ Failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        showTelegramMsg('❌ Error: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Config';
    }
}

/**
 * Send a test Telegram message to verify config
 */
async function testTelegramConfig() {
    const btn = document.getElementById('testTelegramBtn');
    btn.disabled = true;
    btn.textContent = 'Sending...';

    try {
        const res = await fetch(`${BACKEND_URL}/api/telegram/test`, { method: 'POST' });
        const data = await res.json();

        if (res.ok && data.success) {
            showTelegramMsg('✅ Test message sent! Check your Telegram.', 'success');
        } else {
            showTelegramMsg('❌ Failed: ' + (data.detail || data.message || 'Check your token/chat ID'), 'error');
        }
    } catch (e) {
        showTelegramMsg('❌ Error: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Send Test Message';
    }
}

function showTelegramMsg(msg, type) {
    const el = document.getElementById('telegramMsg');
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.style.color = type === 'success' ? '#10b981' : '#ef4444';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

// ============================================================
//  FIX #2 — TOKEN EXPIRY WARNING
// ============================================================

/**
 * Check if Upstox token is still valid and show warning if expiring/expired.
 * Called on page load and every 30 minutes.
 */
async function checkTokenExpiry() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/auth/token-status`);
        if (!res.ok) return;
        const data = await res.json();

        // Remove any existing banner
        const existing = document.getElementById('tokenExpiryBanner');
        if (existing) existing.remove();

        if (data.needs_relogin || (data.expires_in_hours !== null && data.expires_in_hours < 2)) {
            // Show warning banner
            const banner = document.createElement('div');
            banner.id = 'tokenExpiryBanner';
            banner.style.cssText = `
                position: fixed; top: 70px; left: 50%; transform: translateX(-50%);
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white; padding: 12px 24px; border-radius: 12px;
                display: flex; align-items: center; gap: 12px;
                box-shadow: 0 4px 20px rgba(245,158,11,0.4);
                z-index: 9999; font-size: 0.9rem; font-weight: 500;
                animation: slideDown 0.3s ease;
            `;

            const msg = data.needs_relogin
                ? '⚠️ Your Upstox token has expired. Re-login required to continue trading.'
                : `⚠️ Upstox token expires in ${data.expires_in_hours}h. Re-login soon.`;

            banner.innerHTML = `
                <span>${msg}</span>
                <button onclick="triggerRelogin()" style="
                    background: white; color: #d97706; border: none;
                    padding: 6px 14px; border-radius: 8px; cursor: pointer;
                    font-weight: 600; font-size: 0.85rem;">
                    Re-login to Upstox
                </button>
                <button onclick="document.getElementById('tokenExpiryBanner').remove()" style="
                    background: transparent; color: white; border: 1px solid rgba(255,255,255,0.5);
                    padding: 6px 10px; border-radius: 8px; cursor: pointer; font-size: 0.8rem;">
                    Dismiss
                </button>
            `;
            document.body.appendChild(banner);
        }
    } catch (e) {
        // Silently fail — token check is non-critical
    }
}

/**
 * Open Upstox login in new tab for token refresh.
 */
function triggerRelogin() {
    const apiKey = localStorage.getItem('upstox_api_key');
    if (apiKey) {
        const redirectUri = `${BACKEND_URL}/api/auth/callback`;
        window.open(
            `https://api-v2.upstox.com/login/authorization/dialog?response_type=code&client_id=${apiKey}&redirect_uri=${encodeURIComponent(redirectUri)}`,
            '_blank'
        );
        showNotification('Upstox login opened in new tab. After logging in, refresh this page.', 'info');
    } else {
        showNotification('Please disconnect and reconnect your account first.', 'error');
    }
}

// ============================================================
//  FIX #4 — EXCEL DOWNLOAD
// ============================================================

/**
 * Trigger Excel export and show download info.
 */
async function downloadExcel() {
    const btn = document.getElementById('downloadExcelBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Exporting...';
    }

    try {
        const res = await fetch(`${BACKEND_URL}/api/export/download`);
        const data = await res.json();

        if (data.success) {
            showNotification(
                `Excel exported: ${data.filename}. Check data/exports/ folder.`,
                'success'
            );
            // Also check for latest export info
            const latestRes = await fetch(`${BACKEND_URL}/api/export/latest`);
            const latestData = await latestRes.json();
            if (latestData.exists) {
                const infoEl = document.getElementById('exportInfo');
                if (infoEl) {
                    infoEl.textContent = `Last export: ${latestData.filename} (${latestData.size_kb}KB) — ${latestData.modified}`;
                    infoEl.style.display = 'block';
                }
            }
        } else {
            showNotification(data.message || 'No data to export yet', 'error');
        }
    } catch (e) {
        showNotification('Export failed: ' + e.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Download Excel';
        }
    }
}

// ============================================================
//  INIT HOOK — Wire up new features on page load
// ============================================================

// Extend the existing init() to also run new checks
const _originalInit = typeof init === 'function' ? init : null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check token expiry on load
    setTimeout(checkTokenExpiry, 2000);

    // Re-check every 30 minutes
    setInterval(checkTokenExpiry, 30 * 60 * 1000);

    // Start transaction auto-refresh
    startTransactionAutoRefresh();

    // Listen for agent state changes to start/stop refresh
    setInterval(() => {
        if (isAgentRunning && !transactionRefreshInterval) {
            startTransactionAutoRefresh();
        }
    }, 5000);
});
