/* ============================================
   UPVEST - Navbar JavaScript
   Navbar interactions and user menu
   ============================================ */

function initNavbar() {
    // Update user info in navbar
    updateNavbarUserInfo();
    
    // Initialize dropdowns
    initUserDropdown();
    
    // Initialize notifications
    initNotifications();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Highlight active link
    highlightActiveLink();
    
    // Scroll effect
    initScrollEffect();
}

/**
 * Update user info in navbar
 */
function updateNavbarUserInfo() {
    const user = Navigation.getCurrentUser();
    if (!user) return;
    
    const userName = user.name || user.email.split('@')[0];
    const userEmail = user.email;
    
    // Get initials
    const initials = userName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
    
    // Update all user name elements
    document.querySelectorAll('#userName, #userNameDropdown').forEach(el => {
        el.textContent = userName;
    });
    
    // Update email
    document.querySelectorAll('#userEmail').forEach(el => {
        el.textContent = userEmail;
    });
    
    // Update avatar initials
    document.querySelectorAll('#avatarInitials, #avatarInitialsLarge').forEach(el => {
        el.textContent = initials;
    });
}

/**
 * Initialize user dropdown
 */
function initUserDropdown() {
    const userProfileBtn = document.getElementById('userProfileBtn');
    const userDropdown = document.querySelector('.user-dropdown');
    const overlay = document.getElementById('overlay');
    
    if (!userProfileBtn || !userDropdown) return;
    
    userProfileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('active');
        overlay.classList.toggle('active');
    });
    
    // Close on overlay click
    overlay.addEventListener('click', () => {
        userDropdown.classList.remove('active');
        overlay.classList.remove('active');
        document.querySelector('.notification-panel')?.classList.remove('active');
        document.querySelector('.navbar-links')?.classList.remove('active');
    });
    
    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!userDropdown.contains(e.target)) {
            userDropdown.classList.remove('active');
        }
    });
}

/**
 * Initialize notifications
 */
function initNotifications() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationPanel = document.getElementById('notificationPanel');
    const closeNotifications = document.getElementById('closeNotifications');
    const overlay = document.getElementById('overlay');
    
    if (!notificationBtn || !notificationPanel) return;
    
    notificationBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notificationPanel.classList.toggle('active');
        overlay.classList.toggle('active');
        
        // Close user dropdown if open
        document.querySelector('.user-dropdown')?.classList.remove('active');
    });
    
    closeNotifications?.addEventListener('click', () => {
        notificationPanel.classList.remove('active');
        overlay.classList.remove('active');
    });
    
    // Mark notifications as read on click
    notificationPanel.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', () => {
            item.classList.remove('unread');
            updateNotificationBadge();
        });
    });
}

/**
 * Update notification badge count
 */
function updateNotificationBadge() {
    const unreadCount = document.querySelectorAll('.notification-item.unread').length;
    const badge = document.querySelector('.notification-badge');
    
    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
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
    
    mobileMenuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        navbarLinks.classList.toggle('active');
        overlay.classList.toggle('active');
        mobileMenuToggle.classList.toggle('active');
    });
}

/**
 * Highlight active navigation link
 */
function highlightActiveLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href.split('/').pop().replace('.html', ''))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Initialize scroll effect for navbar
 */
function initScrollEffect() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavbar);
} else {
    initNavbar();
}