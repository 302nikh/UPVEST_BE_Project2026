/* ============================================
   UPVEST - DEMAT Account Service
   Upstox OAuth integration
   ============================================ */

const DematService = {
    /**
     * Initialize Upstox OAuth flow
     */
    connectAccount: () => {
        const loginUrl = API.getUpstoxLoginUrl();
        
        // Save current page for redirect after auth
        Utils.saveToStorage('demat_redirect_page', window.location.href);
        
        // Redirect to Upstox login
        window.location.href = loginUrl;
    },
    
    /**
     * Handle OAuth callback
     */
    handleCallback: async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const authCode = urlParams.get('code');
        
        if (!authCode) {
            Utils.showToast('Authorization failed. Please try again.', 'error');
            return false;
        }
        
        try {
            Utils.showLoader('Connecting your DEMAT account...');
            
            // Exchange code for access token
            const tokenData = await API.getUpstoxAccessToken(authCode);
            
            if (!tokenData || !tokenData.access_token) {
                throw new Error('Failed to get access token');
            }
            
            // Get user profile
            const profile = await API.getUpstoxProfile(tokenData.access_token);
            
            // Save connection data
            const connectionData = {
                connected: true,
                broker: 'Upstox',
                clientId: profile.client_id || profile.user_id,
                userName: profile.user_name || profile.email,
                accessToken: tokenData.access_token,
                connectedAt: new Date().toISOString(),
                portfolioValue: 0,
                totalReturns: 0,
                activeInvestments: 0
            };
            
            Utils.saveToStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION, connectionData);
            
            Utils.hideLoader();
            Utils.showToast(CONFIG.SUCCESS.DEMAT_CONNECTED, 'success');
            
            // Redirect back to original page
            const redirectPage = Utils.getFromStorage('demat_redirect_page') || '../home/dashboard.html';
            Utils.removeFromStorage('demat_redirect_page');
            
            setTimeout(() => {
                window.location.href = redirectPage;
            }, 1000);
            
            return true;
            
        } catch (error) {
            Utils.hideLoader();
            console.error('DEMAT connection error:', error);
            Utils.showToast('Failed to connect DEMAT account. Please try again.', 'error');
            return false;
        }
    },
    
    /**
     * Disconnect DEMAT account
     */
    disconnectAccount: () => {
        if (confirm('Are you sure you want to disconnect your DEMAT account?')) {
            Utils.removeFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION);
            Utils.showToast('DEMAT account disconnected successfully', 'success');
            
            // Reload page
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    },
    
    /**
     * Get connection status
     */
    getConnectionStatus: () => {
        const connection = Utils.getFromStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION);
        return connection && connection.connected ? connection : null;
    },
    
    /**
     * Check if account is connected
     */
    isConnected: () => {
        const connection = DematService.getConnectionStatus();
        return connection !== null;
    },
    
    /**
     * Simulate DEMAT connection for demo (without real OAuth)
     */
    connectDemoAccount: () => {
        const demoConnection = {
            connected: true,
            broker: 'Upstox (Demo)',
            clientId: 'DEMO' + Math.random().toString(36).substring(7).toUpperCase(),
            userName: 'Demo User',
            accessToken: 'demo_token_' + Date.now(),
            connectedAt: new Date().toISOString(),
            portfolioValue: 150000,
            totalReturns: 15000,
            activeInvestments: 5
        };
        
        Utils.saveToStorage(CONFIG.SETTINGS.STORAGE_KEYS.DEMAT_CONNECTION, demoConnection);
        Utils.showToast('Demo DEMAT account connected!', 'success');
        
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    },
    
    /**
     * Get portfolio data
     */
    getPortfolioData: async () => {
        const connection = DematService.getConnectionStatus();
        
        if (!connection) {
            throw new Error('DEMAT account not connected');
        }
        
        // In production, fetch real data from Upstox API
        // For now, return demo data
        return {
            totalValue: connection.portfolioValue || 150000,
            totalInvested: 135000,
            totalReturns: connection.totalReturns || 15000,
            returnPercentage: 11.11,
            holdings: [
                { symbol: 'RELIANCE', quantity: 10, avgPrice: 2450, currentPrice: 2580, pnl: 1300 },
                { symbol: 'TCS', quantity: 5, avgPrice: 3200, currentPrice: 3450, pnl: 1250 },
                { symbol: 'INFY', quantity: 15, avgPrice: 1400, currentPrice: 1520, pnl: 1800 },
                { symbol: 'HDFCBANK', quantity: 8, avgPrice: 1600, currentPrice: 1650, pnl: 400 },
                { symbol: 'ICICIBANK', quantity: 12, avgPrice: 900, currentPrice: 950, pnl: 600 }
            ]
        };
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DematService;
}