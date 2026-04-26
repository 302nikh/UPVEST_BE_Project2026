/* ============================================
   UPVEST - Navbar JavaScript (Simplified)
   Mobile menu and logout functionality
   ============================================ */

function initNavbar() {
    // Update user info in navbar
    updateNavbarUserInfo();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Highlight active link
    highlightActiveLink();
}

/**
 * Update user info in navbar
 */
function updateNavbarUserInfo() {
    const user = Navigation.getCurrentUser();
    if (!user) {
        // Set default values if no user
        const avatarInitials = document.querySelector('.avatar-initials');
        const tooltipEmail = document.querySelector('.tooltip-email');
        
        if (avatarInitials) avatarInitials.textContent = 'N';
        if (tooltipEmail) tooltipEmail.textContent = 'nikhilsomwork@gmail.com';
        return;
    }
    
    const userName = user.name || user.email.split('@')[0];
    const userEmail = user.email || 'user@upvest.com';
    
    // Get initials
    const initials = userName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
    
    // Update avatar initials
    const avatarEl = document.querySelector('.avatar-initials');
    if (avatarEl) {
        avatarEl.textContent = initials;
    }
    
    // Update tooltip email
    const tooltipEmail = document.querySelector('.tooltip-email');
    if (tooltipEmail) {
        tooltipEmail.textContent = userEmail;
    }
}

/**
 * Initialize mobile menu
 */
function initMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const navbarLinks = document.querySelector('.navbar-links');
    const overlay = document.getElementById('overlay');
    
    if (!mobileMenuToggle || !navbarLinks) return;
    
    // Toggle menu on button click
    mobileMenuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        navbarLinks.classList.toggle('show');
        overlay.classList.toggle('show');
        mobileMenuToggle.classList.toggle('active');
    });
    
    // Close menu on overlay click
    overlay.addEventListener('click', () => {
        navbarLinks.classList.remove('show');
        overlay.classList.remove('show');
        mobileMenuToggle.classList.remove('active');
    });
    
    // Close menu when clicking a link (mobile)
    if (window.innerWidth <= 992) {
        navbarLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navbarLinks.classList.remove('show');
                overlay.classList.remove('show');
                mobileMenuToggle.classList.remove('active');
            });
        });
    }
}

/**
 * Highlight active navigation link
 */
function highlightActiveLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        
        if (!href || href === '#') return;
        
        // Check if current path matches link
        if (currentPath.includes('dashboard.html') && href.includes('dashboard.html')) {
            link.classList.add('active');
        } else if (currentPath.includes('learning') && href.includes('learning')) {
            link.classList.add('active');
        } else if (currentPath.includes('financial-planning') && href.includes('financial-planning')) {
            link.classList.add('active');
        } else if (currentPath.includes('quiz') && href.includes('quiz')) {
            link.classList.add('active');
        } else if (currentPath.includes('demat') && href.includes('demat')) {
            link.classList.add('active');
        } else if (currentPath.includes('ai-bot') && href.includes('ai-bot')) {
            link.classList.add('active');
        } else if (currentPath.includes('help') && href.includes('help')) {
            link.classList.add('active');
        }
    });
}

/**
 * Logout function - redirects to login page
 */
function logout() {
    // Confirm logout
    if (confirm('Are you sure you want to logout?')) {
        // Clear user data
        if (typeof Utils !== 'undefined' && Utils.clearUserSession) {
            Utils.clearUserSession();
        } else {
            // Fallback: clear localStorage
            localStorage.clear();
            sessionStorage.clear();
        }
        
        // Redirect to login page
        window.location.href = '../auth/login.html';
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavbar);
} else {
    initNavbar();
}
