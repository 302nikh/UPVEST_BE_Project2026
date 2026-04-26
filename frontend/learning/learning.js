/* ============================================
   UPVEST - Learning Page JavaScript
   Handles video loading, MCQ tests, and scenario tests
   ============================================ */

let currentModule = null;

// Module data with questions and video URLs
// TO ADD YOUR OWN VIDEOS: Replace the videoUrl with your YouTube video ID
// Example: If your video URL is https://www.youtube.com/watch?v=dQw4w9WgXcQ
// Use just the ID: 'dQw4w9WgXcQ'
const modules = {
    'fundamentals': {
        title: 'Fundamentals of Investment & Stocks',
        videoUrl: 'https://www.youtube.com/embed/qIw-yFC-HNU', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is a stock?',
                options: ['A loan to a company', 'Ownership share in a company', 'A government bond', 'A type of mutual fund'],
                correct: 'b'
            },
            {
                question: 'What does IPO stand for?',
                options: ['International Public Offering', 'Initial Price Offering', 'Initial Public Offering', 'Investment Portfolio Organization'],
                correct: 'c'
            },
            {
                question: 'Which stock exchange is the largest in India?',
                options: ['BSE', 'NSE', 'MCX', 'NCDEX'],
                correct: 'b'
            },
            {
                question: 'What is market capitalization?',
                options: ['Total number of shares', 'Share price multiplied by total shares', 'Annual revenue of a company', 'Total debt of a company'],
                correct: 'b'
            },
            {
                question: 'What does a stockbroker do?',
                options: ['Lends money to companies', 'Facilitates buying and selling of stocks', 'Manufactures stock certificates', 'Manages company finances'],
                correct: 'b'
            }
        ],
        scenario: 'You have ₹50,000 to invest. The market has dropped 20% in the last month. Several good companies are now trading at lower prices. What would be your investment strategy and why?'
    },
    'risk': {
        title: 'Understanding Risk & Portfolio Management',
        videoUrl: 'https://www.youtube.com/embed/4KGvoy_Ke9Y', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is diversification?',
                options: ['Investing all money in one stock', 'Spreading investments across different assets', 'Only investing in stocks', 'Avoiding all risks'],
                correct: 'b'
            },
            {
                question: 'What is portfolio rebalancing?',
                options: ['Selling all stocks', 'Adjusting asset allocation to maintain desired risk level', 'Only buying new stocks', 'Investing more money'],
                correct: 'b'
            },
            {
                question: 'Which asset is generally considered lowest risk?',
                options: ['Stocks', 'Cryptocurrencies', 'Government bonds', 'Commodities'],
                correct: 'c'
            },
            {
                question: 'What is risk tolerance?',
                options: ['Amount of money you can invest', 'Ability to withstand investment losses', 'Maximum number of stocks to own', 'Time to retirement'],
                correct: 'b'
            },
            {
                question: 'What is a beta in portfolio management?',
                options: ['Total return percentage', 'Volatility relative to market', 'Number of assets', 'Dividend yield'],
                correct: 'b'
            }
        ],
        scenario: 'Your portfolio has 80% stocks and 20% bonds. After a market rally, stocks now make up 90% of your portfolio. What should you do and why?'
    },
    'technical': {
        title: 'Technical Analysis Basics',
        videoUrl: 'https://www.youtube.com/embed/Yv2iYYewdf0', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is a candlestick chart?',
                options: ['A type of stock', 'A visual representation of price movements', 'A company report', 'A trading platform'],
                correct: 'b'
            },
            {
                question: 'What does RSI stand for?',
                options: ['Real Stock Index', 'Relative Strength Index', 'Risk Safety Index', 'Return on Stock Investment'],
                correct: 'b'
            },
            {
                question: 'What is a support level?',
                options: ['Price at which stock tends to stop falling', 'Maximum price of a stock', 'Company valuation', 'Dividend rate'],
                correct: 'a'
            },
            {
                question: 'What is a moving average?',
                options: ['Average of recent prices', 'Total annual return', 'Company average profit', 'Broker commission'],
                correct: 'a'
            },
            {
                question: 'What does a bullish pattern indicate?',
                options: ['Price likely to fall', 'Price likely to rise', 'No price change', 'Market closure'],
                correct: 'b'
            }
        ],
        scenario: 'You notice a stock has bounced off the ₹500 level three times in the past month, but recently broke below it. What does this signal and how should you react?'
    },
    'fundamental': {
        title: 'Fundamental Analysis & Company Valuation',
        videoUrl: 'https://www.youtube.com/embed/4equfbG-OkQ', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is P/E ratio?',
                options: ['Profit/Equity ratio', 'Price/Earnings ratio', 'Portfolio/Expense ratio', 'Price/Equity ratio'],
                correct: 'b'
            },
            {
                question: 'What does EPS stand for?',
                options: ['Earnings Per Share', 'Equity Per Stock', 'Earnings Per Sector', 'Expected Profit Share'],
                correct: 'a'
            },
            {
                question: 'Which financial statement shows company profitability?',
                options: ['Balance Sheet', 'Cash Flow Statement', 'Income Statement', 'Annual Report'],
                correct: 'c'
            },
            {
                question: 'What is ROE (Return on Equity)?',
                options: ['Revenue divided by expenses', 'Net income divided by shareholder equity', 'Total sales divided by assets', 'Stock price divided by book value'],
                correct: 'b'
            },
            {
                question: 'What is the debt-to-equity ratio?',
                options: ['Measures company profitability', 'Measures financial leverage', 'Measures stock volatility', 'Measures dividend yield'],
                correct: 'b'
            }
        ],
        scenario: 'Company A has a P/E ratio of 50 and 30% annual growth. Company B has a P/E of 15 and 5% annual growth. Which is a better investment and why?'
    },
    'mutual-funds': {
        title: 'Mutual Funds & ETFs',
        videoUrl: 'https://www.youtube.com/embed/Es3vXJ7GoV8', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is a mutual fund?',
                options: ['A single stock', 'Pool of money from multiple investors', 'A type of loan', 'A government scheme'],
                correct: 'b'
            },
            {
                question: 'What does ETF stand for?',
                options: ['Exchange Traded Fund', 'Equity Trading Fund', 'Electronic Transfer Fund', 'Expected Trade Frequency'],
                correct: 'a'
            },
            {
                question: 'What is NAV?',
                options: ['New Asset Value', 'Net Annual Value', 'Net Asset Value', 'National Average Value'],
                correct: 'c'
            },
            {
                question: 'What is the main difference between ETF and mutual fund?',
                options: ['ETFs trade like stocks on exchanges', 'Mutual funds are riskier', 'ETFs only invest in tech stocks', 'Mutual funds have no fees'],
                correct: 'a'
            },
            {
                question: 'What is an expense ratio?',
                options: ['Annual fund operating costs', 'Stock market volatility', 'Dividend percentage', 'Broker commission'],
                correct: 'a'
            }
        ],
        scenario: 'You want to invest ₹10,000 monthly for 10 years. Should you choose an index ETF or an actively managed mutual fund? Explain your reasoning.'
    },
    'psychology': {
        title: 'Trading Psychology & Discipline',
        videoUrl: 'https://www.youtube.com/embed/F_WxllDE2TA', // Change this to your video URL
        mcqQuestions: [
            {
                question: 'What is FOMO in trading?',
                options: ['Fear of Missing Out', 'Future Options Money Opportunity', 'Financial Outcome Monitoring', 'Fixed Order Management'],
                correct: 'a'
            },
            {
                question: 'What is a stop-loss order?',
                options: ['Order to buy more stocks', 'Order to sell at a predetermined price to limit loss', 'Order to stop trading', 'Order to increase investment'],
                correct: 'b'
            },
            {
                question: 'What is emotional trading?',
                options: ['Trading based on analysis', 'Trading based on feelings rather than strategy', 'Trading with friends', 'Trading during holidays'],
                correct: 'b'
            },
            {
                question: 'What is confirmation bias in investing?',
                options: ['Seeking information that supports existing beliefs', 'Confirming stock purchases', 'Verifying broker credentials', 'Checking account balance'],
                correct: 'a'
            },
            {
                question: 'What does "Buy low, sell high" mean?',
                options: ['Buy stocks in the morning', 'Purchase undervalued assets and sell when overvalued', 'Buy small companies only', 'Sell during holidays'],
                correct: 'b'
            }
        ],
        scenario: 'You bought a stock at ₹100. It dropped to ₹80. You\'re tempted to sell to avoid further loss, but your analysis says it\'s still a good company. What should you do?'
    }
};

