"""
Handles the generation of KPI report templates with proper formatting
"""
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

class KPIReportGenerator:
    def __init__(self):
        self.date = datetime.now()
        
    def generate_daily_summary(self, production_data):
        """
        Generate a daily KPI summary with production metrics
        Format:
        ==========================================
        DAILY PRODUCTION SUMMARY - July 22, 2025
        ==========================================
        
        TODAY'S HIGHLIGHTS:
        ------------------
        ▲ Total Production: 1,234 units
        ▼ Target Achievement: 95% (Target: 1,300)
        ● Quality Rate: 98.5%
        
        SHIFT BREAKDOWN:
        ---------------
        Shift 1: 450 units (A: 200, B: 150, R: 100)
        Shift 2: 784 units (A: 350, B: 284, R: 150)
        
        TOP PRODUCING SIZES:
        ------------------
        1. 5.00-12: 500 units
        2. 6.00-13: 400 units
        3. 7.00-14: 334 units
        
        QUALITY METRICS:
        --------------
        Pass Rate: 98.5%
        Rework Rate: 1.2%
        Rejection Rate: 0.3%
        
        WEIGHT CONFORMANCE:
        -----------------
        Within Spec: 99.1%
        Above Spec: 0.6%
        Below Spec: 0.3%
        """
        template = f"""
==========================================
DAILY PRODUCTION SUMMARY - {self.date.strftime('%B %d, %Y')}
==========================================

TODAY'S HIGHLIGHTS:
------------------
▲ Total Production: {production_data.get('total_production', 0):,} units
▼ Target Achievement: {production_data.get('target_achievement', 0)}% (Target: {production_data.get('target', 0):,})
● Quality Rate: {production_data.get('quality_rate', 0)}%

SHIFT BREAKDOWN:
---------------"""
        
        for shift, data in production_data.get('shifts', {}).items():
            template += f"\n{shift}: {data.get('total', 0)} units (A: {data.get('A', 0)}, B: {data.get('B', 0)}, R: {data.get('R', 0)})"
            
        template += "\n\nTOP PRODUCING SIZES:"
        template += "\n------------------"
        for size, count in production_data.get('top_sizes', {}).items():
            template += f"\n{size}: {count} units"
            
        return template
        
    def generate_weekly_summary(self, weekly_data):
        """
        Generate a weekly summary with trends
        Format:
        ============================================
        WEEKLY PRODUCTION REPORT - Week 29 (July 22)
        ============================================
        
        WEEKLY PERFORMANCE:
        -----------------
        Total Production: 8,567 units
        Target Achievement: 98% (Target: 8,750)
        Average Daily Production: 1,224 units
        
        DAILY BREAKDOWN:
        --------------
        Monday    : 1,234 units ██████████ 98%
        Tuesday   : 1,345 units ███████████ 102%
        Wednesday : 1,456 units ████████████ 105%
        Thursday  : 1,234 units ██████████ 98%
        Friday    : 1,567 units █████████████ 110%
        Saturday  : 1,234 units ██████████ 98%
        Sunday    : 497 units ████ 45%
        
        SIZE-WISE PRODUCTION:
        -------------------
        5.00-12: 3,000 units (35%)
        6.00-13: 2,500 units (29%)
        7.00-14: 3,067 units (36%)
        """
        template = f"""
============================================
WEEKLY PRODUCTION REPORT - Week {self.date.isocalendar()[1]} ({self.date.strftime('%B %d')})
============================================

WEEKLY PERFORMANCE:
-----------------
Total Production: {weekly_data.get('total_production', 0):,} units
Target Achievement: {weekly_data.get('target_achievement', 0)}% (Target: {weekly_data.get('target', 0):,})
Average Daily Production: {weekly_data.get('avg_daily', 0):,} units

DAILY BREAKDOWN:
--------------"""

        for day, data in weekly_data.get('daily_production', {}).items():
            progress = '█' * int(data.get('achievement', 0) / 10)
            template += f"\n{day:<10}: {data.get('total', 0):,} units {progress} {data.get('achievement', 0)}%"
            
        return template
        
    def generate_monthly_summary(self, monthly_data):
        """
        Generate a monthly summary with comparisons
        Format:
        ==============================================
        MONTHLY PRODUCTION REPORT - July 2025
        ==============================================
        
        MONTHLY OVERVIEW:
        ---------------
        Total Production: 35,678 units
        Target Achievement: 99% (Target: 36,000)
        YoY Growth: +5.2%
        
        WEEK-WISE TRENDS:
        ---------------
        Week 26: 8,567 units ██████████ 98%
        Week 27: 8,890 units ███████████ 102%
        Week 28: 9,234 units ████████████ 105%
        Week 29: 8,987 units ██████████ 98%
        
        TOP ACHIEVEMENTS:
        ---------------
        - Highest Daily Production: 1,567 units (July 15)
        - Best Quality Rate: 99.2% (Week 28)
        - Most Efficient Day: July 12 (105% target)
        
        AREAS FOR IMPROVEMENT:
        --------------------
        - Size 6.00-13 below target by 2%
        - Shift 2 efficiency dropped 1.5%
        - Weight variance increased 0.3%
        """
        template = f"""
==============================================
MONTHLY PRODUCTION REPORT - {self.date.strftime('%B %Y')}
==============================================

MONTHLY OVERVIEW:
---------------
Total Production: {monthly_data.get('total_production', 0):,} units
Target Achievement: {monthly_data.get('target_achievement', 0)}% (Target: {monthly_data.get('target', 0):,})
YoY Growth: {monthly_data.get('yoy_growth', 0)}%

WEEK-WISE TRENDS:
---------------"""

        for week, data in monthly_data.get('weekly_production', {}).items():
            progress = '█' * int(data.get('achievement', 0) / 10)
            template += f"\nWeek {week}: {data.get('total', 0):,} units {progress} {data.get('achievement', 0)}%"
            
        return template

    def generate_charts(self, data):
        """Generate visualizations for the reports"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Daily Production", "Quality Metrics", 
                          "Size-wise Distribution", "Target Achievement")
        )
        
        # Add traces for each subplot
        # Daily Production trend
        fig.add_trace(
            go.Scatter(x=data['dates'], y=data['production'],
                      name="Production"),
            row=1, col=1
        )
        
        # Quality metrics
        fig.add_trace(
            go.Bar(x=['Pass', 'Rework', 'Reject'], 
                  y=[data['quality']['pass'], data['quality']['rework'], 
                     data['quality']['reject']],
                  name="Quality"),
            row=1, col=2
        )
        
        # Size distribution
        fig.add_trace(
            go.Pie(labels=list(data['sizes'].keys()), 
                  values=list(data['sizes'].values()),
                  name="Sizes"),
            row=2, col=1
        )
        
        # Target achievement
        fig.add_trace(
            go.Bar(x=['Target', 'Actual'], 
                  y=[data['target'], data['actual']],
                  name="Achievement"),
            row=2, col=2
        )
        
        return fig

    def save_as_html(self, report_type='daily'):
        """Save the report as an HTML file for web viewing"""
        pass
        
    def save_as_pdf(self, report_type='daily'):
        """Save the report as a PDF file for email attachments"""
        pass
