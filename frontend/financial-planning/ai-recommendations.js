/* ============================================
   UPVEST - AI Recommendations
   AI-powered investment recommendations
   ============================================ */

// This file provides additional AI recommendation utilities
// Main AI generation is handled by API.generateInvestmentPlan()

const AIRecommendations = {
    /**
     * Format AI response for display
     */
    formatResponse: (response) => {
        // Add formatting, emojis, and structure to AI response
        return response;
    },
    
    /**
     * Get quick tips based on user profile
     */
    getQuickTips: (userData) => {
        const tips = [];
        
        if (userData.age < 30) {
            tips.push('💡 Start early to benefit from compound interest');
        }
        
        if (userData.savings > 20000) {
            tips.push('💰 Consider diversifying across multiple funds');
        }
        
        if (userData.risk === 'low') {
            tips.push('🛡️ Focus on capital preservation with debt funds');
        }
        
        return tips;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIRecommendations;
}