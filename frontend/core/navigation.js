/* ============================================
   UPVEST - Navigation & Routing
   Page navigation and authentication guards
   ============================================ */

const Navigation = {
    
    // === Authentication State ===
    
    /**
     * Check if user is logged in
     * @returns {boolean} Login status
     */
    isLoggedIn() {
        const user = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.USER);
        return user !== null && user.email;
    },
    
    /**
     * Get current user data
     * @returns {object|null} User object
     */
    getCurrentUser() {
        return Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.USER);
    },
    
    /**
     * Save user session
     * @param {object} userData - User data to save
     */
    saveUserSession(userData) {
        Utils.saveToStorage(CONFIG.SETTINGS.STORAGE_KEYS.USER, userData);
        Utils.saveToStorage(CONFIG.SETTINGS.STORAGE_KEYS.AUTH_TOKEN, {
            token: Utils.generateId(32),
            timestamp: new Date().toISOString()
        });
    },
    
    /**
     * Clear user session (logout)
     */
    clearUserSession() {
        const keysToRemove = [
            CONFIG.SETTINGS.STORAGE_KEYS.USER,
            CONFIG.SETTINGS.STORAGE_KEYS.AUTH_TOKEN
        ];
        
        keysToRemove.forEach(key => Utils.removeFromStorage(key));
    },
    
    /**
     * Logout and redirect to login page
     */
    logout() {
        this.clearUserSession();
        Utils.showToast('Logged out successfully', 'success');
        this.redirectTo('../auth/login.html');
    },
    
    // === Route Guards ===
    
    /**
     * Protect route - redirect to login if not authenticated
     * Call this at the top of protected pages
     */
    requireAuth() {
        if (!this.isLoggedIn()) {
            Utils.showToast(CONFIG.ERRORS.AUTH_REQUIRED, 'warning');
            this.redirectTo('../auth/login.html');
            return false;
        }
        return true;
    },
    
    /**
     * Redirect authenticated users away from auth pages
     * Call this on login/signup pages
     */
    redirectIfAuthenticated() {
        if (this.isLoggedIn()) {
            this.redirectTo('../home/dashboard.html');
            return true;
        }
        return false;
    },
    
    // === Navigation Methods ===
    
    /**
     * Redirect to a page
     * @param {string} path - Relative or absolute path
     */
    redirectTo(path) {
        window.location.href = path;
    },
    
    /**
     * Go to home/dashboard
     */
    goToHome() {
        this.redirectTo('../home/dashboard.html');
    },
    
    /**
     * Go to login page
     */
    goToLogin() {
        this.redirectTo('../auth/login.html');
    },
    
    /**
     * Go to signup page
     */
    goToSignup() {
        this.redirectTo('../auth/signup.html');
    },
    
    /**
     * Go to learning page
     */
    goToLearning() {
        this.redirectTo('../learning/learning.html');
    },
    
    /**
     * Go to AI bot page
     */
    goToBot() {
        this.redirectTo('../ai-bot/bot-dashboard.html');
    },
    
    /**
     * Go to helpdesk page
     */
    goToHelp() {
        this.redirectTo('../helpdesk/help.html');
    },
    
    /**
     * Go to quiz page
     * @param {string} type - 'mcq' or 'scenario'
     */
    goToQuiz(type = 'mcq') {
        Utils.saveToStorage('quiz_type', type);
        this.redirectTo('../quiz/quiz.html');
    },
    
    /**
     * Go back to previous page
     */
    goBack() {
        window.history.back();
    },
    
    /**
     * Reload current page
     */
    reload() {
        window.location.reload();
    },
    
    // === Navbar Highlight ===
    
    /**
     * Highlight active nav link based on current page
     */
    highlightActiveNavLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // Check if current page matches link
            if (currentPath.includes(href.split('/').pop())) {
                link.classList.add('active');
                link.style.color = 'var(--primary-color)';
                link.style.fontWeight = 'var(--font-weight-bold)';
            } else {
                link.classList.remove('active');
            }
        });
    },
    
    // === Session Management ===
    
    /**
     * Check session validity and refresh if needed
     */
    checkSession() {
        const authToken = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.AUTH_TOKEN);
        
        if (!authToken) return false;
        
        const tokenTime = new Date(authToken.timestamp);
        const now = new Date();
        const timeDiff = now - tokenTime;
        
        // Check if session expired
        if (timeDiff > CONFIG.SETTINGS.SESSION_TIMEOUT) {
            Utils.showToast(CONFIG.ERRORS.SESSION_EXPIRED, 'warning');
            this.logout();
            return false;
        }
        
        return true;
    },
    
    /**
     * Initialize session checker (call on protected pages)
     */
    initSessionChecker() {
        // Check session on page load
        this.checkSession();
        
        // Check session every 5 minutes
        setInterval(() => {
            this.checkSession();
        }, 300000); // 5 minutes
    },
    
    // === Breadcrumb Navigation ===
    
    /**
     * Get breadcrumb trail based on current page
     * @returns {Array} Breadcrumb items
     */
    getBreadcrumbs() {
        const currentPath = window.location.pathname;
        const breadcrumbs = [{ name: 'Home', path: '../home/dashboard.html' }];
        
        if (currentPath.includes('learning')) {
            breadcrumbs.push({ name: 'Learning', path: '../learning/learning.html' });
        } else if (currentPath.includes('quiz')) {
            breadcrumbs.push({ name: 'Learning', path: '../learning/learning.html' });
            breadcrumbs.push({ name: 'Quiz', path: '../quiz/quiz.html' });
        } else if (currentPath.includes('ai-bot') || currentPath.includes('bot-dashboard')) {
            breadcrumbs.push({ name: 'AI Bot', path: '../ai-bot/bot-dashboard.html' });
        } else if (currentPath.includes('helpdesk') || currentPath.includes('help')) {
            breadcrumbs.push({ name: 'Help & Support', path: '../helpdesk/help.html' });
        }
        
        return breadcrumbs;
    },
    
    /**
     * Render breadcrumb navigation
     * @param {string} containerId - Container element ID
     */
    renderBreadcrumbs(containerId = 'breadcrumb-container') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const breadcrumbs = this.getBreadcrumbs();
        const html = breadcrumbs.map((item, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return `
                <span>
                    ${isLast 
                        ? `<span style="color: var(--text-muted)">${item.name}</span>`
                        : `<a href="${item.path}" style="color: var(--primary-color)">${item.name}</a>`
                    }
                    ${!isLast ? '<span style="margin: 0 8px; color: var(--text-muted)">›</span>' : ''}
                </span>
            `;
        }).join('');
        
        container.innerHTML = html;
    },
    
    // === Deep Linking ===
    
    /**
     * Get URL parameters
     * @returns {object} URL parameters as key-value pairs
     */
    getUrlParams() {
        const params = {};
        const searchParams = new URLSearchParams(window.location.search);
        
        for (const [key, value] of searchParams) {
            params[key] = value;
        }
        
        return params;
    },
    
    /**
     * Add URL parameter
     * @param {string} key - Parameter key
     * @param {string} value - Parameter value
     */
    addUrlParam(key, value) {
        const url = new URL(window.location.href);
        url.searchParams.set(key, value);
        window.history.pushState({}, '', url);
    },
    
    /**
     * Get specific URL parameter
     * @param {string} key - Parameter key
     * @returns {string|null} Parameter value
     */
    getUrlParam(key) {
        const params = this.getUrlParams();
        return params[key] || null;
    },
    
    // === Page Initialization ===
    
    /**
     * Initialize navigation for protected pages
     * Call this at the top of every protected page
     */
    initProtectedPage() {
        // Check authentication
        if (!this.requireAuth()) return false;
        
        // Initialize session checker
        this.initSessionChecker();
        
        // Highlight active nav link
        this.highlightActiveNavLink();
        
        // Display user info in navbar
        this.displayUserInfo();
        
        return true;
    },
    
    /**
     * Display user info in navbar
     */
    displayUserInfo() {
        const user = this.getCurrentUser();
        if (!user) return;
        
        // Update user name if element exists
        const userNameElements = document.querySelectorAll('.user-name, #userName');
        userNameElements.forEach(el => {
            el.textContent = user.name || user.email.split('@')[0];
        });
        
        // Update user email if element exists
        const userEmailElements = document.querySelectorAll('.user-email, #userEmail');
        userEmailElements.forEach(el => {
            el.textContent = user.email;
        });
    },
    
    /**
     * Setup logout button handlers
     */
    setupLogoutHandlers() {
        const logoutButtons = document.querySelectorAll('.logout-btn, #logoutBtn');
        
        logoutButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Confirm logout
                if (confirm('Are you sure you want to logout?')) {
                    this.logout();
                }
            });
        });
    },
    
    // === Navigation History ===
    
    /**
     * Save current page to history
     */
    savePageToHistory() {
        const history = Utils.getFromStorage('navigation_history') || [];
        const currentPage = {
            path: window.location.pathname,
            timestamp: new Date().toISOString()
        };
        
        history.push(currentPage);
        
        // Keep only last 10 pages
        if (history.length > 10) {
            history.shift();
        }
        
        Utils.saveToStorage('navigation_history', history);
    },
    
    /**
     * Get navigation history
     * @returns {Array} Navigation history
     */
    getNavigationHistory() {
        return Utils.getFromStorage('navigation_history') || [];
    }
};

// === Auto-initialize on page load ===
document.addEventListener('DOMContentLoaded', () => {
    // Setup logout handlers if buttons exist
    Navigation.setupLogoutHandlers();
    
    // Save page to history
    Navigation.savePageToHistory();
    
    // Check if on auth page and user is already logged in
    if (window.location.pathname.includes('/auth/')) {
        Navigation.redirectIfAuthenticated();
    }
});

// === Global logout function for easy access ===
window.logout = () => Navigation.logout();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Navigation;
}