import pandas as pd

# --- KPIAgent: Automatically analyze DataFrame and generate KPIs ---
class KPIAgent:
    def __init__(self, df):
        self.df = df
        self.kpis = {}
        self.recommendations = []
        self.analyze()

    def analyze(self):
        df = self.df
        # Detect columns
        cols = [c.lower() for c in df.columns]
        # Total production
        if 'quantity' in cols:
            self.kpis['total_production'] = df['quantity'].sum()
        elif 'total' in cols:
            self.kpis['total_production'] = df['total'].sum()
        # Quality rate
        if 'a_grade' in cols and 'b_grade' in cols:
            a = df['a_grade'].sum()
            b = df['b_grade'].sum()
            self.kpis['quality_rate'] = (a / (a + b) * 100) if (a + b) > 0 else 0
        elif 'quality_rate' in cols:
            self.kpis['quality_rate'] = df['quality_rate'].mean()
        # Target achievement
        if 'target' in cols and 'quantity' in cols:
            target = df['target'].sum()
            actual = df['quantity'].sum()
            self.kpis['target_achievement'] = (actual / target * 100) if target > 0 else 0
        # Top sizes
        if 'tyre_size' in cols and ('quantity' in cols or 'total' in cols):
            qty_col = 'quantity' if 'quantity' in cols else 'total'
            top_sizes = df.groupby('tyre_size')[qty_col].sum().sort_values(ascending=False).head(5)
            self.kpis['top_sizes'] = top_sizes.to_dict()
        # Recommendations
        if self.kpis.get('quality_rate', 100) < 95:
            self.recommendations.append('Quality rate below 95%. Investigate causes of defects.')
        if self.kpis.get('target_achievement', 100) < 90:
            self.recommendations.append('Production below target. Review bottlenecks or supply issues.')
        if not self.kpis:
            self.recommendations.append('Insufficient data for KPI calculation.')

    def summary(self):
        lines = [f"Total Production: {self.kpis.get('total_production', 'N/A')}"]
        if 'quality_rate' in self.kpis:
            lines.append(f"Quality Rate: {self.kpis['quality_rate']:.1f}%")
        if 'target_achievement' in self.kpis:
            lines.append(f"Target Achievement: {self.kpis['target_achievement']:.1f}%")
        if 'top_sizes' in self.kpis:
            lines.append("Top Sizes:")
            for size, qty in self.kpis['top_sizes'].items():
                lines.append(f"  {size}: {qty}")
        if self.recommendations:
            lines.append("\nRecommendations:")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
        return '\n'.join(lines)
"""
Advanced KPI Report Generator for Tyre Manufacturing
"""
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np

class TyreKPIReportGenerator:
    def __init__(self):
        self.date = datetime.now()
        self.colors = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'info': '#17becf'
        }
        
    def generate_production_dashboard(self, data):
        """
        Generate a comprehensive production dashboard with industry-standard KPIs
        """
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Production Efficiency",
                "Quality Metrics",
                "Weight Distribution",
                "Compound Mixing Performance",
                "Production by Size",
                "Energy Efficiency"
            ),
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}],
                [{"type": "violin"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "scatter"}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # 1. Production Efficiency Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=data['oee'],
                title={'text': "Overall Equipment Effectiveness"},
                delta={'reference': 85},
                gauge={
                    'axis': {'range': [None, 100]},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ),
            row=1, col=1
        )
        
        # 2. Quality Metrics
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=data['first_pass_yield'],
                title={'text': "First Pass Yield (%)"},
                delta={'reference': 95},
                domain={'row': 1, 'column': 2}
            ),
            row=1, col=2
        )
        
        # 3. Weight Distribution Violin Plot
        fig.add_trace(
            go.Violin(
                y=data['weight_distribution'],
                box_visible=True,
                line_color=self.colors['primary'],
                fillcolor=self.colors['primary'],
                opacity=0.6,
                name="Weight Distribution"
            ),
            row=2, col=1
        )
        
        # 4. Compound Mixing Performance
        categories = ['Mixing Time', 'Temperature', 'Viscosity', 'Dispersion']
        fig.add_trace(
            go.Bar(
                x=categories,
                y=data['compound_metrics'],
                marker_color=self.colors['info'],
                name="Compound Parameters"
            ),
            row=2, col=2
        )
        
        # 5. Production by Size (Pie)
        fig.add_trace(
            go.Pie(
                labels=list(data['size_production'].keys()),
                values=list(data['size_production'].values()),
                hole=.3,
                name="Size Distribution"
            ),
            row=3, col=1
        )
        
        # 6. Energy Efficiency Trend
        fig.add_trace(
            go.Scatter(
                x=data['timestamps'],
                y=data['energy_consumption'],
                mode='lines+markers',
                name="Energy Usage (kWh/kg)",
                line=dict(color=self.colors['success'])
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1000,
            showlegend=False,
            title_text="Tyre Production Performance Dashboard",
            title_x=0.5,
            title_font_size=24,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=100)
        )
        
        return fig

    def generate_expert_kpi_report(self, data):
        """
        Generate a comprehensive KPI report with industry-expert metrics
        """
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    TYRE PRODUCTION EXPERT METRICS                 ║
║                        {self.date.strftime('%B %d, %Y')}                        ║
╚══════════════════════════════════════════════════════════════════╝

