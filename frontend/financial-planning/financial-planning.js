/* ============================================
   UPVEST - Financial Planning JavaScript
   Multi-step form with Gemini AI integration
   ============================================ */

let currentStep = 1;
let selectedRisk = '';
let formData = {};

/**
 * Get duration in years from duration selection
 * @param {string} duration - Duration selection (short/medium/long)
 * @returns {number} Number of years
 */
function getDurationYears(duration) {
    const durationMap = {
        'short': 3,      // Short term (1-3 years)
        'medium': 5,     // Medium term (3-5 years)  
        'long': 10       // Long term (5+ years)
    };
    return durationMap[duration] || 5; // Default to 5 years
}

/**
 * Initialize the page
 */
function init() {
    // Calculate surplus when income/expenses change
    document.getElementById('monthlyIncome')?.addEventListener('input', calculateSurplus);
    document.getElementById('monthlyExpenses')?.addEventListener('input', calculateSurplus);

    // Risk card selection
    document.querySelectorAll('.risk-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.risk-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedRisk = card.dataset.risk;
        });
    });

    console.log('✅ Financial Planning page initialized');
}

/**
 * Calculate monthly surplus
 */
function calculateSurplus() {
    const income = parseFloat(document.getElementById('monthlyIncome').value) || 0;
    const expenses = parseFloat(document.getElementById('monthlyExpenses').value) || 0;
    const surplus = income - expenses;

    if (income > 0 && expenses > 0) {
        document.getElementById('surplusBox').style.display = 'flex';
        document.getElementById('surplusAmount').textContent = `₹${surplus.toLocaleString('en-IN')}`;
    } else {
        document.getElementById('surplusBox').style.display = 'none';
    }
}

/**
 * Navigate to a specific step
 */
function goToStep(step) {
    // Validate current step before moving
    if (step > currentStep) {
        if (currentStep === 1 && !validateStep1()) {
            return;
        }
        if (currentStep === 2 && !validateStep2()) {
            return;
        }
    }

    // Hide current step
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active', 'completed'));

    // Show new step
    document.getElementById(`step${step}`).classList.add('active');
    document.querySelector(`.step[data-step="${step}"]`).classList.add('active');

    // Mark previous steps as completed
    for (let i = 1; i < step; i++) {
        document.querySelector(`.step[data-step="${i}"]`).classList.add('completed');
    }

    currentStep = step;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Validate Step 1
 */
function validateStep1() {
    const income = parseFloat(document.getElementById('monthlyIncome').value);
    const expenses = parseFloat(document.getElementById('monthlyExpenses').value);
    const savings = parseFloat(document.getElementById('currentSavings').value);

    if (!income || income <= 0) {
        alert('Please enter your monthly income');
        return false;
    }
    if (!expenses || expenses <= 0) {
        alert('Please enter your monthly expenses');
        return false;
    }
    if (!savings || savings < 0) {
        alert('Please enter your current savings');
        return false;
    }
    if (expenses >= income) {
        alert('Your expenses should be less than your income to start investing');
        return false;
    }

    // Save data
    formData.monthlyIncome = income;
    formData.monthlyExpenses = expenses;
    formData.currentSavings = savings;
    formData.existingInvestments = parseFloat(document.getElementById('existingInvestments').value) || 0;
    formData.monthlySurplus = income - expenses;

    return true;
}

/**
 * Validate Step 2
 */
function validateStep2() {
    const age = parseInt(document.getElementById('userAge').value);
    const duration = document.getElementById('investmentDuration').value;
    const goal = document.getElementById('investmentGoal').value;

    if (!age || age < 18 || age > 100) {
        alert('Please enter a valid age (18-100)');
        return false;
    }
    if (!duration) {
        alert('Please select investment duration');
        return false;
    }
    if (!goal) {
        alert('Please select your investment goal');
        return false;
    }
    if (!selectedRisk) {
        alert('Please select your risk tolerance');
        return false;
    }

    // Save data
    formData.age = age;
    formData.duration = duration;
    formData.durationYears = getDurationYears(duration); // Add years
    formData.goal = goal;
    formData.risk = selectedRisk;

    return true;
}

/**
 * Generate AI Investment Plan
 */
async function generateAIPlan() {
    if (!validateStep2()) {
        return;
    }

    // Go to AI analysis step
    goToStep(3);

    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        document.getElementById('progressFill').style.width = progress + '%';
    }, 300);

    // Messages during analysis
    const messages = [
        'Calculating optimal allocation...',
        'Analyzing market conditions...',
        'Evaluating risk factors...',
        'Creating personalized strategy...',
        'Finalizing recommendations...'
    ];

    let messageIndex = 0;
    const messageInterval = setInterval(() => {
        if (messageIndex < messages.length) {
            document.getElementById('progressText').textContent = messages[messageIndex];
            messageIndex++;
        }
    }, 1200);

    try {
        // Prepare User Data
        const userData = {
            salary: formData.monthlyIncome,
            expenses: formData.monthlyExpenses,
            savings: formData.monthlySurplus, // Monthly Surplus for SIPs
            currentSavings: formData.currentSavings, // Lump sum for safe investment
            age: formData.age,
            risk: formData.risk,
            duration: formData.duration,
            durationYears: formData.durationYears
        };

        // Call Centralized API (which now returns JSON)
        const plan = await API.generateInvestmentPlan(userData);

        // Complete progress
        clearInterval(progressInterval);
        clearInterval(messageInterval);
        document.getElementById('progressFill').style.width = '100%';

        // Wait a bit then show results
        setTimeout(() => {
            displayInvestmentPlan(plan, userData);
            goToStep(4);
        }, 800);

    } catch (error) {
        clearInterval(progressInterval);
        clearInterval(messageInterval);
        console.error('❌ Error generating plan:', error);

        // Show detailed error message
        const errorMessage = error.message || 'Unable to generate plan. Please try again.';
        alert(errorMessage);
        goToStep(2);
    }
}

