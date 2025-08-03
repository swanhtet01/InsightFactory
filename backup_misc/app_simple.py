"""Smart Tyre Production Dashboard""" 

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Smart Dashboard", page_icon="🏭", layout="wide")

def load_data():
    data_dir = Path("data")
    if not data_dir.exists():
        st.error("Data directory not found")
        return pd.DataFrame()
        
    excel_files = []
    for f in data_dir.glob("*.xlsx"):
        excel_files.append((f, f.stat().st_mtime))
        
    if not excel_files:
        return pd.DataFrame()
        
    excel_files.sort(key=lambda x: x[1], reverse=True)
    latest_files = excel_files[:2]
    
    combined_data = pd.DataFrame()
    for filepath, _ in latest_files:
        try:
            xl = pd.ExcelFile(filepath)
            best_data = None
            max_rows = 0
            
            for sheet in xl.sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet)
                    if df.empty:
                        continue
                        
                    date_col = None
                    for col in df.columns:
                        try:
                            test_dates = pd.to_datetime(df[col], errors="coerce")
                            if test_dates.notna().sum() > len(df) * 0.5:
                                date_col = col
                                df[col] = test_dates
                                break
                        except:
                            continue
                            
                    if not date_col:
                        continue
                        
                    qty_col = None
                    for col in df.columns:
                        if col == date_col:
                            continue
                        try:
                            values = pd.to_numeric(df[col], errors="coerce")
                            if values.notna().sum() > len(df) * 0.5 and values.min() >= 0:
                                qty_col = col
                                df[col] = values
                                break
                        except:
                            continue
                            
                    if date_col and qty_col:
                        temp_df = df[[date_col, qty_col]].copy()
                        temp_df.columns = ["date", "quantity"]
                        temp_df = temp_df.dropna()
                        
                        if len(temp_df) > max_rows:
                            max_rows = len(temp_df)
                            best_data = temp_df
                except:
                    continue
                    
            if best_data is not None:
                if combined_data.empty:
                    combined_data = best_data
                else:
                    combined_data = pd.concat([combined_data, best_data])
        except:
            continue
            
    if combined_data.empty:
        return pd.DataFrame()
        
    combined_data = combined_data.sort_values("date")
    combined_data = combined_data.drop_duplicates()
    return combined_data

def main():
    st.title("🏭 Tyre Production Dashboard")
    
    df = load_data()
    
    if df.empty:
        st.error("No data available")
        return
        
    # Date filter
    timeframe = st.selectbox("Select Timeframe", 
                          ["Last 7 Days", "Last 30 Days", "This Month", "All Time"])
    
    end_date = pd.Timestamp.now()
    if timeframe == "Last 7 Days":
        start_date = end_date - pd.Timedelta(days=7)
    elif timeframe == "Last 30 Days":
        start_date = end_date - pd.Timedelta(days=30)
    elif timeframe == "This Month":
        start_date = end_date.replace(day=1)
    else:
        start_date = df["date"].min()
        
    filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_prod = filtered_df["quantity"].sum()
        st.metric("Total Production", f"{total_prod:,.0f}")
        
    with col2:
        daily_avg = filtered_df.groupby(filtered_df["date"].dt.date)["quantity"].sum().mean()
        st.metric("Daily Average", f"{daily_avg:,.0f}")
        
    with col3:
        latest_day = filtered_df["date"].max()
        latest_prod = filtered_df[filtered_df["date"].dt.date == latest_day.date()]["quantity"].sum()
        st.metric("Latest Day", f"{latest_prod:,.0f}")
    
    # Trend chart
    daily_data = filtered_df.groupby(filtered_df["date"].dt.date)["quantity"].sum().reset_index()
    
    fig = px.line(daily_data, x="date", y="quantity",
                 labels={"date": "Date", "quantity": "Production"})
    st.plotly_chart(fig, use_container_width=True)
    
    # Table view
    with st.expander("View Data"):
        st.dataframe(daily_data.sort_values("date", ascending=False))

if __name__ == "__main__":
    main()

