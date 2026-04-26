/* ============================================
   UPVEST - Help Desk JavaScript
   Gemini AI integration for chat support
   ============================================ */

const messagesArea = document.getElementById('messagesArea');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

let chatHistory = [];

/**
 * Initialize Help Desk
 */
function init() {
    // Send button click
    sendBtn.addEventListener('click', () => {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    console.log('✅ Help Desk initialized with Gemini AI');
}

/**
 * Send User Message
 */
function sendMessage(message) {
    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';

    // Disable send button
    sendBtn.disabled = true;

    // Show typing indicator
    const typingId = showTypingIndicator();

    // Get AI response
    getAIResponse(message).then(response => {
        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add bot response
        addMessage(response, 'bot');

        // Re-enable send button
        sendBtn.disabled = false;
    }).catch(error => {
        console.error('Error getting AI response:', error);

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Show error message
        addMessage('Sorry, I encountered an error. Please try again or check your internet connection.', 'bot');

        // Re-enable send button
        sendBtn.disabled = false;
    });
}

/**
 * Add Message to Chat
 */
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    if (type === 'bot') {
        avatar.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" fill="white"/>
                <path d="M4 20c0-4 4-6 8-6s8 2 8 6" stroke="white" stroke-width="2"/>
            </svg>
        `;
    } else {
        avatar.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="white"/>
                <path d="M12 6v6l4 2" stroke="#1a202c" stroke-width="2"/>
            </svg>
        `;
    }

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = `<p>${content}</p>`;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    messagesArea.appendChild(messageDiv);

    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;

    // Save to history
    chatHistory.push({ role: type, content: content });
}

/**
 * Show Typing Indicator
 */
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typing-indicator-' + Date.now();

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" fill="white"/>
            <path d="M4 20c0-4 4-6 8-6s8 2 8 6" stroke="white" stroke-width="2"/>
        </svg>
    `;

    const typingContent = document.createElement('div');
    typingContent.className = 'message-content';
    typingContent.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(typingContent);

    messagesArea.appendChild(typingDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;

    return typingDiv.id;
}

/**
 * Remove Typing Indicator
 */
function removeTypingIndicator(id) {
    const typingDiv = document.getElementById(id);
    if (typingDiv) {
        typingDiv.remove();
    }
}

/**
 * Get AI Response from Gemini
 */
/**
 * Get AI Response from Gemini
 */
async function getAIResponse(userMessage) {
    try {
        console.log('📤 Sending request to Gemini AI...');

        // Use the centralized API service
        // This handles configuration, prompts, and error handling (including mock fallback)
        const response = await API.getChatbotResponse(userMessage);

        console.log('✅ Received response from Gemini AI');
        return response;

    } catch (error) {
        console.error('❌ Error calling Gemini API:', error);
        throw error;
    }
}

/**
 * Ask Quick Question
 */
function askQuestion(question) {
    userInput.value = question;
    sendMessage(question);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
