<?php
/**
 * Plugin Name: Tyre Production Dashboard
 * Description: Secure portal for tyre production metrics
 * Version: 1.0
 * Author: Your Name
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

// Add menu item
function tyre_dashboard_menu() {
    add_menu_page(
        'Tyre Production Dashboard',
        'Tyre Dashboard',
        'manage_options',
        'tyre-dashboard',
        'render_tyre_dashboard',
        'dashicons-chart-area'
    );
}
add_action('admin_menu', 'tyre_dashboard_menu');

// Add login check
function check_dashboard_access() {
    if (!is_user_logged_in()) {
        wp_redirect(wp_login_url());
        exit;
    }
}
add_action('template_redirect', 'check_dashboard_access');

// Render dashboard page
function render_tyre_dashboard() {
    // Enqueue required scripts
    wp_enqueue_script('plotly', 'https://cdn.plot.ly/plotly-latest.min.js');
    wp_enqueue_style('tyre-dashboard-style', plugin_dir_url(__FILE__) . 'css/dashboard.css');
    ?>
    <div class="wrap">
        <h1>တာယာထုတ်လုပ်မှု ဒက်ရှ်ဘုတ် | Tyre Production Dashboard</h1>
        
        <!-- Language Toggle -->
        <div class="language-toggle">
            <button onclick="setLanguage('en')" class="lang-btn">English</button>
            <button onclick="setLanguage('my')" class="lang-btn">မြန်မာ</button>
        </div>
        
        <!-- Dashboard Content -->
        <div id="dashboard-content">
            <div class="loading">Loading dashboard data...</div>
        </div>
    </div>

    <script>
    const translations = {
        en: {
            title: 'Tyre Production Dashboard',
            production: 'Production',
            quality: 'Quality',
            efficiency: 'Efficiency',
            // Add more translations
        },
        my: {
            title: 'တာယာထုတ်လုပ်မှု ဒက်ရှ်ဘုတ်',
            production: 'ထုတ်လုပ်မှု',
            quality: 'အရည်အသွေး',
            efficiency: 'ထိရောက်မှု',
            // Add more translations
        }
    };

    let currentLang = 'en';

    function setLanguage(lang) {
        currentLang = lang;
        updateDashboard();
    }

    async function fetchDashboardData() {
        try {
            const response = await fetch('https://your-api-domain/api/dashboard-data', {
                headers: {
                    'X-API-Key': 'YOUR_SECRET_API_KEY'
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            return null;
        }
    }

    function createMetricCard(title, value, trend) {
        return `
            <div class="metric-card">
                <h3>${translations[currentLang][title]}</h3>
                <div class="metric-value">${value}</div>
                <div class="metric-trend ${trend >= 0 ? 'positive' : 'negative'}">
                    ${trend >= 0 ? '↑' : '↓'} ${Math.abs(trend)}%
                </div>
            </div>
        `;
    }

    function createCharts(data) {
        // Production by Size
        const sizeTrace = {
            type: 'bar',
            x: data.daily.sizes,
            y: data.daily.total,
            name: translations[currentLang].production
        };
        Plotly.newPlot('production-chart', [sizeTrace]);

        // Quality Metrics
        const qualityData = {
            values: [
                data.daily.a_grade_total,
                data.daily.b_grade_total,
                data.daily.rework_total
            ],
            labels: ['A Grade', 'B Grade', 'Rework'],
            type: 'pie'
        };
        Plotly.newPlot('quality-chart', [qualityData]);

        // More charts...
    }

    async function updateDashboard() {
        const data = await fetchDashboardData();
        if (!data) return;

        const content = document.getElementById('dashboard-content');
        
        // Create metric cards
        content.innerHTML = `
            <div class="metrics-grid">
                ${createMetricCard('production', data.daily.total_production, data.daily.production_change)}
                ${createMetricCard('quality', data.daily.quality_rate, data.daily.quality_change)}
                ${createMetricCard('efficiency', data.daily.target_achievement, data.daily.target_change)}
            </div>
            
            <div class="charts-grid">
                <div id="production-chart"></div>
                <div id="quality-chart"></div>
                <div id="efficiency-chart"></div>
            </div>
        `;

        // Create charts
        createCharts(data);
    }

    // Initial load
    updateDashboard();
    </script>
    <?php
}

// Add CSS
function tyre_dashboard_css() {
    ?>
    <style>
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f77b4;
        }
        
        .metric-trend {
            font-size: 14px;
            margin-top: 8px;
        }
        
        .metric-trend.positive { color: #2ca02c; }
        .metric-trend.negative { color: #d62728; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .language-toggle {
            margin-bottom: 20px;
        }
        
        .lang-btn {
            padding: 8px 16px;
            margin-right: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .lang-btn:hover {
            background: #f0f0f0;
        }
    </style>
    <?php
}
add_action('admin_head', 'tyre_dashboard_css');