PRIMARY PERFORMANCE INDICATORS
────────────────────────────
📊 Overall Equipment Effectiveness (OEE): {data['oee']}%
   ├─ Availability: {data['availability']}%
   ├─ Performance: {data['performance']}%
   └─ Quality: {data['quality']}%

QUALITY METRICS
─────────────
🎯 First Pass Yield: {data['first_pass_yield']}%
🔍 Defect Analysis:
   ├─ Critical Defects: {data['defects']['critical']}%
   ├─ Major Defects: {data['defects']['major']}%
   └─ Minor Defects: {data['defects']['minor']}%

PROCESS STABILITY
────────────────
⚖️ Weight Conformance:
   ├─ Mean: {data['weight_stats']['mean']:.2f} kg
   ├─ Std Dev: {data['weight_stats']['std']:.3f}
   └─ Cpk: {data['weight_stats']['cpk']:.2f}

🌡️ Compound Parameters:
   ├─ Mixing Energy: {data['compound']['mixing_energy']:.1f} kWh/batch
   ├─ Temperature Control: {data['compound']['temp_deviation']:.1f}°C
   └─ Dispersion Index: {data['compound']['dispersion_index']:.2f}

PRODUCTION EFFICIENCY
───────────────────
⚡ Energy Efficiency: {data['energy_efficiency']:.2f} kWh/kg
🏃 Cycle Time Performance:
   ├─ Average Cycle: {data['cycle_times']['average']:.1f} min
   ├─ Optimal Cycle: {data['cycle_times']['optimal']:.1f} min
   └─ Efficiency: {data['cycle_times']['efficiency']:.1f}%

SIZE-WISE METRICS
────────────────
📏 Top Performing Sizes:"""

        # Add size-wise performance
        for size, metrics in data['size_metrics'].items():
            report += f"""
   {size}:
   ├─ Output: {metrics['output']:,} units
   ├─ FPY: {metrics['fpy']:.1f}%
   └─ Cpk: {metrics['cpk']:.2f}"""

        report += """

IMPROVEMENT OPPORTUNITIES
───────────────────────
🎯 Identified Areas:"""
        
        # Add improvement opportunities
        for area in data['improvements']:
            report += f"\n   • {area}"

        return report

    def generate_daily_summary(self, data):
        """
        Generate a concise daily summary with expert insights
        """
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║                      DAILY PRODUCTION SUMMARY                     ║
║                        {self.date.strftime('%B %d, %Y')}                        ║
╚══════════════════════════════════════════════════════════════════╝

KEY ACHIEVEMENTS
──────────────
📈 Production Volume: {data['production']['total']:,} units
   vs Target: {data['production']['vs_target']:+.1f}%
   vs Last Day: {data['production']['vs_last_day']:+.1f}%

🎯 Critical KPIs:
   ├─ OEE: {data['oee']}% ({data['oee_trend']:+.1f}%)
   ├─ First Pass Yield: {data['fpy']}% ({data['fpy_trend']:+.1f}%)
   └─ Energy Efficiency: {data['energy_efficiency']:.2f} kWh/kg ({data['energy_trend']:+.2f})

QUALITY INSIGHTS
──────────────
✓ Pass Rate: {data['quality']['pass_rate']:.1f}%
! Defect Rate: {data['quality']['defect_rate']:.1f}%
↻ Rework Rate: {data['quality']['rework_rate']:.1f}%

PROCESS STABILITY
────────────────
⚖️ Weight Control:
   ├─ Within Spec: {data['weight_control']['within_spec']:.1f}%
   ├─ Above Spec: {data['weight_control']['above_spec']:.1f}%
   └─ Below Spec: {data['weight_control']['below_spec']:.1f}%

🌡️ Process Parameters:
   ├─ Temperature Compliance: {data['process']['temp_compliance']:.1f}%
   ├─ Pressure Stability: {data['process']['pressure_stability']:.1f}%
   └─ Cycle Time Adherence: {data['process']['cycle_adherence']:.1f}%
"""
        return summary

    def save_dashboard_html(self, fig, filename='dashboard.html'):
        """Save the dashboard as an interactive HTML file"""
        fig.write_html(filename)
        
    def save_report_pdf(self, report, filename='report.pdf'):
        """Save the report as a PDF file"""
        # TODO: Implement PDF generation with proper formatting
        pass
