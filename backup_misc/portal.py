"""
Streamlit-based web portal for tyre production dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from helpers.data_processor import process_weekly_data, process_daily_data, process_monthly_data
import yaml

# Load configuration
def load_config():
    try:
        with open('config/portal_config.yml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {
            'allowed_users': {
                'admin': 'your_secure_password'  # Change this
            }
        }

# Security setup
def check_password():
    if not st.session_state.get("authenticated", False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            config = load_config()
            if username in config['allowed_users'] and password == config['allowed_users'][username]:
                st.session_state.authenticated = True
                st.session_state.language = 'en'  # Default language
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
        return False
    return True

# Page config
st.set_page_config(
    page_title="Tyre Production Dashboard | တာယာထုတ်လုပ်မှု ဒက်ရှ်ဘုတ်",
    layout="wide"
)

# Translations
TRANSLATIONS = {
    'en': {
        'title': 'Tyre Production Dashboard',
        'production_metrics': 'Production Metrics',
        'daily_production': 'Daily Production',
        'weekly_summary': 'Weekly Summary',
        'quality_metrics': 'Quality Metrics',
        'efficiency': 'Efficiency',
        'weight_control': 'Weight Control',
        'total_production': 'Total Production',
        'target_achievement': 'Target Achievement',
        'quality_rate': 'Quality Rate',
        'a_grade': 'A Grade',
        'b_grade': 'B Grade',
        'rework': 'Rework',
        'production_by_size': 'Production by Size',
        'shift_performance': 'Shift Performance',
        'logout': 'Logout'
    },
    'my': {
        'title': 'တာယာထုတ်လုပ်မှု ဒက်ရှ်ဘုတ်',
        'production_metrics': 'ထုတ်လုပ်မှု အချက်အလက်များ',
        'daily_production': 'နေ့စဉ်ထုတ်လုပ်မှု',
        'weekly_summary': 'အပတ်စဉ်အနှစ်ချုပ်',
        'quality_metrics': 'အရည်အသွေး အချက်အလက်များ',
        'efficiency': 'ထိရောက်မှု',
        'weight_control': 'အလေးချိန်ထိန်းချုပ်မှု',
        'total_production': 'စုစုပေါင်း ထုတ်လုပ်မှု',
        'target_achievement': 'ပစ်မှတ် ပြည့်မှီမှု',
        'quality_rate': 'အရည်အသွေး နှုန်း',
        'a_grade': 'A အဆင့်',
        'b_grade': 'B အဆင့်',
        'rework': 'ပြန်လည်ပြုပြင်ရန်',
        'production_by_size': 'အရွယ်အစားအလိုက် ထုတ်လုပ်မှု',
        'shift_performance': 'အလုပ်ချိန် စွမ်းဆောင်ရည်',
        'logout': 'ထွက်ရန်'
    }
}

# Custom styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 16px;
        color: #666;
    }
    .stButton>button {
        width: 100%;
    }
    .report-download {
        margin-top: 20px;
        padding: 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
if not check_password():
    st.stop()

# Language selector in sidebar
lang = st.sidebar.selectbox(
    'Language | ဘာသာစကား',
    ['en', 'my'],
    format_func=lambda x: 'English' if x == 'en' else 'မြန်မာ'
)

# Logout button in sidebar
if st.sidebar.button(TRANSLATIONS[lang]['logout']):
    st.session_state.authenticated = False
    st.experimental_rerun()

# Get translations
t = TRANSLATIONS[lang]

# Title
st.title(t['title'])

try:
    # Load data
    weekly_file = 'data/Weekly Tyre 20225.xlsx'
    daily_file = 'data/Daily Pro; A,B,R Report .xlsx'
    monthly_file = 'data/1.  Tyre PD ; A.B.R ( 2025) year ).xlsx'
    
    weekly_data = process_weekly_data(weekly_file)
    daily_data = process_daily_data(daily_file)
    monthly_data = process_monthly_data(monthly_file)
    
    # Dashboard layout
    col1, col2, col3 = st.columns(3)
    
    # Daily Production Metrics
    with col1:
        st.subheader(t['daily_production'])
        st.metric(
            label=t['total_production'],
            value=f"{daily_data['total_production']:,}",
            delta=f"{daily_data['production_change']:+.1f}%"
        )
        
    # Quality Metrics
    with col2:
        st.subheader(t['quality_metrics'])
        st.metric(
            label=t['quality_rate'],
            value=f"{daily_data['quality_rate']:.1f}%",
            delta=f"{daily_data['quality_change']:+.1f}%"
        )
        
    # Efficiency Metrics
    with col3:
        st.subheader(t['efficiency'])
        st.metric(
            label=t['target_achievement'],
            value=f"{daily_data['target_achievement']:.1f}%",
            delta=f"{daily_data['target_change']:+.1f}%"
        )

    # Production by Size Chart
    st.subheader(t['production_by_size'])
    fig_size = go.Figure(data=[
        go.Bar(name=t['a_grade'], x=daily_data['sizes'], y=daily_data['a_grade']),
        go.Bar(name=t['b_grade'], x=daily_data['sizes'], y=daily_data['b_grade']),
        go.Bar(name=t['rework'], x=daily_data['sizes'], y=daily_data['rework'])
    ])
    fig_size.update_layout(barmode='group')
    st.plotly_chart(fig_size, use_container_width=True)
    
    # Shift Performance
    st.subheader(t['shift_performance'])
    fig_shift = go.Figure(data=[
        go.Bar(
            name='Shift 1',
            x=daily_data['sizes'],
            y=daily_data['shift_1'],
            text=daily_data['shift_1'],
            textposition='auto',
        ),
        go.Bar(
            name='Shift 2',
            x=daily_data['sizes'],
            y=daily_data['shift_2'],
            text=daily_data['shift_2'],
            textposition='auto',
        )
    ])
    fig_shift.update_layout(barmode='group')
    st.plotly_chart(fig_shift, use_container_width=True)
    
    # Download section
    st.sidebar.markdown("### Download Reports")
    if st.sidebar.button("Download Daily Report"):
        # Generate report logic here
        st.sidebar.success("Report downloaded!")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
