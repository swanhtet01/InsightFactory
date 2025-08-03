"""
GPT-4o-powered header normalization and cleaning utilities.
"""

import openai
import os
import pandas as pd
import ast
import re

# Load API key directly from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                openai.api_key = line.split('=', 1)[1].strip()
                break

def clean_headers(df):
    """
    Normalize and clean dataframe headers using GPT-4o.
    Args:
        df (pd.DataFrame): Raw dataframe from Excel.
    Returns:
        tuple: (Cleaned dataframe with normalized headers, error message or None)
    """
    # First, try to handle merged cells by looking at non-empty values in first few rows
    header_rows = df.head(3)
    actual_headers = []
    for col in df.columns:
        if 'Unnamed' in str(col):
            # Look for first non-null value in this column from header rows
            for _, row in header_rows.iterrows():
                if pd.notna(row[col]):
                    actual_headers.append(str(row[col]).strip())
                    break
            else:
                # If no value found, use previous non-Unnamed header
                if actual_headers:
                    actual_headers.append(actual_headers[-1])
                else:
                    actual_headers.append('Column_' + str(len(actual_headers)))
        else:
            actual_headers.append(str(col).strip())
    
    prompt = f"""
    The following are the column headers from a tyre production Excel sheet. Clean, normalize, and map them to standard English headers. Use these categories:
    - Date/Time related: Date, Shift (A/B/R), Week, Month, Year
    - Production: Production_Quantity, Good_Quantity, Rejected_Quantity, Rework_Quantity, Scrap_Quantity
    - Quality: QC_Passed, QC_Failed, Quality_Rate
    - Specifications: Size, Spec_Weight, Actual_Weight, Weight_Variance
    - Performance: Downtime_Duration, Efficiency, Yield
    
    Original Headers: {actual_headers}
    Return ONLY a valid Python dictionary mapping original headers to cleaned headers. Do not include any explanation, code block, or extra text.
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a data cleaning assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0.2
    )
    mapping_str = response.choices[0].message.content.strip()
    # Extract first {...} block if extra text is present
    match = re.search(r"\{[\s\S]*\}", mapping_str)
    if match:
        mapping_str = match.group(0)
    mapping = None
    error_msg = None
    # Try to safely parse the mapping
    try:
        mapping = ast.literal_eval(mapping_str)
        if not isinstance(mapping, dict):
            raise ValueError("LLM did not return a dictionary.")
    except Exception as e:
        error_msg = f"[HeaderCleaner] Invalid mapping from LLM, using original headers. Error: {e}\nLLM output: {mapping_str}"
        print(error_msg)
        # Log error to a file
        with open("header_cleaning_errors.log", "a") as logf:
            logf.write(f"{error_msg}\n")
        mapping = {col: col for col in df.columns}
    df = df.rename(columns=mapping)
    return df, error_msg