/**
 * Open Video Modal
 */
function openVideoModal(moduleId) {
    currentModule = moduleId;
    const modal = document.getElementById('videoModal');
    const title = document.getElementById('videoModalTitle');
    const player = document.getElementById('videoPlayer');
    const playerContainer = document.getElementById('videoPlayerContainer');
    const inputSection = document.querySelector('.video-input-section');

    title.textContent = `Watch Video - ${modules[moduleId].title}`;

    // Auto-load video from module data
    if (modules[moduleId].videoUrl) {
        player.src = modules[moduleId].videoUrl;
        playerContainer.style.display = 'block';
        inputSection.style.display = 'none'; // Hide input section
    } else {
        playerContainer.style.display = 'none';
        inputSection.style.display = 'block';
        document.getElementById('youtubeUrlInput').value = '';
    }

    modal.classList.add('active');

    console.log(`✅ Video loaded for ${moduleId}`);
}

/**
 * Load YouTube Video
 */
function loadVideo() {
    const urlInput = document.getElementById('youtubeUrlInput');
    const url = urlInput.value.trim();

    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    // Extract video ID from YouTube URL
    let videoId = '';
    if (url.includes('youtube.com/watch?v=')) {
        videoId = url.split('v=')[1].split('&')[0];
    } else if (url.includes('youtu.be/')) {
        videoId = url.split('youtu.be/')[1].split('?')[0];
    } else {
        alert('Invalid YouTube URL. Please use format: https://www.youtube.com/watch?v=...');
        return;
    }

    // Load video in iframe
    const playerContainer = document.getElementById('videoPlayerContainer');
    const player = document.getElementById('videoPlayer');

    player.src = `https://www.youtube.com/embed/${videoId}`;
    playerContainer.style.display = 'block';

    console.log(`✅ Video loaded: ${videoId}`);
}

