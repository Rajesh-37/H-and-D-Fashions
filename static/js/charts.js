/**
 * Creates a line or bar chart for daily data
 * @param {string} canvasId - The ID of the canvas element
 * @param {object} data - The data object with dates as keys and values as values
 * @param {string} label - The label for the chart
 * @param {string} type - The type of chart ('line' or 'bar')
 * @param {string} backgroundColor - The background color for the chart
 * @param {string} borderColor - The border color for the chart
 */
function createDailyChart(canvasId, data, label, type = 'line', backgroundColor = 'rgba(54, 162, 235, 0.2)', borderColor = 'rgba(54, 162, 235, 1)') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Prepare data for chart
    const dates = Object.keys(data).sort();
    const values = dates.map(date => data[date]);
    
    const chart = new Chart(ctx, {
        type: type,
        data: {
            labels: dates.map(date => {
                const d = new Date(date);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [{
                label: label,
                data: values,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 2,
                tension: 0.1,
                fill: type === 'line' ? true : false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
    
    return chart;
}

/**
 * Creates a pie or doughnut chart for category data
 * @param {string} canvasId - The ID of the canvas element
 * @param {object} data - The data object with categories as keys and values as values
 * @param {string} title - The title for the chart
 * @param {string} type - The type of chart ('pie' or 'doughnut')
 */
function createPieChart(canvasId, data, title, type = 'doughnut') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Prepare data for chart
    const categories = Object.keys(data);
    const values = categories.map(cat => data[cat]);
    
    const chart = new Chart(ctx, {
        type: type,
        data: {
            labels: categories,
            datasets: [{
                data: values,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(199, 199, 199, 0.8)',
                    'rgba(83, 102, 255, 0.8)',
                    'rgba(40, 159, 64, 0.8)',
                    'rgba(210, 199, 199, 0.8)'
                ],
                borderColor: 'rgba(32, 33, 36, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((acc, data) => acc + data, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    return chart;
}

/**
 * Creates a multi-dataset chart for comparison (sales vs expenses)
 * @param {string} canvasId - The ID of the canvas element
 * @param {object} salesData - The sales data object with dates as keys and values as values
 * @param {object} expenseData - The expense data object with dates as keys and values as values
 */
function createComparisonChart(canvasId, salesData, expenseData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Get all unique dates from both datasets
    const allDates = [...new Set([...Object.keys(salesData), ...Object.keys(expenseData)])].sort();
    
    // Prepare datasets
    const salesValues = allDates.map(date => salesData[date] || 0);
    const expenseValues = allDates.map(date => expenseData[date] || 0);
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: allDates.map(date => {
                const d = new Date(date);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [
                {
                    label: 'Sales',
                    data: salesValues,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Expenses',
                    data: expenseValues,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
    
    return chart;
}
