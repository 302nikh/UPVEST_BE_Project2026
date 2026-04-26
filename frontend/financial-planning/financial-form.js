/* ============================================
   UPVEST - Financial Form Handler
   Form validation and submission
   ============================================ */

const FinancialForm = {
    /**
     * Validate financial profile form
     */
    validate: (formData) => {
        const errors = [];
        
        // Validate salary
        if (!formData.salary || formData.salary <= 0) {
            errors.push('Monthly salary must be greater than 0');
        }
        
        // Validate expenses
        if (!formData.expenses || formData.expenses < 0) {
            errors.push('Monthly expenses cannot be negative');
        }
        
        // Validate savings
        if (!formData.savings || formData.savings <= 0) {
            errors.push('Monthly savings must be greater than 0');
        }
        
        // Check if expenses exceed salary
        if (formData.expenses >= formData.salary) {
            errors.push('Monthly expenses cannot exceed or equal salary');
        }
        
        // Validate age
        if (!formData.age || formData.age < 18 || formData.age > 100) {
            errors.push('Age must be between 18 and 100');
        }
        
        // Validate risk
        if (!formData.risk || !['low', 'medium', 'high'].includes(formData.risk)) {
            errors.push('Please select a valid risk appetite');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    },
    
    /**
     * Get form data
     */
    getData: () => {
        return {
            salary: parseFloat(document.getElementById('monthlySalary')?.value) || 0,
            expenses: parseFloat(document.getElementById('monthlyExpenses')?.value) || 0,
            savings: parseFloat(document.getElementById('monthlySavings')?.value) || 0,
            age: parseInt(document.getElementById('age')?.value) || 0,
            risk: document.querySelector('input[name="risk"]:checked')?.value || 'medium'
        };
    },
    
    /**
     * Set form data
     */
    setData: (data) => {
        if (data.salary) document.getElementById('monthlySalary').value = data.salary;
        if (data.expenses) document.getElementById('monthlyExpenses').value = data.expenses;
        if (data.savings) document.getElementById('monthlySavings').value = data.savings;
        if (data.age) document.getElementById('age').value = data.age;
        if (data.risk) {
            const riskRadio = document.querySelector(`input[name="risk"][value="${data.risk}"]`);
            if (riskRadio) riskRadio.checked = true;
        }
    },
    
    /**
     * Calculate recommended savings
     */
    calculateRecommendedSavings: (salary, age, risk) => {
        let savingsRate = 0.20; // Default 20%
        
        // Adjust based on age
        if (age < 30) {
            savingsRate = 0.25; // Save more when young
        } else if (age > 50) {
            savingsRate = 0.30; // Save more as retirement approaches
        }
        
        // Adjust based on risk
        if (risk === 'high') {
            savingsRate += 0.05;
        } else if (risk === 'low') {
            savingsRate -= 0.05;
        }
        
        return Math.round(salary * savingsRate);
    },
    
    /**
     * Get investment recommendations based on profile
     */
    getRecommendations: (userData) => {
        const { age, risk, savings } = userData;
        const recommendations = [];
        
        // Age-based recommendations
        if (age < 30) {
            recommendations.push('Focus on equity investments for long-term growth');
            recommendations.push('Start SIP in diversified mutual funds');
        } else if (age >= 30 && age < 50) {
            recommendations.push('Balance between equity and debt instruments');
            recommendations.push('Increase PPF/ELSS contributions for tax benefits');
        } else {
            recommendations.push('Shift towards safer debt instruments');
            recommendations.push('Focus on capital preservation');
        }
        
        // Risk-based recommendations
        if (risk === 'low') {
            recommendations.push('Consider fixed deposits and government bonds');
            recommendations.push('Maintain higher emergency fund (12 months)');
        } else if (risk === 'high') {
            recommendations.push('Explore direct equity investments');
            recommendations.push('Consider mid and small-cap funds');
        }
        
        // Savings-based recommendations
        if (savings < 10000) {
            recommendations.push('Start with small SIP amounts (₹500-₹1000)');
            recommendations.push('Build emergency fund first');
        } else if (savings > 50000) {
            recommendations.push('Diversify across multiple asset classes');
            recommendations.push('Consider portfolio management services');
        }
        
        return recommendations;
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinancialForm;
}