/**
 * Open MCQ Test Modal
 */
function openMCQModal(moduleId) {
    currentModule = moduleId;
    const modal = document.getElementById('mcqModal');
    const title = document.getElementById('mcqModalTitle');
    const form = document.getElementById('mcqForm');

    title.textContent = `MCQ Test - ${modules[moduleId].title}`;

    // Generate questions
    const questions = modules[moduleId].mcqQuestions;
    let formHTML = '';

    questions.forEach((q, index) => {
        formHTML += `
            <div class="question-block">
                <h4>Question ${index + 1}</h4>
                <p style="margin-bottom: 16px; color: #475569; font-size: 14px;">${q.question}</p>
                <div class="options">
                    ${q.options.map((opt, i) => `
                        <label>
                            <input type="radio" name="q${index + 1}" value="${String.fromCharCode(97 + i)}">
                            Option ${String.fromCharCode(65 + i)}: ${opt}
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
    });

    formHTML += '<button type="submit" class="btn-submit">Submit Test</button>';
    form.innerHTML = formHTML;

    // Add submit handler
    form.onsubmit = (e) => {
        e.preventDefault();
        evaluateMCQ(moduleId);
    };

    modal.classList.add('active');
}

/**
 * Evaluate MCQ Test
 */
function evaluateMCQ(moduleId) {
    const questions = modules[moduleId].mcqQuestions;
    const form = document.getElementById('mcqForm');
    let score = 0;
    let results = [];

    questions.forEach((q, index) => {
        const selected = form.querySelector(`input[name="q${index + 1}"]:checked`);
        const isCorrect = selected && selected.value === q.correct;

        if (isCorrect) score++;

        results.push({
            question: index + 1,
            correct: isCorrect,
            selected: selected ? selected.value : 'none',
            correctAnswer: q.correct
        });
    });

    const percentage = (score / questions.length) * 100;
    const passed = percentage >= 60;

    // Show results
    const resultHTML = `
        <div style="text-align: center; padding: 30px;">
            <div style="font-size: 48px; margin-bottom: 16px;">
                ${passed ? '🎉' : '📚'}
            </div>
            <h3 style="font-size: 24px; margin-bottom: 12px; color: ${passed ? '#16a34a' : '#dc2626'};">
                ${passed ? 'Test Passed!' : 'Keep Learning!'}
            </h3>
            <p style="font-size: 18px; color: #475569; margin-bottom: 20px;">
                Score: ${score} / ${questions.length} (${percentage.toFixed(0)}%)
            </p>
            <p style="color: #64748b; margin-bottom: 24px;">
                ${passed ? 'Great job! You can proceed to the next module.' : 'Review the material and try again to score above 60%.'}
            </p>
            <button onclick="closeModal('mcqModal')" class="btn-primary">Close</button>
        </div>
    `;

    document.getElementById('mcqForm').innerHTML = resultHTML;

    console.log(`MCQ Results for ${moduleId}:`, results);
}

