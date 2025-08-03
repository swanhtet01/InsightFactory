def load_data():

"""
Robust data loader for tyre KPI dashboard.
Scans all .xlsx files in data/, loads all sheets, auto-detects headers, and extracts all relevant tabular data.
"""
import os
import pandas as pd
import re
from typing import List

def find_header_row(df: pd.DataFrame, keywords: List[str]) -> int:
    for i, row in df.iterrows():
        row_strs = [str(x).lower() for x in row]
        score = sum(any(k in cell for k in keywords) for cell in row_strs)
        if score >= 2:
            return i
    return None

def load_data(data_dir: str = "data") -> pd.DataFrame:
    all_dfs = []
    header_keywords = ['date', 'tyre', 'size', 'qty', 'quantity', 'oee', 'fpy', 'cpk', 'a_grade', 'b_grade', 'target', 'scrap']
    for fname in os.listdir(data_dir):
        if fname.endswith('.xlsx'):
            fpath = os.path.join(data_dir, fname)
            try:
                xl = pd.ExcelFile(fpath)
                for sheet in xl.sheet_names:
                    raw = xl.parse(sheet, header=None)
                    header_row = find_header_row(raw, header_keywords)
                    if header_row is not None:
                        df = xl.parse(sheet, header=header_row)
                        df = df.dropna(how='all')
                        df.columns = [re.sub(r'[^\w\d ]+', '', str(col)).strip().lower().replace(' ', '_') for col in df.columns]
                        # Only keep if at least 2 of the main columns are present
                        main_cols = set(['date','tyre_size','quantity'])
                        if main_cols.intersection(set(df.columns)) and len(df) > 0:
                            all_dfs.append(df)
            except Exception as e:
                print(f"[data_loader] Error loading {fname}: {e}")
    if not all_dfs:
        return pd.DataFrame()
    df = pd.concat(all_dfs, ignore_index=True)
    # Clean up
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    for col in ['quantity','oee','fpy','cpk','a_grade','b_grade','target','scrap']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df = df[df['date'].notna() & df['tyre_size'].notna()]
    df = df.sort_values('date')
    return df
