/* ============================================
   UPVEST - Quiz JavaScript
   MCQ and Scenario-based quizzes
   ============================================ */

// MCQ Questions (based on learning modules)
const MCQ_QUESTIONS = [
    {
        id: 1,
        question: "What does NIFTY 50 represent?",
        options: [
            "Top 50 companies listed on NSE",
            "50 government bonds",
            "50 mutual funds",
            "50 stock brokers"
        ],
        correct: 0,
        module: 1
    },
    {
        id: 2,
        question: "What is a stock?",
        options: [
            "A loan to a company",
            "Ownership share in a company",
            "A government security",
            "A type of insurance"
        ],
        correct: 1,
        module: 2
    },
    {
        id: 3,
        question: "What does SIP stand for?",
        options: [
            "Stock Investment Plan",
            "Systematic Investment Plan",
            "Simple Interest Payment",
            "Secure Investment Portfolio"
        ],
        correct: 1,
        module: 3
    },
    {
        id: 4,
        question: "What is diversification in investing?",
        options: [
            "Investing all money in one stock",
            "Spreading investments across different assets",
            "Only buying government bonds",
            "Keeping all money in savings account"
        ],
        correct: 1,
        module: 4
    },
    {
        id: 5,
        question: "What is a mutual fund?",
        options: [
            "A bank account",
            "A pooled investment vehicle managed by professionals",
            "A type of loan",
            "A government scheme"
        ],
        correct: 1,
        module: 3
    },
    {
        id: 6,
        question: "What does P/E ratio measure?",
        options: [
            "Profit and Expenses",
            "Price to Earnings ratio",
            "Portfolio Efficiency",
            "Payment Estimate"
        ],
        correct: 1,
        module: 6
    },
    {
        id: 7,
        question: "What is ELSS?",
        options: [
            "Emergency Loan Savings Scheme",
            "Equity Linked Savings Scheme",
            "Electronic Ledger Security System",
            "Extra Long-term Stock Strategy"
        ],
        correct: 1,
        module: 7
    },
    {
        id: 8,
        question: "What is the lock-in period for ELSS?",
        options: [
            "1 year",
            "2 years",
            "3 years",
            "5 years"
        ],
        correct: 2,
        module: 7
    },
    {
        id: 9,
        question: "What is a DEMAT account?",
        options: [
            "A savings account",
            "An account to hold shares electronically",
            "A loan account",
            "A credit card account"
        ],
        correct: 1,
        module: 2
    },
    {
        id: 10,
        question: "What is NAV in mutual funds?",
        options: [
            "Net Asset Value",
            "New Account Verification",
            "National Average Value",
            "Non-Adjustable Variable"
        ],
        correct: 0,
        module: 3
    },
    {
        id: 11,
        question: "What is a blue-chip stock?",
        options: [
            "A stock that is blue in color",
            "Stock of well-established, financially sound companies",
            "A penny stock",
            "A government bond"
        ],
        correct: 1,
        module: 2
    },
    {
        id: 12,
        question: "What is compound interest?",
        options: [
            "Simple interest calculated twice",
            "Interest calculated on principal and accumulated interest",
            "Interest paid by companies",
            "A type of bank fee"
        ],
        correct: 1,
        module: 8
    },
    {
        id: 13,
        question: "What is a bear market?",
        options: [
            "Market where prices are rising",
            "Market where prices are falling",
            "Market for animal stocks",
            "A stable market"
        ],
        correct: 1,
        module: 1
    },
    {
        id: 14,
        question: "What is a bull market?",
        options: [
            "Market where prices are falling",
            "Market where prices are rising",
            "A volatile market",
            "A closed market"
        ],
        correct: 1,
        module: 1
    },
    {
        id: 15,
        question: "What is risk appetite?",
        options: [
            "How much food you can eat",
            "Your willingness to take investment risks",
            "Your monthly expenses",
            "Your salary level"
        ],
        correct: 1,
        module: 4
    },
    {
        id: 16,
        question: "What is capital gains tax?",
        options: [
            "Tax on salary",
            "Tax on profit from selling investments",
            "Tax on property",
            "Tax on business income"
        ],
        correct: 1,
        module: 7
    },
    {
        id: 17,
        question: "What is a dividend?",
        options: [
            "A loan from company",
            "Profit distributed to shareholders",
            "A type of bond",
            "A bank interest"
        ],
        correct: 1,
        module: 2
    },
    {
        id: 18,
        question: "What is portfolio rebalancing?",
        options: [
            "Selling all stocks",
            "Adjusting asset allocation to maintain desired risk level",
            "Buying only new stocks",
            "Closing investment accounts"
        ],
        correct: 1,
        module: 4
    },
    {
        id: 19,
        question: "What is an IPO?",
        options: [
            "International Payment Order",
            "Initial Public Offering",
            "Investment Portfolio Option",
            "Indian Postal Order"
        ],
        correct: 1,
        module: 2
    },
    {
        id: 20,
        question: "What is the benefit of long-term investing?",
        options: [
            "Quick profits",
            "Compound growth and lower taxes",
            "Daily income",
            "No risk involved"
        ],
        correct: 1,
        module: 8
    }
];