/**
 * Open Scenario Test Modal
 */
function openScenarioModal(moduleId) {
    currentModule = moduleId;
    const modal = document.getElementById('scenarioModal');
    const title = document.getElementById('scenarioModalTitle');
    const scenarioText = document.getElementById('scenarioText');
    const answerTextarea = document.getElementById('scenarioAnswer');
    const evaluationResult = document.getElementById('evaluationResult');

    title.textContent = `Scenario Test - ${modules[moduleId].title}`;
    scenarioText.textContent = modules[moduleId].scenario;
    answerTextarea.value = '';
    evaluationResult.style.display = 'none';

    modal.classList.add('active');
}

/**
 * Submit Scenario for AI Evaluation
 */
async function submitScenario() {
    const answer = document.getElementById('scenarioAnswer').value.trim();

    if (!answer || answer.length < 50) {
        alert('Please provide a detailed answer (minimum 50 characters)');
        return;
    }

    const evaluationResult = document.getElementById('evaluationResult');
    evaluationResult.innerHTML = '<p style="text-align: center; color: #7c3aed;">🤖 Evaluating your answer with AI...</p>';
    evaluationResult.style.display = 'block';

    try {
        // Call Gemini API for evaluation
        const scenario = modules[currentModule].scenario;
        const prompt = `You are an investment education expert. Evaluate this student's answer to an investment scenario question.

Scenario: ${scenario}

Student's Answer: ${answer}

Provide a constructive evaluation covering:
1. Strengths of the answer
2. Areas for improvement
3. Key concepts they understood/missed
4. A score out of 10
5. Encouragement for their learning journey

Keep the tone supportive and educational.`;

        const response = await fetch(CONFIG.getGeminiUrl(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }]
            })
        });

        const data = await response.json();
        const evaluation = data.candidates[0].content.parts[0].text;

        evaluationResult.innerHTML = `
            <h4>✨ AI Evaluation</h4>
            <div style="white-space: pre-wrap; line-height: 1.7;">${evaluation}</div>
        `;
        evaluationResult.style.background = '#f0fdf4';
        evaluationResult.style.borderColor = '#bbf7d0';

        console.log('✅ Scenario evaluated successfully');

    } catch (error) {
        console.error('Error evaluating scenario:', error);
        // Fallback to Mock Evaluation
        const mockEvaluation = getMockEvaluation(modules[currentModule].scenario, answer);

        evaluationResult.innerHTML = `
            <h4>✨ AI Evaluation (Demo Mode)</h4>
            <div style="white-space: pre-wrap; line-height: 1.7;">${mockEvaluation}</div>
        `;
        evaluationResult.style.background = '#f0fdf4';
        evaluationResult.style.borderColor = '#bbf7d0';
    }
}

/**
 * Generate Mock Evaluation (Fallback)
 */
function getMockEvaluation(scenario, answer) {
    const score = Math.floor(Math.random() * 3) + 7; // Random score 7-9

    return `**Strengths:**\nAn excellent attempt! You've grasped the core concept of the scenario. Your reasoning aligns well with standard investment principles, particularly regarding risk assessment and strategic decision-making.\n\n**Areas for Improvement:**\nConsider diving deeper into the long-term implications of your choice. A more detailed quantitative analysis could strengthen your argument further.\n\n**Key Concepts:**\n- Risk vs. Reward tradeoff\n- Market sentiment analysis\n- Asset allocation dynamics\n\n**Score:** ${score}/10\n\n**Keep it up!** You're on the right track to becoming a savvy investor.`;
}

/**
 * Close Modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');

    // Stop video if closing video modal
    if (modalId === 'videoModal') {
        document.getElementById('videoPlayer').src = '';
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Learning page initialized');
    console.log('📚 Modules available:', Object.keys(modules));
});
