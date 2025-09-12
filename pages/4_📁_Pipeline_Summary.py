import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pipeline Summary", layout="wide")
st.title("📁 Pipeline Summary")

summary_path = Path("reports/latest_summary.json")
if not summary_path.exists():
    st.warning("No summary report found. Run the pipeline first.")
    st.stop()

with summary_path.open() as f:
    summary = json.load(f)

st.subheader("KPI Metrics")
st.dataframe(pd.DataFrame([summary.get("kpis", {})]))

st.subheader("Claim Metrics")
st.dataframe(pd.DataFrame([summary.get("claims", {})]))

st.subheader("Document Metrics")
st.dataframe(pd.DataFrame(summary.get("documents", [])))

html_path = Path("reports/latest_summary.html")
if html_path.exists():
    st.subheader("HTML Report")
    html = html_path.read_text()
    st.components.v1.html(html, height=400, scrolling=True)