/**
 * Get AI Investment Plan from Gemini
 */
// Removed getAIInvestmentPlan as we use API.generateInvestmentPlan now

function buildFallbackPlan(data) {
    const allocationByRisk = {
        low: { equity: 25, debt: 35, gold: 15, emergency: 25 },
        medium: { equity: 40, debt: 30, gold: 10, emergency: 20 },
        high: { equity: 55, debt: 20, gold: 10, emergency: 15 }
    };
    const riskKey = (data.risk || 'medium').toLowerCase();
    const allocation = allocationByRisk[riskKey] || allocationByRisk.medium;
    const monthly = data.monthlySurplus || 0;

    const amount = (percent) => Math.round((monthly * percent) / 100);

    return `## Executive Summary
Based on your current surplus, here’s a balanced starter plan with realistic allocations. This is a fallback plan created while the AI service is rate-limited.

## Asset Allocation
- Equity (Stocks/Mutual Funds): ${allocation.equity}%
- Debt (Bonds/Fixed Deposits): ${allocation.debt}%
- Gold (Digital Gold/Gold ETFs): ${allocation.gold}%
- Emergency Fund (Liquid assets): ${allocation.emergency}%

## Monthly Investment Plan
- Equity SIPs: ${Utils.formatCurrency(amount(allocation.equity))}
- Debt/FD: ${Utils.formatCurrency(amount(allocation.debt))}
- Gold ETFs: ${Utils.formatCurrency(amount(allocation.gold))}
- Emergency Fund: ${Utils.formatCurrency(amount(allocation.emergency))}

## Suggested Options
1. Nifty 50 Index Fund - 12-15% p.a. - Medium risk
2. Large Cap Mutual Fund - 12-14% p.a. - Medium risk
3. PPF (Tax saving) - 7.1% p.a. - Low risk
4. Corporate Bond Fund - 8-9% p.a. - Low to Medium risk
5. Gold ETF - 8-10% p.a. - Medium risk

## Key Recommendations
1. Start SIPs immediately and review every 6 months.
2. Keep at least 3-6 months of expenses in the emergency fund.
3. Increase equity allocation as income grows.
4. Rebalance annually based on market performance.`;
}

/**
 * Format AI text with better styling
 */