// Scenario-based questions
const SCENARIO_QUESTIONS = [
    {
        id: 1,
        scenario: "You are 25 years old with a monthly salary of ₹50,000. You have ₹20,000 in savings per month. You want to build wealth for retirement. What investment strategy would you recommend for yourself and why?",
        hint: "Consider your age, time horizon, and risk capacity"
    },
    {
        id: 2,
        scenario: "The stock market has crashed by 20% in the last month. You have ₹5 lakhs invested in equity mutual funds. What would be your action plan and reasoning?",
        hint: "Think about market cycles and long-term perspective"
    },
    {
        id: 3,
        scenario: "You need to save ₹1.5 lakhs for tax deduction under Section 80C. You have 6 months left in the financial year. What investment options would you choose and why?",
        hint: "Consider ELSS, PPF, and other 80C instruments"
    },
    {
        id: 4,
        scenario: "You have ₹10 lakhs to invest. Your goal is to buy a house in 5 years. How would you allocate this money across different investment options?",
        hint: "Balance between growth and capital protection"
    },
    {
        id: 5,
        scenario: "Your friend suggests investing all your savings in a single stock that has given 200% returns last year. How would you respond and what alternative approach would you suggest?",
        hint: "Think about diversification and risk management"
    }
];

let currentQuizType = null;
let currentQuestionIndex = 0;
let userAnswers = [];
let quizStartTime = null;
let timerInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!Navigation.initProtectedPage()) return;
    
    await loadNavbar();
    initQuiz();
});

async function loadNavbar() {
    try {
        const response = await fetch('../home/navbar.html');
        const html = await response.text();
        document.getElementById('navbar-container').innerHTML = html;
        if (typeof initNavbar === 'function') initNavbar();
    } catch (error) {
        console.error('Error loading navbar:', error);
    }
}

function initQuiz() {
    const quizTypeCards = document.querySelectorAll('.quiz-type-card');
    
    quizTypeCards.forEach(card => {
        const button = card.querySelector('button');
        button.addEventListener('click', () => {
            const type = card.dataset.type;
            startQuiz(type);
        });
    });
    
    document.getElementById('prevBtn').addEventListener('click', previousQuestion);
    document.getElementById('nextBtn').addEventListener('click', nextQuestion);
    document.getElementById('retakeBtn').addEventListener('click', resetQuiz);
}

function startQuiz(type) {
    currentQuizType = type;
    currentQuestionIndex = 0;
    userAnswers = [];
    quizStartTime = Date.now();
    
    document.getElementById('quizSelection').style.display = 'none';
    document.getElementById('quizContainer').style.display = 'block';
    
    if (type === 'mcq') {
        startTimer(15 * 60); // 15 minutes
    } else {
        startTimer(20 * 60); // 20 minutes
    }
    
    loadQuestion();
}

function loadQuestion() {
    const questions = currentQuizType === 'mcq' ? MCQ_QUESTIONS : SCENARIO_QUESTIONS;
    const question = questions[currentQuestionIndex];
    const questionCard = document.getElementById('questionCard');
    
    // Update progress
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
    document.getElementById('progressText').textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
    
    // Load question content
    if (currentQuizType === 'mcq') {
        questionCard.innerHTML = `
            <div class="question-number">Question ${currentQuestionIndex + 1}</div>
            <div class="question-text">${question.question}</div>
            <div class="options-list">
                ${question.options.map((option, index) => `
                    <div class="option-item" data-index="${index}">
                        ${String.fromCharCode(65 + index)}. ${option}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Add click handlers
        questionCard.querySelectorAll('.option-item').forEach(item => {
            item.addEventListener('click', () => selectOption(item));
        });
        
        // Restore previous answer if exists
        if (userAnswers[currentQuestionIndex] !== undefined) {
            const selectedOption = questionCard.querySelector(`[data-index="${userAnswers[currentQuestionIndex]}"]`);
            if (selectedOption) selectedOption.classList.add('selected');
        }
    } else {
        questionCard.innerHTML = `
            <div class="question-number">Scenario ${currentQuestionIndex + 1}</div>
            <div class="question-text">${question.scenario}</div>
            <div class="question-hint" style="font-size: 14px; color: var(--text-muted); margin-bottom: 16px;">
                💡 Hint: ${question.hint}
            </div>
            <textarea class="scenario-textarea" placeholder="Type your detailed answer here...">${userAnswers[currentQuestionIndex] || ''}</textarea>
        `;
    }
    
    // Update navigation buttons
    document.getElementById('prevBtn').disabled = currentQuestionIndex === 0;
    document.getElementById('nextBtn').textContent = currentQuestionIndex === questions.length - 1 ? 'Submit Quiz' : 'Next';
}

function selectOption(item) {
    document.querySelectorAll('.option-item').forEach(opt => opt.classList.remove('selected'));
    item.classList.add('selected');
    userAnswers[currentQuestionIndex] = parseInt(item.dataset.index);
}

function previousQuestion() {
    if (currentQuestionIndex > 0) {
        saveCurrentAnswer();
        currentQuestionIndex--;
        loadQuestion();
    }
}

