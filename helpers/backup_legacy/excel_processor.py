"""
Excel file processor for production data
"""
import pandas as pd
import numpy as np
from datetime import datetime
import re

def standardize_headers(df):
    """Standardize column headers"""
    std_headers = {
        r'(?i)date|day|month|year': 'date',
        r'(?i)time|hour': 'time',
        r'(?i)product|item|type|model': 'product',
        r'(?i)quantity|qty|output|production|count|volume|amount': 'quantity',
        r'(?i)target|plan|goal|forecast': 'target',
        r'(?i)reject|defect|fail|scrap': 'defects',
        r'(?i)rework|repair|fix': 'rework',
        r'(?i)quality|grade|rating|class': 'quality',
        r'(?i)machine|equipment|line|station': 'machine',
        r'(?i)shift|period': 'shift',
        r'(?i)weight|wt': 'weight',
        r'(?i)size|dimension': 'size'
    }
    
    new_columns = []
    for col in df.columns:
        matched = False
        for pattern, new_name in std_headers.items():
            if re.search(pattern, str(col)):
                new_columns.append(new_name)
                matched = True
                break
        if not matched:
            new_columns.append(col)
    
    df.columns = new_columns
    return df

def process_excel_file(filepath, sheet_name=None):
    """Process Excel file and extract production data"""
    try:
        # If no sheet specified, find the best one
        if sheet_name is None:
            xl = pd.ExcelFile(filepath)
            sheets = xl.sheet_names
            
            if not sheets:
                raise ValueError("No sheets found in the Excel file")
                
            best_sheet = sheets[0]  # Default to first sheet
            
            # First try direct month names or numbers
            month_patterns = [
                r'(?i)january|jan|01|1月',
                r'(?i)february|feb|02|2月',
                r'(?i)march|mar|03|3月',
                r'(?i)april|apr|04|4月',
                r'(?i)may|05|5月',
                r'(?i)june|jun|06|6月',
                r'(?i)july|jul|07|7月',
                r'(?i)august|aug|08|8月',
                r'(?i)september|sep|09|9月',
                r'(?i)october|oct|10|10月',
                r'(?i)november|nov|11|11月',
                r'(?i)december|dec|12|12月'
            ]
            
            # Then try other relevant patterns
            data_patterns = [
                r'(?i)production|output|prod',
                r'(?i)daily|weekly|monthly|yearly',
                r'(?i)data|report|summary',
                r'(?i)main|primary|raw',
                r'(?i)\d{2}[-_]\d{2}|\d{4}'  # Date patterns
            ]
            
            best_sheet = None
            max_score = -1

            # First try month patterns
            for sheet in sheets:
                score = 0
                for pattern in month_patterns:
                    if re.search(pattern, sheet):
                        score += 2  # Give higher weight to month matches
                for pattern in data_patterns:
                    if re.search(pattern, sheet):
                        score += 1
                if score > max_score:
                    max_score = score
                    best_sheet = sheet

            # If no good match found, try preview and select the most data-like sheet
            if best_sheet is None:
                for sheet in sheets:
                    try:
                        preview = pd.read_excel(filepath, sheet_name=sheet, nrows=5)
                        if len(preview.columns) >= 3 and preview.shape[0] > 0:
                            best_sheet = sheet
                            break
                    except Exception as e:
                        continue

            # If still no sheet found, use the first one
            if best_sheet is None and sheets:
                best_sheet = sheets[0]

            # Final fallback: if still None, raise clear error
            if best_sheet is None:
                raise ValueError(f"Could not determine which sheet to use in file: {filepath}")
                
            sheet_name = best_sheet
        
        # Read the Excel file
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Clean and standardize
        df = standardize_headers(df)
        
        # Try to create timestamp from available date/time information
        date_columns = [col for col in df.columns if any(term in col.lower() for term in ['date', 'day', 'month', 'year'])]
        time_columns = [col for col in df.columns if 'time' in col.lower()]
        
        if date_columns:
            main_date_col = date_columns[0]
            if time_columns:
                df['timestamp'] = pd.to_datetime(
                    df[main_date_col].astype(str) + ' ' + df[time_columns[0]].astype(str),
                    errors='coerce'
                )
            else:
                df['timestamp'] = pd.to_datetime(df[main_date_col], errors='coerce')
        
        # If no timestamp created, try to extract from sheet name
        if 'timestamp' not in df.columns or df['timestamp'].isna().all():
            try:
                sheet_date = pd.to_datetime(sheet_name, errors='raise')
                df['timestamp'] = sheet_date
            except:
                pass
        
        # Ensure required columns exist
        required_columns = ['timestamp', 'quantity']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found")
        
        # Add computed columns
        if 'target' in df.columns and 'quantity' in df.columns:
            df['efficiency'] = df['quantity'] / df['target']
        
        if 'defects' in df.columns and 'quantity' in df.columns:
            df['quality_rate'] = 1 - (df['defects'] / df['quantity'])
        
        return df
    
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}")
        return None
