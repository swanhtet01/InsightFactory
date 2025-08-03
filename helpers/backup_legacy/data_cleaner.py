import pandas as pd
import numpy as np
import re
from typing import List, Dict, Optional

def clean_tyre_data(files: List[str]) -> Dict:
    """
    Load, clean, and unify all Excel files for robust KPI analytics.
    Returns a dict with cleaned DataFrame, summary, and issues.
    """
    all_dfs = []
    issues = []
    import openpyxl
    header_keywords = ['no', 'date', 'tyre', 'size', 'qty', 'quantity', 'oee', 'fpy', 'cpk', 'a_grade', 'b_grade', 'target', 'scrap', 'energy', 'total wt']
    for file in files:
        try:
            xl = pd.ExcelFile(file)
            file_dfs = []
            for sheet in xl.sheet_names:
                try:
                    raw_df = xl.parse(sheet, header=None)
                    # Find the most likely header row (at least 2 header keywords)
                    header_row = None
                    for i, row in raw_df.iterrows():
                        row_strs = [str(x).lower() for x in row]
                        score = sum(any(h in cell for h in header_keywords) for cell in row_strs)
                        if score >= 2:
                            header_row = i
                            break
                    if header_row is None:
                        continue
                    # Use this row as header
                    df = xl.parse(sheet, header=header_row)
                    df = df.dropna(how='all')
                    # Standardize column names
                    df.columns = [re.sub(r'[^\w\d ]+', '', str(col)).strip().lower().replace(' ', '_') for col in df.columns]
                    # Try to find and rename key columns
                    col_map = {}
                    for col in df.columns:
                        if 'date' in col and 'update' not in col:
                            col_map[col] = 'date'
                        elif 'tyre' in col or 'size' in col:
                            col_map[col] = 'tyre_size'
                        elif 'qty' in col or 'quantity' in col:
                            col_map[col] = 'quantity'
                        elif 'oee' in col:
                            col_map[col] = 'oee'
                        elif 'fpy' in col:
                            col_map[col] = 'fpy'
                        elif 'cpk' in col:
                            col_map[col] = 'cpk'
                        elif 'a_grade' in col or (col.startswith('a') and 'grade' in col):
                            col_map[col] = 'a_grade'
                        elif 'b_grade' in col or (col.startswith('b') and 'grade' in col):
                            col_map[col] = 'b_grade'
                        elif 'target' in col:
                            col_map[col] = 'target'
                        elif 'scrap' in col:
                            col_map[col] = 'scrap'
                        elif 'energy' in col:
                            col_map[col] = 'energy_efficiency'
                    df.rename(columns=col_map, inplace=True)
                    # Remove duplicates
                    if 'date' in df.columns and 'tyre_size' in df.columns:
                        df = df.drop_duplicates(subset=['date', 'tyre_size'])
                    # Parse dates
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    # Convert numerics
                    for col in ['quantity','oee','fpy','cpk','a_grade','b_grade','target','scrap','energy_efficiency']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    # Only keep blocks with at least 2 required columns and at least 1 row
                    required_cols = set(['date','tyre_size','quantity'])
                    if required_cols.intersection(set(df.columns)) and len(df) > 0:
                        file_dfs.append(df)
                except Exception as sheet_e:
                    issues.append(f"{file} [{sheet}]: {sheet_e}")
            if file_dfs:
                all_dfs.extend(file_dfs)
            else:
                issues.append(f"{file}: No usable data found in any sheet.")
        except Exception as e:
            issues.append(f"{file}: {e}")
    if not all_dfs:
        return {'data': pd.DataFrame(), 'issues': issues}
    # Unify all data
    df = pd.concat(all_dfs, ignore_index=True)
    # Remove rows with no date or tyre_size
    df = df[df['date'].notna() & df['tyre_size'].notna()]
    # Sort
    df = df.sort_values('date')
    return {'data': df, 'issues': issues}
