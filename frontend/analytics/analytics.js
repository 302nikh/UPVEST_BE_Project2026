/* ============================================
   UPVEST Analytics Dashboard — JavaScript
   Fetches data from /api/analytics/* endpoints
   and renders charts + tables.
   ============================================ */

// Read backend URL from central config (frontend/core/config.js)
const BACKEND_URL = (typeof CONFIG !== 'undefined' && CONFIG.BACKEND_API)
    ? CONFIG.BACKEND_API.BASE_URL
    : 'http://localhost:5000';
let currentPeriod = 30;
let rawDayData = [];
let sortState = { col: 'date', dir: -1 };

// Chart instances (kept for destroy/re-render)
let chartPnl = null;
let chartWinRate = null;
let chartEquity = null;
let chartDist = null;

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
});

async function refreshAll() {
    const btn = document.getElementById('refreshBtn');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        await Promise.all([
            loadPerformanceMetrics(),
            loadDailyAnalytics(),
            loadStrategyPerformance()
        ]);
        document.getElementById('lastUpdated').textContent =
            'Last updated: ' + new Date().toLocaleTimeString('en-IN');
    } catch (e) {
        console.error('[ANALYTICS] Refresh error:', e);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function changePeriod(days) {
    currentPeriod = parseInt(days);
    refreshAll();
}

// ─── Performance Metrics ──────────────────────────────────────────────────────
async function loadPerformanceMetrics() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/performance?days=${currentPeriod}`);
        if (!res.ok) return;
        const data = await res.json();

        // Total P&L
        const pnl = data.total_pnl || 0;
        const pnlEl = document.getElementById('totalPnl');
        pnlEl.textContent = formatCurrency(pnl);
        pnlEl.className = 'kpi-value ' + (pnl >= 0 ? 'positive' : 'negative');
        document.getElementById('avgDailyPnl').textContent =
            `Avg daily: ${formatCurrency(data.avg_daily_pnl || 0)}`;

        // Sharpe Ratio
        const sharpe = data.sharpe_ratio || 0;
        const sharpeEl = document.getElementById('sharpeRatio');
        sharpeEl.textContent = sharpe.toFixed(2);
        sharpeEl.className = 'kpi-value ' + (sharpe >= 1 ? 'positive' : sharpe < 0 ? 'negative' : '');
        document.getElementById('sharpeLabel').textContent =
            sharpe >= 2 ? 'Excellent' : sharpe >= 1 ? 'Good' : sharpe >= 0 ? 'Fair' : 'Poor';

        // Max Drawdown
        document.getElementById('maxDrawdown').textContent =
            `-${(data.max_drawdown_pct || 0).toFixed(1)}%`;

        // Win Rate
        const wr = data.win_rate_pct || 0;
        const wrEl = document.getElementById('winRate');
        wrEl.textContent = `${wr.toFixed(1)}%`;
        wrEl.className = 'kpi-value ' + (wr >= 55 ? 'positive' : wr < 45 ? 'negative' : '');
        document.getElementById('winRateSub').textContent =
            `${data.winning_days || 0}W / ${data.losing_days || 0}L`;

        // Total Trades
        document.getElementById('totalTrades').textContent = data.total_trades || 0;
        document.getElementById('tradesSub').textContent = `Over ${currentPeriod} days`;

        // Best / Worst Day
        const best = data.best_day_pnl || 0;
        const worst = data.worst_day_pnl || 0;
        document.getElementById('bestDay').textContent = formatCurrency(best);
        document.getElementById('worstDay').textContent = `Worst: ${formatCurrency(worst)}`;

    } catch (e) {
        console.warn('[ANALYTICS] Performance metrics error:', e);
    }
}

// ─── Daily Analytics ──────────────────────────────────────────────────────────
async function loadDailyAnalytics() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/daily?days=${currentPeriod}`);
        if (!res.ok) return;
        const json = await res.json();
        rawDayData = json.data || [];

        renderDailyPnlChart(rawDayData);
        renderWinRateChart(rawDayData);
        renderEquityChart(rawDayData);
        renderTradeDistChart(rawDayData);
        renderDailyTable(rawDayData);

    } catch (e) {
        console.warn('[ANALYTICS] Daily analytics error:', e);
        // Render empty state
        renderDailyTable([]);
    }
}

