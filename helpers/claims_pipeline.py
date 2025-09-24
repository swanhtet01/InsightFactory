"""Compute simple metrics from claim spreadsheets."""
from typing import List
import os
import pandas as pd

from config import REPORTS_DIR


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
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORTS_DIR / 'latest_claim_metrics.csv'
    pd.DataFrame([metrics]).to_csv(output, index=False)
    print(f'Saved claim metrics to {output}')
    return metrics
