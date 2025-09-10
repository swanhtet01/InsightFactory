"""Compute simple metrics from claim spreadsheets."""
from typing import List
import os
import pandas as pd


def compute_claim_metrics(files: List[str]) -> dict:
    claim_files = [
        f for f in files if f.lower().endswith(('.xlsx', '.xls', '.csv')) and 'claim' in os.path.basename(f).lower()
    ]
    if not claim_files:
        return {}
    frames = []
    for path in claim_files:
        try:
            if path.lower().endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            frames.append(df)
        except Exception as e:
            print(f"Failed to load {path}: {e}")
    if not frames:
        return {}
    df = pd.concat(frames, ignore_index=True)
    metrics = {'total_claims': len(df)}
    if 'amount' in df.columns:
        metrics['total_claim_amount'] = df['amount'].sum()
    os.makedirs('reports', exist_ok=True)
    pd.DataFrame([metrics]).to_csv('reports/latest_claim_metrics.csv', index=False)
    print('Saved claim metrics to reports/latest_claim_metrics.csv')
    return metrics
