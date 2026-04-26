/* ============================================
   UPVEST - Dashboard JavaScript
   Main dashboard functionality
   ============================================ */

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!Navigation.initProtectedPage()) return;

    // Load navbar
    await loadNavbar();

    // Initialize dashboard
    initDashboard();
});

/**
 * Load navbar component
 */
async function loadNavbar() {
    try {
        const response = await fetch('navbar.html');
        const html = await response.text();
        document.getElementById('navbar-container').innerHTML = html;

        // Initialize navbar after loading
        if (typeof initNavbar === 'function') {
            initNavbar();
        }
    } catch (error) {
        console.error('Error loading navbar:', error);
    }
}

/**
 * Initialize dashboard
 */
function initDashboard() {
    // Display user info
    displayUserInfo();

    // Initialize DEMAT status
    initDematStatus();

    // Initialize charts
    initCharts();

    // Load popular stocks
    loadPopularStocks();

    // Initialize financial form
    initFinancialForm();

    // Load saved plan if exists
    loadSavedPlan();

    // Update market time
    updateMarketTime();

    // Auto-refresh market data every 30 seconds
    setInterval(() => {
        refreshMarketData();
    }, 30000);
}

/**
 * Display user information
 */
function displayUserInfo() {
    const user = Navigation.getCurrentUser();
    if (!user) return;

    const userName = user.name || user.email.split('@')[0];

    // Update welcome message
    const welcomeUserName = document.getElementById('welcomeUserName');
    if (welcomeUserName) {
        welcomeUserName.textContent = userName;
    }

    // Update Navbar User Info
    const navUserName = document.getElementById('navUserName');
    const menuUserName = document.getElementById('menuUserName');
    const menuUserEmail = document.getElementById('menuUserEmail');
    const avatarInitials = document.querySelector('.avatar-initials-text');

    if (navUserName) navUserName.textContent = userName;
    if (menuUserName) menuUserName.textContent = userName;
    if (menuUserEmail) menuUserEmail.textContent = user.email;
    if (avatarInitials) avatarInitials.textContent = userName.charAt(0).toUpperCase();

    // Load portfolio stats (demo data for now)
    loadPortfolioStats();
}

/**
 * Load portfolio statistics
 */
async function loadPortfolioStats() {
    // 1. Try to fetch from Python Backend API first (Real Trading Bot Data)
    try {
        const isBackendConnected = await BackendAPI.isConnected();
        if (isBackendConnected) {
            const portfolio = await BackendAPI.getPortfolio();
            
            document.getElementById('portfolioValue').textContent = `₹${portfolio.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById('totalReturns').textContent = `₹${portfolio.total_pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById('activeInvestments').textContent = portfolio.open_positions;
            
            // Calculate changes
            // For P&L, we can just show the total P&L percentage if available, otherwise just P&L
            const pnlClass = portfolio.total_pnl >= 0 ? 'positive' : 'negative';
            const pnlSign = portfolio.total_pnl >= 0 ? '+' : '';
            
            const portfolioChangeEl = document.getElementById('portfolioChange');
            portfolioChangeEl.textContent = `${pnlSign}₹${Math.abs(portfolio.total_pnl).toFixed(2)}`;
            portfolioChangeEl.className = `stat-change ${pnlClass}`;
            
            return; // Exit if successful
        }
    } catch (error) {
        console.warn('Failed to fetch from BackendAPI, falling back to storage/demo:', error);
    }

    // 2. Fallback to existing DEMAT storage logic
    const dematConnection = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION);

    if (dematConnection && dematConnection.connected) {
        // Show actual portfolio data from storage
        const portfolioValue = dematConnection.portfolioValue || 0;
        const totalReturns = dematConnection.totalReturns || 0;
        const activeInvestments = dematConnection.activeInvestments || 0;

        document.getElementById('portfolioValue').textContent = Utils.formatCurrency(portfolioValue);
        document.getElementById('totalReturns').textContent = Utils.formatCurrency(totalReturns);
        document.getElementById('activeInvestments').textContent = activeInvestments;

        // Calculate changes
        const portfolioChange = portfolioValue > 0 ? ((totalReturns / portfolioValue) * 100).toFixed(2) : '0.00';
        const portfolioChangeEl = document.getElementById('portfolioChange');
        portfolioChangeEl.textContent = `${portfolioChange >= 0 ? '+' : ''}${portfolioChange}%`;
        portfolioChangeEl.className = `stat-change ${portfolioChange >= 0 ? 'positive' : 'negative'}`;
    } else {
        // Show demo data
        document.getElementById('portfolioValue').textContent = '₹0';
        document.getElementById('totalReturns').textContent = '₹0';
        document.getElementById('activeInvestments').textContent = '0';
        document.getElementById('portfolioChange').textContent = '+0%';
    }
}

/**
 * Initialize DEMAT account status
 */
