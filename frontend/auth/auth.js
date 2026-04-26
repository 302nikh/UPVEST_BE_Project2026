/* ============================================
   UPVEST - Authentication Logic
   Login and Signup functionality
   ============================================ */

const Auth = {
    
    // === Login Function ===
    
    /**
     * Handle user login
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<boolean>} Login success status
     */
    async login(email, password) {
        try {
            // Validate inputs
            if (!this.validateEmail(email)) {
                throw new Error('Please enter a valid email address');
            }
            
            if (!password || password.length < 6) {
                throw new Error('Password must be at least 6 characters');
            }
            
            // Show loading
            Utils.showLoader('Logging in...');
            
            // Simulate API call delay (remove in production with real backend)
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Get stored users (demo mode)
            const users = Utils.getFromStorage('upvest_users') || [];
            
            // Find user
            const user = users.find(u => u.email === email);
            
            if (!user) {
                throw new Error('Account not found. Please sign up first.');
            }
            
            // Verify password (in production, this would be hashed)
            if (user.password !== password) {
                throw new Error('Incorrect password. Please try again.');
            }
            
            // Save user session
            const sessionData = {
                id: user.id,
                email: user.email,
                name: user.name,
                loginTime: new Date().toISOString()
            };
            
            Navigation.saveUserSession(sessionData);
            
            // Hide loader
            Utils.hideLoader();
            
            // Show success message
            Utils.showToast(CONFIG.SUCCESS.LOGIN, 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                Navigation.goToHome();
            }, 500);
            
            return true;
            
        } catch (error) {
            Utils.hideLoader();
            Utils.showToast(error.message, 'error');
            return false;
        }
    },
    
    // === Signup Function ===
    
    /**
     * Handle user signup
     * @param {object} userData - User registration data
     * @returns {Promise<boolean>} Signup success status
     */
    async signup(userData) {
        try {
            const { name, email, password, confirmPassword } = userData;
            
            // Validate name
            if (!name || name.trim().length < 2) {
                throw new Error('Please enter your full name');
            }
            
            // Validate email
            if (!this.validateEmail(email)) {
                throw new Error('Please enter a valid email address');
            }
            
            // Validate password
            const passwordValidation = this.validatePassword(password);
            if (!passwordValidation.isValid) {
                throw new Error('Password must be at least 8 characters with uppercase, lowercase, and numbers');
            }
            
            // Confirm password match
            if (password !== confirmPassword) {
                throw new Error('Passwords do not match');
            }
            
            // Show loading
            Utils.showLoader('Creating your account...');
            
            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Get existing users
            const users = Utils.getFromStorage('upvest_users') || [];
            
            // Check if email already exists
            const existingUser = users.find(u => u.email === email);
            if (existingUser) {
                throw new Error('Email already registered. Please login instead.');
            }
            
            // Create new user
            const newUser = {
                id: Utils.generateId(16),
                name: name.trim(),
                email: email.toLowerCase(),
                password: password, // In production, this should be hashed
                createdAt: new Date().toISOString()
            };
            
            // Save user
            users.push(newUser);
            Utils.saveToStorage('upvest_users', users);
            
            // Auto-login after signup
            const sessionData = {
                id: newUser.id,
                email: newUser.email,
                name: newUser.name,
                loginTime: new Date().toISOString()
            };
            
            Navigation.saveUserSession(sessionData);
            
            // Hide loader
            Utils.hideLoader();
            
            // Show success message
            Utils.showToast(CONFIG.SUCCESS.SIGNUP, 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                Navigation.goToHome();
            }, 500);
            
            return true;
            
        } catch (error) {
            Utils.hideLoader();
            Utils.showToast(error.message, 'error');
            return false;
        }
    },
    
    // === Validation Functions ===
    
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} Valid status
     */
    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    /**
     * Validate password strength
     * @param {string} password - Password to validate
     * @returns {object} Validation result
     */
    validatePassword(password) {
        return {
            isValid: password.length >= 8 &&
                     /[A-Z]/.test(password) &&
                     /[a-z]/.test(password) &&
                     /\d/.test(password),
            hasMinLength: password.length >= 8,
            hasUpperCase: /[A-Z]/.test(password),
            hasLowerCase: /[a-z]/.test(password),
            hasNumber: /\d/.test(password)
        };
    },
    
    /**
     * Calculate password strength
     * @param {string} password - Password to check
     * @returns {string} Strength level: 'weak', 'medium', 'strong'
     */
    getPasswordStrength(password) {
        let strength = 0;
        
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
        
        if (strength <= 2) return 'weak';
        if (strength <= 4) return 'medium';
        return 'strong';
    },
    
    // === UI Helper Functions ===
    
    /**
     * Show password strength indicator
     * @param {HTMLElement} input - Password input element
     * @param {HTMLElement} indicator - Strength indicator element
     */
    updatePasswordStrength(input, indicator) {
        const password = input.value;
        const strength = this.getPasswordStrength(password);
        
        const strengthBar = indicator.querySelector('.password-strength-bar');
        const strengthText = indicator.querySelector('.password-strength-text');
        
        if (password.length === 0) {
            indicator.classList.remove('visible');
            return;
        }
        
        indicator.classList.add('visible');
        strengthBar.className = `password-strength-bar ${strength}`;
        
        const messages = {
            weak: 'Weak password',
            medium: 'Medium strength',
            strong: 'Strong password'
        };
        
        strengthText.textContent = messages[strength];
        strengthText.style.color = strength === 'weak' ? 'var(--danger-color)' :
                                    strength === 'medium' ? 'var(--warning-color)' :
                                    'var(--success-color)';
    },
    
    /**
     * Toggle password visibility
     * @param {HTMLElement} input - Password input element
     * @param {HTMLElement} toggleBtn - Toggle button element
     */
    togglePasswordVisibility(input, toggleBtn) {
        const type = input.type === 'password' ? 'text' : 'password';
        input.type = type;
        
        // Update icon (using emoji for simplicity)
        toggleBtn.textContent = type === 'password' ? '👁️' : '🙈';
    },
    
    /**
     * Validate form field on blur
     * @param {HTMLElement} input - Input element
     */
    validateField(input) {
        const value = input.value.trim();
        const type = input.type;
        const name = input.name;
        
        let isValid = true;
        let errorMessage = '';
        
        if (name === 'email') {
            isValid = this.validateEmail(value);
            errorMessage = 'Please enter a valid email address';
        } else if (type === 'password' && name === 'password') {
            const validation = this.validatePassword(value);
            isValid = validation.isValid;
            errorMessage = 'Password must be 8+ characters with uppercase, lowercase, and numbers';
        } else if (name === 'confirmPassword') {
            const passwordInput = document.querySelector('input[name="password"]');
            isValid = value === passwordInput.value;
            errorMessage = 'Passwords do not match';
        } else if (name === 'name') {
            isValid = value.length >= 2;
            errorMessage = 'Please enter your full name';
        }
        
        // Update UI
        if (isValid) {
            input.classList.remove('error');
            input.classList.add('success');
        } else {
            input.classList.remove('success');
            input.classList.add('error');
            
            // Show error message
            let errorElement = input.nextElementSibling;
            if (!errorElement || !errorElement.classList.contains('form-error')) {
                errorElement = document.createElement('div');
                errorElement.className = 'form-error';
                input.parentNode.insertBefore(errorElement, input.nextSibling);
            }
            errorElement.textContent = errorMessage;
        }
        
        return isValid;
    },
    
    /**
     * Clear form validation states
     * @param {HTMLFormElement} form - Form element
     */
    clearFormValidation(form) {
        const inputs = form.querySelectorAll('.form-input');
        inputs.forEach(input => {
            input.classList.remove('error', 'success');
        });
        
        const errors = form.querySelectorAll('.form-error');
        errors.forEach(error => error.remove());
    }
};

