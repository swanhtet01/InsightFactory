import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from helpers.drive_watcher import sync_drive

# Page config
st.set_page_config(
    page_title="Production KPIs",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sidebar with minimal controls
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("↻ Refresh Data", use_container_width=True):
        with st.spinner("Syncing & Processing..."):
            try:
                sync_drive()
                st.success("Data refreshed!")
                st.rerun()  # Rerun the app to show new data
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")
    
    # Add time filter in sidebar
    st.markdown("### Time Period")
    time_filter = st.radio(
        "Select Period",
        ["Today", "This Week", "This Month", "Custom"],
        index=0
    )
    
    if time_filter == "Custom":
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

# Process and validate data from all sources
data_dir = os.path.join(os.getcwd(), "data")
from helpers.data_validator import validate_and_merge_sources

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_validated_data():
    return validate_and_merge_sources(data_dir)

results = load_validated_data()

if not results:
    st.info("No production data available. Click 'Refresh Data' to sync.")
else:
    # Process validated results
    latest_data = max(results, key=lambda x: x['date'])
    
    # Show data source quality
    source_counts = {'excel': 0, 'image': 0}
    avg_confidence = 0
    for r in results:
        source_counts[r['source']] += 1
        avg_confidence += r.get('confidence', 0)
    avg_confidence = avg_confidence / len(results) if results else 0
    
    # Show small data quality indicator
    quality_color = "🟢" if avg_confidence > 80 else "🟡" if avg_confidence > 60 else "🔴"
    st.caption(f"{quality_color} Data Quality: {avg_confidence:.1f}% ({source_counts['excel']} Excel, {source_counts['image']} Image sources)")

# Page config
st.set_page_config(
    page_title="Production KPIs",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern KPI cards
st.markdown("""
<style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .kpi-title {
        color: #666666;
        font-size: 0.9em;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #1f1f1f;
        font-size: 1.8em;
        font-weight: bold;
    }
    .kpi-trend {
        color: #28a745;
        font-size: 0.9em;
        margin-top: 8px;
    }
    .kpi-trend.negative {
        color: #dc3545;
    }
    .stTabs {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with minimal controls
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("↻ Refresh Data", use_container_width=True):
        with st.spinner("Syncing & Processing..."):
            try:
                sync_drive()
                st.success("Data refreshed!")
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")
    
    # Add time filter in sidebar
    st.markdown("### Time Period")
    time_filter = st.radio(
        "Select Period",
        ["Today", "This Week", "This Month", "Custom"],
        index=0
    )
    
    if time_filter == "Custom":
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

# Process and validate data from all sources
data_dir = os.path.join(os.getcwd(), "data")
from helpers.data_validator import validate_and_merge_sources

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_validated_data():
    # First sync with drive
    sync_drive()
    # Then validate and merge all sources
    return validate_and_merge_sources(data_dir)

results = load_validated_data()

if not results:
    st.info("No production data available. Click 'Refresh Data' to sync.")
else:
    # Find most recent data
    latest_data = max(
        (r for r in results if r.get('kpis') and r['kpis'].get('latest_date')),
        key=lambda x: datetime.strptime(x['kpis']['latest_date'], '%Y-%m-%d'),
        default=None
    )

    if latest_data and latest_data.get('kpis'):
        kpis = latest_data['kpis']
        latest_date = datetime.strptime(kpis['latest_date'], '%Y-%m-%d')
        
        # Header with status overview
        st.title("🏭 Production Dashboard")
        header_cols = st.columns([2,1])
        with header_cols[0]:
            st.caption(f"Last Updated: {latest_date.strftime('%B %d, %Y %I:%M %p')}")
        with header_cols[1]:
            refresh_time = (datetime.now() - latest_date).total_seconds() / 3600
            status_color = "🟢" if refresh_time < 24 else "🟡" if refresh_time < 48 else "🔴"
            st.caption(f"{status_color} Data Freshness: {int(refresh_time)} hours")
        
        # Top KPI Cards Row
        kpi_cols = st.columns(4)
        
        def format_change(current, previous):
            if not previous:
                return None
            change = ((current - previous) / previous * 100)
            return f"{change:+.1f}%" if change else "0%"
            
        def kpi_card(title, value, change=None, prefix="", suffix=""):
            change_class = "negative" if change and "-" in change else ""
            card_html = f"""
            <div class="kpi-card">
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{prefix}{value:,.0f}{suffix}</div>
                {f'<div class="kpi-trend {change_class}">▲ {change}</div>' if change else ''}
            </div>
            """
            return card_html

        # Production KPIs
        with kpi_cols[0]:
            today_prod = kpis.get('today', {}).get('production', 0)
            yesterday_prod = kpis.get('yesterday', {}).get('production', 0)
            prod_change = format_change(today_prod, yesterday_prod)
            st.markdown(kpi_card(
                "Today's Production",
                today_prod,
                prod_change
            ), unsafe_allow_html=True)
            
        with kpi_cols[1]:
            today_target = kpis.get('today', {}).get('target', 0)
            target_achievement = (today_prod / today_target * 100) if today_target else 0
            st.markdown(kpi_card(
                "Target Achievement",
                target_achievement,
                suffix="%"
            ), unsafe_allow_html=True)
            
        with kpi_cols[2]:
            reject_rate = kpis.get('today', {}).get('reject_rate', 0)
            yesterday_rate = kpis.get('yesterday', {}).get('reject_rate', 0)
            reject_change = format_change(reject_rate, yesterday_rate)
            st.markdown(kpi_card(
                "Reject Rate",
                reject_rate,
                reject_change,
                suffix="%"
            ), unsafe_allow_html=True)
            
        with kpi_cols[3]:
            efficiency = kpis.get('today', {}).get('efficiency', 0)
            prev_efficiency = kpis.get('yesterday', {}).get('efficiency', 0)
            efficiency_change = format_change(efficiency, prev_efficiency)
            st.markdown(kpi_card(
                "Production Efficiency",
                efficiency,
                efficiency_change,
                suffix="%"
            ), unsafe_allow_html=True)
            
        # Tabs for detailed views
        tab1, tab2, tab3 = st.tabs(["📈 Trends", "🎯 Quality", "⚡ Performance"])
        
        with tab1:
            trend_cols = st.columns([2,1])
            with trend_cols[0]:
                # Production trend chart
                if latest_data.get('df_json'):
                    df = pd.read_json(latest_data['df_json'], orient='records')
                    df = df[latest_data['df_columns']]
                    date_col = next(col for col, cat in latest_data.get('column_categories', {}).items() if cat == 'date')
                    df[date_col] = pd.to_datetime(df[date_col])
                    
                    daily_prod = df.groupby(df[date_col].dt.date)['Production_Quantity'].sum().reset_index()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily_prod[date_col],
                        y=daily_prod['Production_Quantity'],
                        mode='lines+markers',
                        name='Actual',
                        line=dict(color='#2E86C1', width=2)
                    ))
                    fig.update_layout(
                        title='Daily Production Trend',
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0),
                        yaxis_title='Production Quantity',
                        xaxis_title='Date',
                        hovermode='x unified',
                        showlegend=True,
                        plot_bgcolor='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with trend_cols[1]:
                # Period comparison
                st.markdown("### Period Comparison")
                period_metrics = {
                    'This Week': kpis.get('this_week', {}).get('production', 0),
                    'Last Week': kpis.get('prev_week', {}).get('production', 0),
                    'This Month': kpis.get('this_month', {}).get('production', 0),
                    'Last Month': kpis.get('prev_month', {}).get('production', 0)
                }
                for period, value in period_metrics.items():
                    st.metric(period, f"{value:,}")
        
        with tab2:
            quality_cols = st.columns(2)
            with quality_cols[0]:
                # Quality trend
                if 'Rejected_Quantity' in df.columns:
                    daily_quality = df.groupby(df[date_col].dt.date).agg({
                        'Production_Quantity': 'sum',
                        'Rejected_Quantity': 'sum'
                    }).reset_index()
                    daily_quality['Reject_Rate'] = (daily_quality['Rejected_Quantity'] / daily_quality['Production_Quantity'] * 100).round(2)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=daily_quality[date_col],
                        y=daily_quality['Reject_Rate'],
                        name='Reject Rate',
                        marker_color='#E74C3C'
                    ))
                    fig.update_layout(
                        title='Quality Trend',
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0),
                        yaxis_title='Reject Rate (%)',
                        xaxis_title='Date'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with quality_cols[1]:
                # Quality analysis by type
                type_col = next((col for col, cat in latest_data.get('column_categories', {}).items() if cat == 'type'), None)
                if type_col and 'Rejected_Quantity' in df.columns:
                    type_quality = df.groupby(type_col).agg({
                        'Production_Quantity': 'sum',
                        'Rejected_Quantity': 'sum'
                    })
                    type_quality['Reject_Rate'] = (type_quality['Rejected_Quantity'] / type_quality['Production_Quantity'] * 100).round(2)
                    
                    fig = px.bar(
                        type_quality,
                        x=type_quality.index,
                        y='Reject_Rate',
                        title='Reject Rate by Type',
                        labels={'Reject_Rate': 'Reject Rate (%)'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            perf_cols = st.columns(2)
            with perf_cols[0]:
                # Efficiency trend
                if 'Target_Quantity' in df.columns:
                    daily_perf = df.groupby(df[date_col].dt.date).agg({
                        'Production_Quantity': 'sum',
                        'Target_Quantity': 'sum'
                    }).reset_index()
                    daily_perf['Achievement'] = (daily_perf['Production_Quantity'] / daily_perf['Target_Quantity'] * 100).round(2)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily_perf[date_col],
                        y=daily_perf['Achievement'],
                        mode='lines+markers',
                        name='Achievement',
                        line=dict(color='#27AE60', width=2)
                    ))
                    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Target")
                    fig.update_layout(
                        title='Target Achievement Trend',
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0),
                        yaxis_title='Achievement (%)',
                        xaxis_title='Date'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with perf_cols[1]:
                # Performance metrics table
                st.markdown("### Performance Summary")
                performance_df = pd.DataFrame({
                    'Metric': ['Overall Efficiency', 'Target Achievement', 'Quality Rate', 'Productivity'],
                    'Current': [
                        f"{kpis.get('today', {}).get('efficiency', 0):.1f}%",
                        f"{target_achievement:.1f}%",
                        f"{100 - reject_rate:.1f}%",
                        f"{kpis.get('today', {}).get('productivity', 0):.1f}"
                    ]
                })
                st.dataframe(performance_df.style.background_gradient(cmap='RdYlGn'), hide_index=True)
                
                
            if kpis.get('this_month'):
                month = kpis['this_month']
                prev_month = kpis.get('prev_month', {})
                
                st.metric(
                    "This Month",
                    f"{month.get('production', 0):,}",
                    format_change(
                        month.get('production', 0),
                        prev_month.get('production', 0)
                    )
                )
                
                st.metric(
                    "Monthly Reject Rate",
                    f"{month.get('reject_rate', 0):.2f}%",
                    format_change(
                        month.get('reject_rate', 0),
                        prev_month.get('reject_rate', 0)
                    ),
                    delta_color="inverse"
                )
        
        # Production Trends
        st.subheader("Production Trends")
        trend_cols = st.columns([2, 1])
        
        with trend_cols[0]:
            # Get the DataFrame
            if latest_data.get('df_json') and latest_data.get('df_columns'):
                # Load JSON data
                df_data = json.loads(latest_data['df_json'])
                df = pd.DataFrame(df_data)
                
                # Ensure columns are in the right order
                if latest_data.get('df_columns'):
                    df = df[latest_data['df_columns']]
                
                # Convert date columns
                for col in df.columns:
                    if col in ['Date', 'date', 'Period', 'period']:
                        df[col] = pd.to_datetime(df[col])
                
                # Get date column for grouping
                date_cols = df.select_dtypes(include=['datetime64']).columns
                if len(date_cols) > 0:
                    date_col = date_cols[0]
                    df['Date'] = df[date_col].dt.date
                    daily_prod = df.groupby('Date')['Production_Quantity'].sum().reset_index()
                    
                    fig = go.Figure()
                    
                    # Add production line
                    fig.add_trace(go.Scatter(
                        x=daily_prod['Date'],
                        y=daily_prod['Production_Quantity'],
                        name='Production',
                        line=dict(color='blue', width=2)
                    ))
                    
                    # Add target line if available
                    if 'Target' in df.columns:
                        daily_target = df.groupby('Date')['Target'].mean().reset_index()
                        fig.add_trace(go.Scatter(
                            x=daily_target['Date'],
                            y=daily_target['Target'],
                            name='Target',
                            line=dict(color='red', dash='dash')
                        ))
                    
                    fig.update_layout(
                        title='Daily Production Trend',
                        xaxis_title='Date',
                        yaxis_title='Production Quantity',
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with trend_cols[1]:
            # Efficiency gauge
            if kpis.get('today'):
                today = kpis['today']
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=today.get('efficiency', 0),
                    title={'text': "Today's Efficiency"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 60], 'color': "red"},
                            {'range': [60, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        }
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
        
        # Data tables section
        data_cols = st.columns([1, 1])
        
        with data_cols[0]:
            st.subheader("Recent Production Data")
            if latest_data.get('df_json') and latest_data.get('df_columns'):
                # Load and prepare data
                df_data = json.loads(latest_data['df_json'])
                df = pd.DataFrame(df_data)
                
                if latest_data.get('df_columns'):
                    df = df[latest_data['df_columns']]
                    
                # Convert date columns
                for col in df.columns:
                    if col in ['Date', 'date', 'Period', 'period']:
                        df[col] = pd.to_datetime(df[col])
                
                # Get the relevant columns
                display_cols = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if (
                        'date' in col_lower or
                        'production' in col_lower or
                        'reject' in col_lower
                    ):
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        df.tail(5)[display_cols].sort_values('Date', ascending=False),
                        use_container_width=True
                    )
        
        with data_cols[1]:
            st.subheader("Quality Metrics")
            if kpis.get('quality_metrics'):
                quality = kpis['quality_metrics']
                metrics_df = pd.DataFrame({
                    'Metric': ['Reject Rate', 'Rework Rate', 'First Pass Yield'],
                    'Value': [
                        f"{quality.get('reject_rate', 0):.2f}%",
                        f"{quality.get('rework_rate', 0):.2f}%",
                        f"{quality.get('first_pass_yield', 0):.2f}%"
                    ]
                })
                st.dataframe(metrics_df, use_container_width=True)
        
        # Insights from AI
        with st.expander("🤖 AI Insights", expanded=False):
            st.info("""
            **Recent Observations:**
            - Production trend shows {trend_direction}
            - Quality metrics are {quality_trend}
            - Efficiency levels are {efficiency_status}
            
            **Recommendations:**
            1. {recommendation1}
            2. {recommendation2}
            3. {recommendation3}
            """.format(
                trend_direction="improving" if kpis.get('trend_positive', False) else "declining",
                quality_trend="within target" if kpis.get('quality_on_target', False) else "needs attention",
                efficiency_status="optimal" if kpis.get('efficiency_optimal', False) else "below target",
                recommendation1="Monitor line speed vs. reject rate correlation",
                recommendation2="Review shift patterns for efficiency optimization",
                recommendation3="Schedule preventive maintenance based on performance trends"
            ))
    else:
        st.warning("No KPI data available. Please check data sources and refresh.")
