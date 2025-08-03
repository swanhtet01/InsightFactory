
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from helpers.data_loader import load_data
from helpers.github_uploader import start_github_sync
from helpers.kpi_engine import KPIAgent
from config import TRANSLATIONS

# Start GitHub sync in background
github_manager = start_github_sync()

st.set_page_config(page_title="Tyre Factory KPI Dashboard", layout="wide")
st.title("📊 Tyre Factory KPI Dashboard")

# Set default language
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'
lang = st.session_state.lang

# --- Load and check data ---
with st.spinner("Loading production data from Excel files in data/ ..."):
    df = load_data()
if df.empty:
    st.error("No valid data found in the data/ folder. Please check your Excel files.")
    st.stop()
df = df.copy()
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.drop_duplicates(subset=['date', 'tyre_size']).sort_values('date')

def get_latest_production_data():
    """Get the latest production data from the data folder"""
    return load_data()

# --- KPI Metrics ---
def safe_mean(series):
    return float(series.mean()) if not series.empty else 0

oee = safe_mean(df['oee']) if 'oee' in df.columns else 0
fpy = safe_mean(df['fpy']) if 'fpy' in df.columns else 0
prod = df['quantity'].sum() if 'quantity' in df.columns else 0
target = df['target'].sum() if 'target' in df.columns else 0
target_ach = (prod / target * 100) if target > 0 else 0
quality_rate = (df['a_grade'].sum() / (df['a_grade'].sum() + df['b_grade'].sum()) * 100) if 'a_grade' in df.columns and 'b_grade' in df.columns and (df['a_grade'].sum() + df['b_grade'].sum()) > 0 else 0
scrap_rate = (df['scrap'].sum() / prod * 100) if 'scrap' in df.columns and prod > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("OEE (%)", f"{oee:.1f}")
col1.metric("FPY (%)", f"{fpy:.1f}")
col2.metric("Production", f"{prod:,.0f} units")
col2.metric("Target Achievement (%)", f"{target_ach:.1f}")
col3.metric("Quality Rate (%)", f"{quality_rate:.1f}")
col3.metric("Scrap Rate (%)", f"{scrap_rate:.2f}")

# --- KPI Trends ---
st.markdown("---")
st.subheader("KPI Trends (7-day Rolling Average)")
kpi_trends = {
    'OEE (%)': 'oee',
    'FPY (%)': 'fpy',
    'Production Quantity': 'quantity',
    'Scrap Rate (%)': 'scrap',
}
for label, col in kpi_trends.items():
    if col in df.columns and 'date' in df.columns:
        trend = df.sort_values('date').set_index('date')[col].rolling(window=7, min_periods=3).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend.index, y=trend.values, mode='lines+markers', name=f'{label} (7d avg)'))
        fig.update_layout(title=f"{label} (7d Rolling Avg)", xaxis_title="Date", yaxis_title=label, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# --- Data Table ---
st.markdown("---")
st.subheader("Raw Data Preview")
st.dataframe(df.head(20), use_container_width=True)

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Tyre Factory KPI Dashboard | Built for Fortune 500 standards. For help, contact your analytics team.")
t = TRANSLATIONS[lang]

# Title
st.title(t['title'])

def format_number(num):
    """Format large numbers for display"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return f"{num:.0f}"

def calculate_trend(current, previous):
    """Calculate trend percentage"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def filter_data_by_date(df, period):
    """Filter dataframe based on selected time period"""
    if df.empty:
        return df
        
    now = datetime.now()
    if period == "Last 24 Hours":
        return df[df['timestamp'] >= now - timedelta(days=1)]
    elif period == "Last 7 Days":
        return df[df['timestamp'] >= now - timedelta(days=7)]
    elif period == "Last 30 Days":
        return df[df['timestamp'] >= now - timedelta(days=30)]
    elif period == "This Month":
        return df[df['timestamp'].dt.month == now.month]
    elif period == "This Year":
        return df[df['timestamp'].dt.year == now.year]
    return df

def main():
    st.title("🏭 Tyre Production Dashboard")
    
    # Date filters
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "This Month", "This Year"]
        )
    
    # Load and process data
    with st.spinner("Loading latest production data..."):
        df = get_latest_production_data()
    if df.empty:
        st.error("No production data found. Please check data sources.")
        return
    filtered_df = filter_data_by_date(df, date_range)
    if filtered_df.empty:
        st.warning(f"No data available for the selected period: {date_range}")
        return

    # --- Use KPIAgent to analyze and display KPIs ---
    agent = KPIAgent(filtered_df)
    st.subheader("Production KPIs & Insights")
    st.markdown(f"""
        <div class="kpi-card">
            <pre style='font-size: 1.1em'>{agent.summary()}</pre>
        </div>
    """, unsafe_allow_html=True)

    # Optionally, show more detailed charts if enough data is present
    if 'date' in filtered_df.columns and 'quantity' in filtered_df.columns:
        st.subheader("Production Trend")
        daily_prod = filtered_df.groupby(filtered_df['date'])['quantity'].sum().reset_index()
        fig = px.line(daily_prod, x='date', y='quantity', title="Daily Production")
        st.plotly_chart(fig, use_container_width=True)

    if 'tyre_size' in filtered_df.columns and ('quantity' in filtered_df.columns or 'total' in filtered_df.columns):
        qty_col = 'quantity' if 'quantity' in filtered_df.columns else 'total'
        st.subheader("Production by Tyre Size")
        size_prod = filtered_df.groupby('tyre_size')[qty_col].sum().reset_index()
        size_prod = size_prod.sort_values(qty_col, ascending=True)
        fig = px.bar(size_prod, x=qty_col, y='tyre_size', orientation='h',
                    title="Production by Tyre Size",
                    labels={'tyre_size': 'Tyre Size', qty_col: 'Production Quantity'})
        st.plotly_chart(fig, use_container_width=True)

    # Data sources info
    st.sidebar.title("Data Sources")
    st.sidebar.markdown(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if 'source' in filtered_df.columns:
        sources = filtered_df['source'].unique()
        for source in sources:
            source_df = filtered_df[filtered_df['source'] == source]
            st.sidebar.markdown(f"**{source.title()} Data:**")
            st.sidebar.markdown(f"- Records: {len(source_df):,}")
            if 'date' in source_df.columns:
                st.sidebar.markdown(f"- Date Range: {source_df['date'].min()} to {source_df['date'].max()}")
        # Production by tyre size
        size_prod = filtered_df.groupby('tyre_size')['quantity'].sum().reset_index()
        size_prod = size_prod.sort_values('quantity', ascending=True)
        fig = px.bar(size_prod, x='quantity', y='tyre_size', orientation='h',
                    title="Production by Tyre Size",
                    labels={'tyre_size': 'Tyre Size', 'quantity': 'Production Quantity'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Data sources info
    st.sidebar.title("Data Sources")
    st.sidebar.markdown(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    sources = filtered_df['source'].unique()
    for source in sources:
        source_df = filtered_df[filtered_df['source'] == source]
        st.sidebar.markdown(f"**{source.title()} Data:**")
        st.sidebar.markdown(f"- Records: {len(source_df):,}")
        st.sidebar.markdown(f"- Date Range: {source_df['date'].min()} to {source_df['date'].max()}")

if __name__ == "__main__":
    main()