function formatInvestmentPlan(text) {
    // Convert markdown-style formatting to HTML
    let formatted = text;

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong style="color: #1a202c; font-weight: 700;">$1</strong>');

    // Convert headers (## Header) to styled h3
    formatted = formatted.replace(/^## (.+)$/gm, '<h3 style="font-size: 18px; font-weight: 700; color: #7c3aed; margin-top: 24px; margin-bottom: 12px;">📌 $1</h3>');

    // Convert single # headers
    formatted = formatted.replace(/^# (.+)$/gm, '<h2 style="font-size: 20px; font-weight: 700; color: #1a202c; margin-top: 28px; margin-bottom: 14px;">🎯 $1</h2>');

    // Convert bullet points (- item or * item) to styled list items
    formatted = formatted.replace(/^[•\-\*] (.+)$/gm, '<div style="padding-left: 24px; margin-bottom: 8px; position: relative;"><span style="position: absolute; left: 0; color: #7c3aed; font-weight: 700;">•</span><span style="color: #1a202c; line-height: 1.6;">$1</span></div>');

    // Convert numbered lists (1. item)
    formatted = formatted.replace(/^(\d+)\. (.+)$/gm, '<div style="padding-left: 28px; margin-bottom: 10px; position: relative;"><span style="position: absolute; left: 0; color: #7c3aed; font-weight: 700;">$1.</span><span style="color: #1a202c; line-height: 1.6;">$2</span></div>');

    // Highlight percentages
    formatted = formatted.replace(/(\d+(?:\.\d+)?%)/g, '<span style="color: #10b981; font-weight: 600;">$1</span>');

    // Highlight currency amounts (₹)
    formatted = formatted.replace(/(₹[\d,]+(?:\.\d+)?(?:\s*(?:lakh|lakhs|crore|crores|L|Cr))?)/gi, '<span style="color: #10b981; font-weight: 600;">$1</span>');

    // Highlight years
    formatted = formatted.replace(/(\d+(?:\+)?\s*years?)/gi, '<span style="color: #3b82f6; font-weight: 600;">$1</span>');

    // Convert line breaks to <br> but preserve structure
    formatted = formatted.replace(/\n\n/g, '<div style="height: 16px;"></div>');
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

/**
 * Display Investment Plan
 */
/**
 * Display Investment Plan
 */
function displayInvestmentPlan(plan, userData) {
    const container = document.getElementById('investmentPlanContent');

    // Fallback if plan is string (handle old format or parse error)
    if (typeof plan === 'string') {
        container.innerHTML = `<div style="padding: 20px;">${plan}</div>`;
        return;
    }

    const html = `
        <div class="plan-header-summary">
            <div class="summary-card detail-card">
                <h3>💰 Monthly Investment</h3>
                <div class="value">₹${userData.savings.toLocaleString('en-IN')}</div>
                <div class="subtitle">Based on your surplus</div>
            </div>
            <div class="summary-card detail-card">
                <h3>📈 ${userData.durationYears}-Year Projection</h3>
                <div class="value">₹${Utils.formatNumber(plan.projections.expected_value)}</div>
                <div class="subtitle">@ ${plan.projections.cagr}% expected CAGR</div>
            </div>
            <div class="summary-card detail-card">
                <h3>🛡️ Risk Profile</h3>
                <div class="value">${userData.risk}</div>
                <div class="subtitle">${plan.risk_analysis}</div>
            </div>
        </div>

        <div class="charts-container" style="display: flex; gap: 20px; margin: 30px 0; flex-wrap: wrap;">
            <div class="chart-card" style="flex: 1; min-width: 300px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <h3 style="margin-bottom: 20px;">Asset Allocation</h3>
                <canvas id="allocationChart"></canvas>
            </div>
            <div class="chart-card" style="flex: 1.5; min-width: 300px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <h3 style="margin-bottom: 20px;">Wealth Projection (${userData.durationYears} Years)</h3>
                <canvas id="projectionChart"></canvas>
            </div>
        </div>

        <div class="strategy-section">
            <h3 style="font-size: 22px; margin-bottom: 20px; color: #1a202c;">🚀 Your Investment Strategy</h3>
            <div class="strategy-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                ${plan.investment_strategy.map(item => `
                    <div class="strategy-card" style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid ${getColorForCategory(item.category)}; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="font-size: 18px; margin: 0; color: #2d3748;">${item.category}</h4>
                            <span style="background: #edf2f7; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 14px;">${item.percentage}%</span>
                        </div>
                        <div style="font-size: 24px; font-weight: 700; color: #2d3748; margin-bottom: 10px;">
                            ₹${item.amount.toLocaleString('en-IN')}<span style="font-size: 14px; color: #718096; font-weight: 400;">/month</span>
                        </div>
                        <p style="color: #4a5568; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">
                            ${item.recommendation}
                        </p>
                        <div style="display: flex; justify-content: space-between; font-size: 13px; color: #718096; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                            <span>Expected Return: <strong style="color: #38a169;">${item.expected_return}</strong></span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="executive-summary" style="margin-top: 30px; background: #ebf8ff; padding: 20px; border-radius: 12px; border: 1px solid #bee3f8;">
            <h4 style="color: #2b6cb0; margin-bottom: 10px;">💡 Executive Summary</h4>
            <p style="color: #2c5282; line-height: 1.6;">${plan.executive_summary}</p>
        </div>
        
        <div class="market-insight" style="margin-top: 20px; background: #fffaf0; padding: 20px; border-radius: 12px; border: 1px solid #fbd38d;">
            <h4 style="color: #c05621; margin-bottom: 10px;">⚡ Real-Time Market Insight</h4>
            <p style="color: #7b341e; line-height: 1.6;">${plan.market_insight || "Market data utilized for this plan."}</p>
        </div>

        <div style="margin-top: 32px; display: flex; gap: 16px; justify-content: center;">
            <button class="btn-next" onclick="downloadPlan()" style="width: auto; padding: 14px 32px;">
                📥 Download Plan
            </button>
            <button class="btn-secondary" onclick="goToStep(1)">
                🔄 Create New Plan
            </button>
        </div>
    `;

    container.innerHTML = html;

    // Initialize Charts
    renderCharts(plan, userData);
}

function getColorForCategory(category) {
    if (category.includes('Equity')) return '#3b82f6'; // Blue
    if (category.includes('Gold')) return '#eab308'; // Yellow
    if (category.includes('Debt') || category.includes('Bond') || category.includes('PPF')) return '#10b981'; // Green
    if (category.includes('Emergency')) return '#f97316'; // Orange
    return '#6366f1'; // Indigo default
}

function renderCharts(plan, userData) {
    // 1. Asset Allocation Chart
    const ctxAlloc = document.getElementById('allocationChart').getContext('2d');
    const allocation = plan.asset_allocation;

    new Chart(ctxAlloc, {
        type: 'doughnut',
        data: {
            labels: Object.keys(allocation).map(k => k.charAt(0).toUpperCase() + k.slice(1)),
            datasets: [{
                data: Object.values(allocation),
                backgroundColor: ['#3b82f6', '#10b981', '#eab308', '#f97316'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

    // 2. Wealth Projection Chart
    const ctxProj = document.getElementById('projectionChart').getContext('2d');
    const durationYears = userData.durationYears || 10; // Default to 10 years if not provided
    const years = Array.from({ length: durationYears + 1 }, (_, i) => i); // 0 to durationYears
    const initialSavings = userData.savings || 0; // Current savings
    const monthlyInvestment = plan.projections.total_investment / (durationYears * 12); // Monthly SIP based on total investment over duration
    const cagr = plan.projections.cagr / 100;

    // Future Value of SIP + Future Value of Initial Savings
    const projections = years.map(year => {
        const months = year * 12;
        const monthlyRate = cagr / 12;

        // Future Value of Initial Savings (FV = PV * (1 + r)^n)
        const fvInitialSavings = initialSavings * Math.pow(1 + monthlyRate, months);

        // Future Value of SIP (FV = P * [((1+i)^n - 1)/i] * (1+i))
        let fvSIP = 0;
        if (monthlyRate > 0) {
            fvSIP = monthlyInvestment * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) * (1 + monthlyRate);
        } else {
            fvSIP = monthlyInvestment * months; // Simple addition if rate is 0
        }

        return fvInitialSavings + fvSIP;
    });

    const investments = years.map(year => initialSavings + (monthlyInvestment * 12 * year));

    new Chart(ctxProj, {
        type: 'line',
        data: {
            labels: years.map(y => `Year ${y}`),
            datasets: [
                {
                    label: 'Expected Value',
                    data: projections,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Total Invested',
                    data: investments,
                    borderColor: '#94a3b8',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    ticks: {
                        callback: function (value) {
                            return '₹' + (value / 100000).toFixed(1) + 'L';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Download Plan (Placeholder)
 */
function downloadPlan() {
    alert('Download feature coming soon! You can copy the plan text for now.');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
