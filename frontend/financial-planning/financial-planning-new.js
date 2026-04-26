/* ============================================
   UPVEST - Financial Planning JavaScript
   Multi-step form with Gemini AI integration
   ============================================ */

let currentStep = 1;
let selectedRisk = '';
let formData = {};

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
        // Call Gemini AI for investment recommendations
        const plan = await getAIInvestmentPlan(formData);
        
        // Complete progress
        clearInterval(progressInterval);
        clearInterval(messageInterval);
        document.getElementById('progressFill').style.width = '100%';
        
        // Wait a bit then show results
        setTimeout(() => {
            displayInvestmentPlan(plan);
            goToStep(4);
        }, 800);
        
    } catch (error) {
        clearInterval(progressInterval);
        clearInterval(messageInterval);
        console.error('Error generating plan:', error);
        alert('Unable to generate plan. Please try again or check your API configuration.');
        goToStep(2);
    }
}

/**
 * Get AI Investment Plan from Gemini
 */
async function getAIInvestmentPlan(data) {
    const prompt = `You are an expert financial advisor. Create a detailed, personalized investment plan based on this profile:

**User Profile:**
- Age: ${data.age} years
- Monthly Income: ₹${data.monthlyIncome.toLocaleString('en-IN')}
- Monthly Expenses: ₹${data.monthlyExpenses.toLocaleString('en-IN')}
- Monthly Surplus: ₹${data.monthlySurplus.toLocaleString('en-IN')}
- Current Savings: ₹${data.currentSavings.toLocaleString('en-IN')}
- Existing Investments: ₹${data.existingInvestments.toLocaleString('en-IN')}
- Investment Duration: ${data.duration === 'short' ? '1-3 years' : data.duration === 'medium' ? '3-5 years' : '5+ years'}
- Primary Goal: ${data.goal}
- Risk Tolerance: ${data.risk} risk

**Please provide:**

1. **Executive Summary**: Brief overview of the recommended strategy (2-3 sentences)

2. **Asset Allocation** (provide exact percentages that add up to 100%):
   - Equity (Stocks/Mutual Funds)
   - Debt (Bonds/Fixed Deposits)
   - Gold (Digital Gold/Gold ETFs)
   - Emergency Fund (Liquid assets)
   
3. **Specific Investment Recommendations** (list 4-5 real options with current returns):
   Format each as: "Investment Name - Expected Return - Risk Level - Brief description"
   Use REAL Indian investment options like:
   - PPF (Public Provident Fund) - 7.1% p.a.
   - Nifty 50 Index Funds - 12-15% p.a.
   - Corporate Bonds - 8-9% p.a.
   - Large Cap Mutual Funds - 12-14% p.a.
   - Balanced Hybrid Funds - 10-12% p.a.
   - Gold ETFs - 8-10% p.a.
   - Liquid Funds - 6-7% p.a.

4. **Monthly Investment Plan**:
   - How much to invest in each category
   - SIP recommendations

5. **Expected Outcomes**:
   - Projected portfolio value after selected duration
   - Expected annual returns

6. **Key Recommendations** (3-4 action items)

Be specific with numbers. Use current real market returns for Indian investments (2024-2025).`;

    console.log('📤 Requesting investment plan from Gemini AI...');

    const response = await fetch(`${CONFIG.API_ENDPOINTS.GEMINI_BASE_URL}${CONFIG.API_ENDPOINTS.GEMINI_GENERATE}?key=${CONFIG.API_KEYS.GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            contents: [{
                parts: [{
                    text: prompt
                }]
            }],
            generationConfig: {
                temperature: 0.7,
                topK: 40,
                topP: 0.95,
                maxOutputTokens: 2048,
            }
        })
    });

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    const aiResponse = await response.json();
    const planText = aiResponse.candidates[0].content.parts[0].text;

    console.log('✅ Received AI investment plan');

    return {
        text: planText,
        data: data
    };
}

/**
 * Display Investment Plan
 */
function displayInvestmentPlan(plan) {
    const container = document.getElementById('investmentPlanContent');
    
    const html = `
        <div class="plan-summary">
            <h3 style="font-size: 20px; font-weight: 700; color: #1a202c; margin-bottom: 12px;">
                📊 Your Financial Summary
            </h3>
            <div class="plan-summary-grid">
                <div class="summary-item">
                    <div class="summary-label">Monthly Surplus</div>
                    <div class="summary-value" style="color: #10b981;">
                        ₹${plan.data.monthlySurplus.toLocaleString('en-IN')}
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Current Savings</div>
                    <div class="summary-value">
                        ₹${plan.data.currentSavings.toLocaleString('en-IN')}
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Risk Profile</div>
                    <div class="summary-value" style="color: #7c3aed;">
                        ${plan.data.risk.charAt(0).toUpperCase() + plan.data.risk.slice(1)} Risk
                    </div>
                </div>
            </div>
        </div>

        <div class="ai-recommendations">
            <h3 style="font-size: 20px; font-weight: 700; color: #1a202c; margin-bottom: 16px;">
                🤖 AI-Generated Investment Strategy
            </h3>
            <div style="background: #f8fafc; border-radius: 12px; padding: 24px; line-height: 1.8; white-space: pre-wrap; font-size: 15px; color: #1a202c;">
${plan.text}
            </div>
        </div>

        <div style="margin-top: 32px; padding: 20px; background: #fef3c7; border: 1.5px solid #fde047; border-radius: 12px; display: flex; gap: 12px;">
            <div style="color: #854d0e; font-size: 20px;">⚠️</div>
            <div style="font-size: 14px; color: #854d0e; line-height: 1.6;">
                <strong style="display: block; margin-bottom: 4px;">Important Disclaimer:</strong>
                This is AI-generated advice for educational purposes. Please consult with a certified financial advisor before making investment decisions. Past performance doesn't guarantee future results.
            </div>
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
}

/**
 * Download Plan (Placeholder)
 */
function downloadPlan() {
    alert('Download feature coming soon! You can copy the plan text for now.');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
