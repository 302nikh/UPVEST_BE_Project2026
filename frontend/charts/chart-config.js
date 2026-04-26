/* ============================================
   UPVEST - Chart Configuration
   Chart.js default settings and themes
   ============================================ */

const ChartConfig = {
    // Default chart options
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: true,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(102, 126, 234, 0.5)',
                borderWidth: 1,
                padding: 12,
                displayColors: false,
                callbacks: {
                    label: function(context) {
                        return '₹' + context.parsed.y.toFixed(2);
                    }
                }
            }
        },
        scales: {
            x: {
                display: true,
                grid: {
                    display: false
                },
                ticks: {
                    color: '#999',
                    font: {
                        size: 11
                    }
                }
            },
            y: {
                display: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    color: '#999',
                    font: {
                        size: 11
                    },
                    callback: function(value) {
                        return '₹' + value.toLocaleString('en-IN');
                    }
                }
            }
        }
    },
    
    // Line chart gradient (positive)
    createPositiveGradient: (ctx) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, 'rgba(40, 167, 69, 0.3)');
        gradient.addColorStop(1, 'rgba(40, 167, 69, 0.01)');
        return gradient;
    },
    
    // Line chart gradient (negative)
    createNegativeGradient: (ctx) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, 'rgba(220, 53, 69, 0.3)');
        gradient.addColorStop(1, 'rgba(220, 53, 69, 0.01)');
        return gradient;
    },
    
    // Get line dataset config
    getLineDataset: (label, data, isPositive = true) => {
        return {
            label: label,
            data: data,
            borderColor: isPositive ? '#28a745' : '#dc3545',
            backgroundColor: function(context) {
                const ctx = context.chart.ctx;
                return isPositive ? 
                    ChartConfig.createPositiveGradient(ctx) : 
                    ChartConfig.createNegativeGradient(ctx);
            },
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: isPositive ? '#28a745' : '#dc3545',
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2
        };
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartConfig;
}