// === Initialize Authentication Page ===
document.addEventListener('DOMContentLoaded', () => {
    
    // Check if user is already logged in and redirect
    Navigation.redirectIfAuthenticated();
    
    // === Login Form Handler ===
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            await Auth.login(email, password);
        });
        
        // Add field validation on blur
        const loginInputs = loginForm.querySelectorAll('.form-input');
        loginInputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value.trim()) {
                    Auth.validateField(input);
                }
            });
        });
    }
    
    // === Signup Form Handler ===
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const userData = {
                name: document.getElementById('signupName').value.trim(),
                email: document.getElementById('signupEmail').value.trim(),
                password: document.getElementById('signupPassword').value,
                confirmPassword: document.getElementById('signupConfirmPassword').value
            };
            
            await Auth.signup(userData);
        });
        
        // Add field validation on blur
        const signupInputs = signupForm.querySelectorAll('.form-input');
        signupInputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value.trim()) {
                    Auth.validateField(input);
                }
            });
        });
        
        // Password strength indicator
        const passwordInput = document.getElementById('signupPassword');
        const strengthIndicator = document.getElementById('passwordStrength');
        
        if (passwordInput && strengthIndicator) {
            passwordInput.addEventListener('input', () => {
                Auth.updatePasswordStrength(passwordInput, strengthIndicator);
            });
        }
    }
    
    // === Password Toggle Handler ===
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            Auth.togglePasswordVisibility(input, toggle);
        });
    });
    
    // === Demo Account Button ===
    const demoLoginBtn = document.getElementById('demoLoginBtn');
    if (demoLoginBtn) {
        demoLoginBtn.addEventListener('click', async () => {
            // Create demo account if not exists
            const users = Utils.getFromStorage('upvest_users') || [];
            const demoUser = users.find(u => u.email === 'demo@upvest.com');
            
            if (!demoUser) {
                users.push({
                    id: 'demo-user-001',
                    name: 'Demo User',
                    email: 'demo@upvest.com',
                    password: 'Demo@123',
                    createdAt: new Date().toISOString()
                });
                Utils.saveToStorage('upvest_users', users);
            }
            
            // Auto-fill and login
            document.getElementById('loginEmail').value = 'demo@upvest.com';
            document.getElementById('loginPassword').value = 'Demo@123';
            
            await Auth.login('demo@upvest.com', 'Demo@123');
        });
    }
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Auth;
}