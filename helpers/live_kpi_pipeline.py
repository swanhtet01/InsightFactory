"""Compute KPIs from newly synced data files."""
from typing import List
import os
import pandas as pd
from helpers.kpi_engine import KPIAgent


def compute_kpis_for_files(files: List[str]) -> dict:
    """Read Excel/CSV files and compute KPIs.

    Args:
        files: List of local file paths to process.

    Returns:
        dict of KPI metrics.
    """
    excel_files = [f for f in files if f.lower().endswith((".xlsx", ".xls", ".csv"))]
    if not excel_files:
        return {}
    frames = []
    for path in excel_files:
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            frames.append(df)
        except Exception as e:
            print(f"Failed to load {path}: {e}")
    if not frames:
        return {}
    combined = pd.concat(frames, ignore_index=True)
    agent = KPIAgent()
    kpis = agent.compute_kpis(combined)
    os.makedirs("reports", exist_ok=True)
    pd.DataFrame([kpis]).to_csv("reports/latest_kpis.csv", index=False)
    print("Saved KPIs to reports/latest_kpis.csv")
    return kpis