function initDematStatus() {
    console.log('Initializing DEMAT status...');

    // Check if DEMAT elements exist (they may not be in all pages)
    const dematCard = document.getElementById('dematStatusCard');
    const dematStatusText = document.getElementById('dematStatusText');
    const connectBtn = document.getElementById('connectDematBtn');

    if (!dematCard || !dematStatusText || !connectBtn) {
        console.log('ℹ️ DEMAT elements not found on this page (this is OK for dashboard)');
        return; // Skip DEMAT initialization if elements don't exist
    }

    const dematConnection = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION);

    if (dematConnection && dematConnection.connected) {
        // Account is connected
        dematCard.classList.add('connected');
        const dematIcon = dematCard.querySelector('.demat-icon');
        if (dematIcon) dematIcon.textContent = '✅';
        dematStatusText.textContent = `Connected to ${dematConnection.broker || 'Upstox'} • Account: ${dematConnection.clientId || 'XXXXXX'}`;

        // Replace button with status indicator
        connectBtn.outerHTML = `
            <div class="demat-status-indicator">
                <span class="status-dot"></span>
                <span>Active</span>
            </div>
        `;
    } else {
        // Account not connected
        connectBtn.addEventListener('click', () => {
            // Redirect to investment page
            window.location.href = '../demat/investment.html';
        });
    }

    console.log('✅ DEMAT status initialized');
}

/**
 * Initialize charts
 */
function initCharts() {
    console.log('=== Initializing Charts ===');
    console.log('Chart.js available:', typeof Chart !== 'undefined');
    console.log('initMarketCharts function available:', typeof initMarketCharts === 'function');

    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js is not loaded!');
        return;
    }

    if (typeof initMarketCharts === 'function') {
        console.log('✅ Calling initMarketCharts()...');
        try {
            initMarketCharts();
            console.log('✅ Charts initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing charts:', error);
        }
    } else {
        console.error('❌ initMarketCharts function not found!');
        console.log('Available functions:', Object.keys(window).filter(k => k.includes('Chart')));
    }
}

/**
 * Load popular stocks (using real-time API)
 */
