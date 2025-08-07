"""
Robust data loader for tyre KPI dashboard.
Scans all .xlsx files in data/, loads all sheets, auto-detects headers,
and extracts all relevant tabular data.
"""
import os
import pandas as pd
import re
from typing import List

def find_header_row(df: pd.DataFrame, keywords: List[str]) -> int:
    """
    Finds the header row in a DataFrame by searching for keywords.
    """
    for i, row in df.iterrows():
        row_strs = [str(x).lower() for x in row]
        score = sum(any(k in cell for k in keywords) for cell in row_strs)
        # Require at least 2 keywords to match to be considered a header
        if score >= 2:
            return i
    return None

def load_data(data_dir: str = "data") -> pd.DataFrame:
    """
    Loads all .xlsx files from a directory, finds headers, cleans data, and returns a single DataFrame.
    """
    all_dfs = []
    header_keywords = [
        'date', 'tyre', 'size', 'qty', 'quantity', 'oee', 'fpy', 'cpk',
        'a_grade', 'b_grade', 'target', 'scrap', 'production', 'output',
        'efficiency', 'performance', 'quality', 'availability'
    ]
    
    if not os.path.exists(data_dir):
        print(f"⚠️ Data directory '{data_dir}' not found. Please ensure it exists.")
        return pd.DataFrame()

    for fname in os.listdir(data_dir):
        if fname.endswith('.xlsx') and not fname.startswith('~'):
            fpath = os.path.join(data_dir, fname)
            try:
                xl = pd.ExcelFile(fpath)
                for sheet in xl.sheet_names:
                    try:
                        raw_df = xl.parse(sheet, header=None)
                        header_row_index = find_header_row(raw_df, header_keywords)

                        if header_row_index is not None:
                            # Re-parse the sheet with the correct header row
                            df = xl.parse(sheet, header=header_row_index)
                            df = df.dropna(how='all').reset_index(drop=True)

                            # Clean column names
                            df.columns = [re.sub(r'[^\w\d ]+', '', str(col)).strip().lower().replace(' ', '_') for col in df.columns]

                            # Basic validation: ensure essential columns are present
                            main_cols = {'date', 'tyre_size', 'quantity'}
                            if main_cols.intersection(set(df.columns)):
                                print(f"✅ Loaded {len(df)} rows from '{fname}' (Sheet: {sheet})")
                                df['source_file'] = fname  # Add source file for traceability
                                all_dfs.append(df)
                            else:
                                print(f"⚠️ Skipping sheet '{sheet}' in '{fname}' due to missing essential columns.")

                    except Exception as sheet_error:
                        print(f"⚠️ Error processing sheet '{sheet}' in '{fname}': {sheet_error}")
            except Exception as file_error:
                print(f"❌ Error loading file '{fname}': {file_error}")

    if not all_dfs:
        print("🤷 No valid data found in any Excel files in the 'data' directory.")
        return pd.DataFrame()

    # Concatenate and clean the final DataFrame
    final_df = pd.concat(all_dfs, ignore_index=True)

    # Coerce data types and handle errors
    if 'date' in final_df.columns:
        final_df['date'] = pd.to_datetime(final_df['date'], errors='coerce')

    numeric_cols = ['quantity', 'oee', 'fpy', 'cpk', 'a_grade', 'b_grade', 'target', 'scrap']
    for col in numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)

    # Drop rows where essential data is missing after cleaning
    final_df = final_df.dropna(subset=['date', 'tyre_size'])
    final_df = final_df.sort_values('date').reset_index(drop=True)

    print(f"✅ Successfully loaded and processed {len(final_df)} total rows.")
    return final_df