function nextQuestion() {
    saveCurrentAnswer();
    
    const questions = currentQuizType === 'mcq' ? MCQ_QUESTIONS : SCENARIO_QUESTIONS;
    
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        loadQuestion();
    } else {
        submitQuiz();
    }
}

function saveCurrentAnswer() {
    if (currentQuizType === 'scenario') {
        const textarea = document.querySelector('.scenario-textarea');
        if (textarea) {
            userAnswers[currentQuestionIndex] = textarea.value;
        }
    }
}

async function submitQuiz() {
    clearInterval(timerInterval);
    const timeTaken = Math.floor((Date.now() - quizStartTime) / 1000);
    
    Utils.showLoader('Evaluating your answers...');
    
    let score = 0;
    
    if (currentQuizType === 'mcq') {
        // Calculate MCQ score
        MCQ_QUESTIONS.forEach((q, index) => {
            if (userAnswers[index] === q.correct) score++;
        });
        
        displayResults(score, MCQ_QUESTIONS.length, timeTaken);
    } else {
        // Evaluate scenario answers using AI
        try {
            score = await evaluateScenarioAnswers();
            displayResults(score, SCENARIO_QUESTIONS.length, timeTaken);
        } catch (error) {
            Utils.hideLoader();
            Utils.showToast('Error evaluating answers. Please try again.', 'error');
        }
    }
}

async function evaluateScenarioAnswers() {
    // Use Gemini AI to evaluate scenario answers
    let totalScore = 0;
    
    for (let i = 0; i < SCENARIO_QUESTIONS.length; i++) {
        const question = SCENARIO_QUESTIONS[i];
        const answer = userAnswers[i] || '';
        
        if (!answer.trim()) continue;
        
        const prompt = `Evaluate this investment scenario answer on a scale of 0-1 (0 = completely wrong, 1 = excellent answer).

Scenario: ${question.scenario}

User's Answer: ${answer}

Provide ONLY a number between 0 and 1 as the score. Consider:
- Understanding of investment principles
- Practical approach
- Risk management
- Logical reasoning

Score (0-1):`;
        
        try {
            const response = await API.request(CONFIG.getGeminiUrl(), {
                method: 'POST',
                body: JSON.stringify({
                    contents: [{ parts: [{ text: prompt }] }]
                })
            });
            
            const scoreText = response.candidates[0].content.parts[0].text;
            const scoreMatch = scoreText.match(/([0-9]*\.?[0-9]+)/);
            
            if (scoreMatch) {
                const questionScore = parseFloat(scoreMatch[1]);
                totalScore += Math.min(Math.max(questionScore, 0), 1);
            }
        } catch (error) {
            console.error('Error evaluating question', i + 1, error);
            // Give partial credit if AI fails
            totalScore += 0.5;
        }
    }
    
    return totalScore;
}

function displayResults(score, total, timeTaken) {
    Utils.hideLoader();
    
    const percentage = Math.round((score / total) * 100);
    
    document.getElementById('quizContainer').style.display = 'none';
    document.getElementById('quizResults').style.display = 'block';
    
    // Update results
    document.getElementById('scoreValue').textContent = `${percentage}%`;
    document.getElementById('correctAnswers').textContent = `${Math.round(score)}/${total}`;
    
    const minutes = Math.floor(timeTaken / 60);
    const seconds = timeTaken % 60;
    document.getElementById('timeTaken').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    // Performance rating
    let performance = 'Needs Improvement';
    let icon = '📚';
    
    if (percentage >= 90) {
        performance = 'Excellent';
        icon = '🏆';
    } else if (percentage >= 75) {
        performance = 'Very Good';
        icon = '🌟';
    } else if (percentage >= 60) {
        performance = 'Good';
        icon = '👍';
    } else if (percentage >= 40) {
        performance = 'Fair';
        icon = '📖';
    }
    
    document.getElementById('performance').textContent = performance;
    document.getElementById('resultsIcon').textContent = icon;
    document.getElementById('resultsTitle').textContent = percentage >= 60 ? 'Great Job!' : 'Keep Learning!';
    
    // Save quiz result
    saveQuizResult({
        type: currentQuizType,
        score: score,
        total: total,
        percentage: percentage,
        timeTaken: timeTaken,
        date: new Date().toISOString()
    });
}

function saveQuizResult(result) {
    const results = Utils.getFromStorage('quiz_results') || [];
    results.push(result);
    Utils.saveToStorage('quiz_results', results);
}

function resetQuiz() {
    currentQuizType = null;
    currentQuestionIndex = 0;
    userAnswers = [];
    
    document.getElementById('quizResults').style.display = 'none';
    document.getElementById('quizSelection').style.display = 'block';
}

function startTimer(seconds) {
    let remaining = seconds;
    
    timerInterval = setInterval(() => {
        remaining--;
        
        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        
        document.getElementById('quizTimer').textContent = `⏱️ ${minutes}:${secs.toString().padStart(2, '0')}`;
        
        if (remaining <= 0) {
            clearInterval(timerInterval);
            submitQuiz();
        }
    }, 1000);
}