async function loadPopularStocks() {
    const stocksGrid = document.getElementById('stocksGrid');
    if (!stocksGrid) return;

    // Show loading
    stocksGrid.innerHTML = '<div style="text-align: center; padding: 20px; color: #718096;">Loading live stock prices...</div>';

    try {
        console.log('📈 Fetching popular stocks data...');

        const stocks = CONFIG.STOCKS.POPULAR_STOCKS.slice(0, 5);

        // Fetch real-time stock data from Yahoo Finance
        const stockPromises = stocks.map(stock => MarketAPI.getStockQuote(stock.symbol));
        const stockData = await Promise.all(stockPromises);

        console.log('✅ Popular stocks loaded successfully');

        // Render stock cards
        stocksGrid.innerHTML = stockData.map((data, index) => {
            const changeClass = data.changePercent >= 0 ? 'positive' : 'negative';
            const sign = data.changePercent >= 0 ? '+' : '';
            return `
                <div class="stock-card">
                    <div class="stock-symbol">${stocks[index].symbol.replace('.NS', '')}</div>
                    <div class="stock-name">${stocks[index].name}</div>
                    <div class="stock-price">₹${data.price.toFixed(2)}</div>
                    <div class="stock-change ${changeClass}">${sign}${data.changePercent.toFixed(2)}%</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading stocks:', error);
        stocksGrid.innerHTML = '<div style="text-align: center; padding: 20px; color: #718096;">Unable to load stocks. Please check your connection.</div>';
    }
}

/**
 * Initialize financial form
 */
function initFinancialForm() {
    console.log('Checking for financial form...');
    const form = document.getElementById('financialProfileForm');
    if (!form) {
        console.log('ℹ️ Financial form not found (this is OK for dashboard - form is on separate page)');
        return;
    }
    console.log('✅ Financial form found, initializing...');

    // Auto-calculate savings
    const salaryInput = document.getElementById('monthlySalary');
    const expensesInput = document.getElementById('monthlyExpenses');
    const savingsInput = document.getElementById('monthlySavings');

    function calculateSavings() {
        const salary = parseFloat(salaryInput.value) || 0;
        const expenses = parseFloat(expensesInput.value) || 0;
        const savings = Math.max(0, salary - expenses);
        savingsInput.value = savings;
    }

    salaryInput.addEventListener('input', calculateSavings);
    expensesInput.addEventListener('input', calculateSavings);

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateInvestmentPlan();
    });

    // Edit plan button
    const editPlanBtn = document.getElementById('editPlanBtn');
    if (editPlanBtn) {
        editPlanBtn.addEventListener('click', () => {
            document.getElementById('planFormCard').style.display = 'block';
            document.getElementById('planResultCard').style.display = 'none';
        });
    }

    // View full plan button
    const viewFullPlanBtn = document.getElementById('viewFullPlanBtn');
    if (viewFullPlanBtn) {
        viewFullPlanBtn.addEventListener('click', () => {
            showFullPlanModal();
        });
    }

    // Download plan button
    const downloadPlanBtn = document.getElementById('downloadPlanBtn');
    if (downloadPlanBtn) {
        downloadPlanBtn.addEventListener('click', () => {
            downloadPlanAsPDF();
        });
    }

    // Close modal
    const closeModalBtn = document.getElementById('closeFullPlanModal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            document.getElementById('fullPlanModal').classList.remove('active');
        });
    }
}

/**
 * Generate investment plan using AI
 */
async function generateInvestmentPlan() {
    const salary = parseFloat(document.getElementById('monthlySalary').value);
    const expenses = parseFloat(document.getElementById('monthlyExpenses').value);
    const savings = parseFloat(document.getElementById('monthlySavings').value);
    const age = parseInt(document.getElementById('age').value);
    const risk = document.querySelector('input[name="risk"]:checked').value;

    // Validate
    if (!salary || !expenses || !savings || !age) {
        Utils.showToast('Please fill all fields', 'warning');
        return;
    }

    if (savings <= 0) {
        Utils.showToast('Monthly savings must be greater than 0', 'warning');
        return;
    }

    try {
        Utils.showLoader('Generating your personalized investment plan...');

        const userData = { salary, expenses, savings, age, risk };

        // Generate plan using AI
        const plan = await API.generateInvestmentPlan(userData);

        // Save plan
        Utils.saveToStorage(CONFIG.SETTINGS.STORAGE_KEYS.INVESTMENT_PLAN, {
            plan,
            userData,
            generatedAt: new Date().toISOString()
        });

        // Display plan
        displayInvestmentPlan(plan);

        Utils.hideLoader();
        Utils.showToast(CONFIG.SUCCESS.PLAN_GENERATED, 'success');

    } catch (error) {
        Utils.hideLoader();
        Utils.showToast('Error generating plan. Please try again.', 'error');
        console.error('Plan generation error:', error);
    }
}

/**
 * Display investment plan
 */
function displayInvestmentPlan(plan) {
    document.getElementById('planFormCard').style.display = 'none';
    document.getElementById('planResultCard').style.display = 'block';
    document.getElementById('planContent').textContent = plan;
    document.getElementById('fullPlanContent').innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${plan}</pre>`;

    // Scroll to plan
    Utils.scrollTo('#planResultCard');
}

/**
 * Load saved plan
 */
function loadSavedPlan() {
    console.log('Checking for saved investment plan...');

    // Check if plan elements exist
    if (!document.getElementById('planFormCard') || !document.getElementById('planResultCard')) {
        console.log('ℹ️ Plan elements not found (this is OK for dashboard - plan is on separate page)');
        return;
    }

    const savedPlan = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.INVESTMENT_PLAN);

    if (savedPlan && savedPlan.plan) {
        console.log('✅ Saved plan found, loading...');
        // Pre-fill form
        const { userData } = savedPlan;
        if (userData) {
            const salaryInput = document.getElementById('monthlySalary');
            const expensesInput = document.getElementById('monthlyExpenses');
            const savingsInput = document.getElementById('monthlySavings');
            const ageInput = document.getElementById('age');
            const riskInput = document.querySelector(`input[name="risk"][value="${userData.risk}"]`);

            if (salaryInput) salaryInput.value = userData.salary;
            if (expensesInput) expensesInput.value = userData.expenses;
            if (savingsInput) savingsInput.value = userData.savings;
            if (ageInput) ageInput.value = userData.age;
            if (riskInput) riskInput.checked = true;
        }

        // Display plan
        displayInvestmentPlan(savedPlan.plan);
    } else {
        console.log('ℹ️ No saved plan found');
    }
}

/**
 * Show full plan modal
 */
function showFullPlanModal() {
    document.getElementById('fullPlanModal').classList.add('active');
}

/**
 * Download plan as PDF (simplified version)
 */
function downloadPlanAsPDF() {
    const plan = document.getElementById('planContent').textContent;
    const user = Navigation.getCurrentUser();

    // Create text file (PDF generation requires library)
    const blob = new Blob([plan], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `UPVEST_Investment_Plan_${user.name || 'User'}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    Utils.showToast('Plan downloaded successfully!', 'success');
}

/**
 * Update market time
 */
function updateMarketTime() {
    const marketTimeEl = document.getElementById('marketTime');
    if (!marketTimeEl) return;

    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();

    // Indian market hours: 9:15 AM - 3:30 PM
    const isMarketOpen = (hours === 9 && minutes >= 15) ||
        (hours > 9 && hours < 15) ||
        (hours === 15 && minutes <= 30);

    const status = isMarketOpen ? 'Market Open' : 'Market Closed';
    const lastUpdate = Utils.formatDate(now, 'time');

    marketTimeEl.innerHTML = `${status} • Updated at ${lastUpdate}`;
}

/**
 * Refresh market data
 */
async function refreshMarketData() {
    // Refresh charts
    if (typeof refreshCharts === 'function') {
        refreshCharts();
    }

    // Refresh stocks
    await loadPopularStocks();

    // Update time
    updateMarketTime();
}