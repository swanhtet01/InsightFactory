import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Import our refactored helpers
from helpers.data_loader import load_data
from helpers.kpi_engine import KPIAgent

# Set wide layout and page title
st.set_page_config(layout="wide", page_title="InsightFactory | Tyre Production Dashboard")

def filter_data_by_date(df, period_option, date_range_selection):
    """Filter dataframe based on the selected time period option."""
    if df.empty or 'date' not in df.columns:
        return pd.DataFrame()

    df['date'] = pd.to_datetime(df['date'])

    if period_option == "All Time":
        return df
    elif period_option == "Custom Range":
        if len(date_range_selection) == 2:
            start_date, end_date = pd.to_datetime(date_range_selection)
            return df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        else:
            return df # Default to all data if range is not set

    # Dynamic period filtering
    now = datetime.now()
    if period_option == "Last 7 Days":
        start_date = now - timedelta(days=7)
    elif period_option == "Last 30 Days":
        start_date = now - timedelta(days=30)
    elif period_option == "Last 90 Days":
        start_date = now - timedelta(days=90)
    elif period_option == "This Month":
        start_date = now.replace(day=1)
    elif period_option == "This Year":
        start_date = now.replace(month=1, day=1)
    else:
        return df # Should not happen

    return df[df['date'] >= start_date]


def main():
    """
    The main function that runs the Streamlit application.
    """
    # --- Page Title and Logo ---
    col1, col2 = st.columns([1, 6])
    with col1:
        if "static/logo.png":
            st.image("static/logo.png", width=100)
    with col2:
        st.title("Tyre Production Dashboard")
        st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # --- Data Loading ---
    with st.spinner("Loading and processing production data..."):
        # Use st.cache_data to avoid reloading data on every interaction
        @st.cache_data(ttl=300) # Cache for 5 minutes
        def cached_load_data():
            return load_data()

        df = cached_load_data()

    if df.empty:
        st.error("No production data found. Please check the 'data/' directory for valid Excel files.")
        st.stop()

    # --- Sidebar for Filters ---
    st.sidebar.header("Filters")

    # Time period filter
    period_option = st.sidebar.selectbox(
        "Select Time Period",
        ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "This Month", "This Year", "Custom Range"]
    )

    date_range = []
    if period_option == "Custom Range":
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        date_range = st.sidebar.date_input(
            "Select date range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

    # Filter data based on selection
    filtered_df = filter_data_by_date(df, period_option, date_range)

    if filtered_df.empty:
        st.warning(f"No data available for the selected period: '{period_option}'.")
        st.stop()

    # Tyre size filter
    all_tyre_sizes = sorted(filtered_df['tyre_size'].unique())
    selected_sizes = st.sidebar.multiselect(
        "Select Tyre Size(s)",
        options=all_tyre_sizes,
        default=all_tyre_sizes
    )

    if not selected_sizes:
        st.warning("Please select at least one tyre size.")
        st.stop()

    final_df = filtered_df[filtered_df['tyre_size'].isin(selected_sizes)]

    if final_df.empty:
        st.warning("No data matches the selected tyre size filters.")
        st.stop()

    # --- KPI Display ---
    st.header("Key Performance Indicators")

    # Initialize KPI agent with the filtered data
    kpi_agent = KPIAgent(final_df)
    kpi_agent.compute_kpis()
    kpis = kpi_agent.kpis

    # Display KPIs in metric cards
    col1, col2, col3 = st.columns(3)
    col1.metric("OEE (%)", f"{kpis.get('oee', 0):.1f}")
    col1.metric("FPY (%)", f"{kpis.get('fpy', 0):.1f}")
    col2.metric("Total Production", f"{kpis.get('production', 0):,.0f} units")
    col2.metric("Target Achievement", f"{kpis.get('target_achievement', 0):.1f}%")
    col3.metric("A-Grade Quality Rate", f"{kpis.get('quality_rate', 0):.1f}%")
    col3.metric("Scrap Rate", f"{kpis.get('scrap_rate', 0):.2f}%")

    # --- Visualizations ---
    st.header("Analytics & Trends")

    # Production Trend (Line Chart)
    daily_prod = final_df.groupby(final_df['date'].dt.date)['quantity'].sum().reset_index()
    fig_trend = px.line(daily_prod, x='date', y='quantity', title="Daily Production Trend", markers=True)
    fig_trend.update_layout(template="plotly_white")
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Production by Tyre Size (Bar Chart)
    size_prod = final_df.groupby('tyre_size')['quantity'].sum().sort_values(ascending=False).reset_index()
    fig_bar = px.bar(size_prod, x='tyre_size', y='quantity', title="Production Volume by Tyre Size")
    fig_bar.update_layout(template="plotly_white")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Raw Data Table ---
    with st.expander("Show Raw Data"):
        st.dataframe(final_df, use_container_width=True)

    # --- Footer ---
    st.markdown("---")
    st.caption("© 2025 InsightFactory | A modern, intuitive KPI dashboard.")


if __name__ == "__main__":
    main()
