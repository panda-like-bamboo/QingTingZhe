// static/js/charts.js
document.addEventListener('DOMContentLoaded', function() {
    const ageChartCtx = document.getElementById('ageChart');
    const genderChartCtx = document.getElementById('genderChart');

    if (!ageChartCtx || !genderChartCtx) {
        console.error("Chart canvas elements not found!");
        return;
    }

    // Mock data - In a real app, fetch this from an API endpoint
    const mockData = {
        ageData: {
            labels: ['<18', '18-25', '26-35', '36-45', '46-55', '56+'],
            values: [5, 25, 40, 22, 15, 8]
        },
        genderData: {
            labels: ['男', '女', '其他'],
            values: [63, 35, 2]
        }
    };

    // Age Distribution Line Chart
    new Chart(ageChartCtx, {
        type: 'line',
        data: {
            labels: mockData.ageData.labels,
            datasets: [{
                label: '年龄分布',
                data: mockData.ageData.values,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: '数量' }
                },
                x: {
                    title: { display: true, text: '年龄段' }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '用户年龄分布'
                }
            }
        }
    });

    // Gender Distribution Pie Chart
    new Chart(genderChartCtx, {
        type: 'pie',
        data: {
            labels: mockData.genderData.labels,
            datasets: [{
                label: '性别分布',
                data: mockData.genderData.values,
                backgroundColor: [
                    'rgb(54, 162, 235)',
                    'rgb(255, 99, 132)',
                    'rgb(201, 203, 207)'
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '用户性别分布'
                }
            }
        }
    });
});