// ─── Strategy Performance ─────────────────────────────────────────────────────
async function loadStrategyPerformance() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/strategies`);
        if (!res.ok) return;
        const json = await res.json();
        renderStrategyTable(json.strategies || []);
    } catch (e) {
        console.warn('[ANALYTICS] Strategy performance error:', e);
        renderStrategyTable([]);
    }
}

// ─── Chart Renderers ──────────────────────────────────────────────────────────

function renderDailyPnlChart(data) {
    const ctx = document.getElementById('dailyPnlChart').getContext('2d');
    if (chartPnl) chartPnl.destroy();

    const labels = data.map(d => formatDateShort(d.date));
    const values = data.map(d => d.total_pnl || 0);
    const colors = values.map(v => v >= 0 ? 'rgba(16,185,129,0.8)' : 'rgba(239,68,68,0.8)');
    const borders = values.map(v => v >= 0 ? '#10b981' : '#ef4444');

    chartPnl = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Daily P&L (₹)',
                data: values,
                backgroundColor: colors,
                borderColor: borders,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: chartOptions('₹')
    });
}

function renderWinRateChart(data) {
    const ctx = document.getElementById('winRateChart').getContext('2d');
    if (chartWinRate) chartWinRate.destroy();

    const labels = data.map(d => formatDateShort(d.date));
    const values = data.map(d => d.win_rate_pct || 0);

    chartWinRate = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Win Rate (%)',
                data: values,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245,158,11,0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#f59e0b'
            }]
        },
        options: chartOptions('%')
    });
}

function renderEquityChart(data) {
    const ctx = document.getElementById('equityChart').getContext('2d');
    if (chartEquity) chartEquity.destroy();

    const labels = data.map(d => formatDateShort(d.date));
    const values = data.map(d => d.ending_balance || 0).filter(v => v > 0);
    const labelsFiltered = labels.slice(labels.length - values.length);

    chartEquity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labelsFiltered,
            datasets: [{
                label: 'Portfolio Value (₹)',
                data: values,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102,126,234,0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointBackgroundColor: '#667eea'
            }]
        },
        options: chartOptions('₹')
    });
}

function renderTradeDistChart(data) {
    const ctx = document.getElementById('tradeDistChart').getContext('2d');
    if (chartDist) chartDist.destroy();

    const totalBuy = data.reduce((s, d) => s + (d.buy_trades || 0), 0);
    const totalSell = data.reduce((s, d) => s + (d.sell_trades || 0), 0);
    const totalAI = data.reduce((s, d) => s + (d.ai_trades || 0), 0);
    const totalRule = data.reduce((s, d) => s + (d.rule_based_trades || 0), 0);

    chartDist = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Buy', 'Sell', 'AI', 'Rule-based'],
            datasets: [{
                data: [totalBuy, totalSell, totalAI, totalRule],
                backgroundColor: [
                    'rgba(16,185,129,0.8)',
                    'rgba(239,68,68,0.8)',
                    'rgba(102,126,234,0.8)',
                    'rgba(245,158,11,0.8)'
                ],
                borderColor: ['#10b981', '#ef4444', '#667eea', '#f59e0b'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', font: { size: 11 }, padding: 12 }
                }
            },
            cutout: '65%'
        }
    });
}

function chartOptions(unit) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#1a2035',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                callbacks: {
                    label: ctx => `${unit === '₹' ? '₹' : ''}${ctx.parsed.y?.toLocaleString('en-IN') || 0}${unit === '%' ? '%' : ''}`
                }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 10 }
            },
            y: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: {
                    color: '#64748b',
                    font: { size: 10 },
                    callback: v => unit === '₹' ? `₹${(v / 1000).toFixed(0)}k` : `${v}%`
                }
            }
        }
    };
}

// ─── Table Renderers ──────────────────────────────────────────────────────────

function renderDailyTable(data) {
    const tbody = document.getElementById('analyticsTableBody');

    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" style="text-align:center;padding:40px;color:#64748b;">
                No analytics data available. Start trading to see day-wise results.
            </td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(d => {
        const pnl = d.total_pnl || 0;
        const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        const pnlSign = pnl >= 0 ? '+' : '';
        const wr = d.win_rate_pct || 0;
        const balance = d.ending_balance || 0;

        return `
        <tr>
            <td><strong>${formatDateFull(d.date)}</strong></td>
            <td class="${pnlClass}">${pnlSign}${formatCurrency(pnl)}</td>
            <td>${d.total_trades || 0}</td>
            <td>
                <span class="badge badge-buy">${d.buy_trades || 0} B</span>
                <span class="badge badge-sell">${d.sell_trades || 0} S</span>
            </td>
            <td>
                <div class="win-rate-bar">
                    <div class="win-rate-track">
                        <div class="win-rate-fill" style="width:${wr}%"></div>
                    </div>
                    <span>${wr.toFixed(0)}%</span>
                </div>
            </td>
            <td>${d.ai_trades || 0}</td>
            <td>${balance > 0 ? formatCurrency(balance) : '—'}</td>
        </tr>`;
    }).join('');
}

function renderStrategyTable(strategies) {
    const tbody = document.getElementById('strategyTableBody');

    if (!strategies || strategies.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" style="text-align:center;padding:40px;color:#64748b;">
                No strategy data available yet.
            </td></tr>`;
        return;
    }

    tbody.innerHTML = strategies.map(s => {
        const pnl = s.total_pnl || 0;
        const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
        const wr = s.win_rate_pct || 0;
        const wrColor = wr >= 55 ? '#10b981' : wr < 45 ? '#ef4444' : '#f59e0b';

        return `
        <tr>
            <td><strong>${s.strategy}</strong></td>
            <td>${s.total_trades}</td>
            <td style="color:${wrColor};font-weight:600">${wr.toFixed(1)}%</td>
            <td class="${pnlClass}">${pnl >= 0 ? '+' : ''}${formatCurrency(pnl)}</td>
            <td>${formatCurrency(s.avg_pnl_per_trade || 0)}</td>
            <td class="pnl-positive">+${formatCurrency(s.best_trade || 0)}</td>
            <td class="pnl-negative">${formatCurrency(s.worst_trade || 0)}</td>
        </tr>`;
    }).join('');
}

// ─── Table Sort & Filter ──────────────────────────────────────────────────────

function sortTable(col) {
    if (sortState.col === col) {
        sortState.dir *= -1;
    } else {
        sortState.col = col;
        sortState.dir = -1;
    }

    const sorted = [...rawDayData].sort((a, b) => {
        const av = a[col] ?? '';
        const bv = b[col] ?? '';
        if (typeof av === 'number') return (av - bv) * sortState.dir;
        return String(av).localeCompare(String(bv)) * sortState.dir;
    });

    renderDailyTable(sorted);
}

function filterTable(query) {
    const q = query.toLowerCase();
    const filtered = rawDayData.filter(d =>
        d.date?.toLowerCase().includes(q)
    );
    renderDailyTable(filtered);
}

// ─── Formatters ───────────────────────────────────────────────────────────────

function formatCurrency(val) {
    const abs = Math.abs(val);
    const sign = val < 0 ? '-' : '';
    if (abs >= 100000) return `${sign}₹${(abs / 100000).toFixed(2)}L`;
    if (abs >= 1000) return `${sign}₹${(abs / 1000).toFixed(1)}K`;
    return `${sign}₹${abs.toFixed(0)}`;
}

function formatDateShort(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

function formatDateFull(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}
