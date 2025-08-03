"""
Folder analyzer for Insight Factory Assistant.
Scans the data/ folder, detects file types, processes tabular files, and combines data.
"""
import os
import pandas as pd
import json
from datetime import datetime
from helpers.excel_processor import process_excel_file
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Constants
SUPPORTED_EXTENSIONS = {
    'excel': ['.xlsx', '.xls'],
    'csv': ['.csv'],
    'image': ['.png', '.jpg', '.jpeg']
}

def analyze_data_folder(data_dir="data", use_cache=True):
    """Analyze all files in the data directory with caching and data validation."""
    results = []
    all_data = pd.DataFrame()
    
    # Process each file in the directory
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        
        # Skip if not a file
        if not os.path.isfile(filepath):
            continue
            
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        try:
            # Process Excel files
            if ext in SUPPORTED_EXTENSIONS['excel']:
                df = process_excel_file(filepath)
                if df is not None and not df.empty:
                    all_data = pd.concat([all_data, df], ignore_index=True)
                    
            # Process CSV files
            elif ext in SUPPORTED_EXTENSIONS['csv']:
                df = pd.read_csv(filepath)
                if 'date' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['date'])
                if df is not None and not df.empty:
                    all_data = pd.concat([all_data, df], ignore_index=True)
                    
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue
    
    # Sort and save processed data
    if not all_data.empty:
        if 'timestamp' in all_data.columns:
            all_data = all_data.sort_values('timestamp')
        all_data.to_json(os.path.join(data_dir, 'processed_data.json'))
        print(f"\nResults saved to {data_dir}/processed_data.json")
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    # Ensure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Helper function to check if cache is valid
    def is_cache_valid(file_path, cache_entry):
        if not cache_entry or 'hash' not in cache_entry or 'timestamp' not in cache_entry:
            return False
        
        # Check if file was modified
        with open(file_path, 'rb') as f:
            current_hash = hashlib.md5(f.read()).hexdigest()
        
        # Cache is valid if hash matches and cache is less than 1 hour old
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        return (current_hash == cache_entry['hash'] and 
                datetime.now() - cache_time < timedelta(hours=1))
    
    for fname in os.listdir(data_dir):
        fpath = os.path.join(data_dir, fname)
        if not os.path.isfile(fpath):
            continue
        
        result = {"file": fname}
        ext = os.path.splitext(fname)[-1].lower()
        
        try:
            # Check cache first
            if use_cache and fname in cache and is_cache_valid(fpath, cache[fname]):
                results.append(cache[fname]['data'])
                continue
            
            # Process based on file type
            if ext in [".xlsx", ".xls"]:
                from helpers.gpt_cleaner import clean_headers
                excel_file = pd.ExcelFile(fpath)
                sheet_data = []
                file_date = None
                
                # First pass: Analyze all sheets
                for sheet in excel_file.sheet_names:
                    try:
                        df_temp = pd.read_excel(fpath, sheet_name=sheet, header=None)
                        
                        # Skip empty sheets
                        if df_temp.empty or df_temp.dropna(how='all').empty:
                            continue
                            
                        # Find potential header rows and data start
                        header_candidates = []
                        for idx, row in df_temp.iterrows():
                            cells = [str(val).lower().strip() for val in row if pd.notna(val)]
                            if not cells:
                                continue
                                
                            # Score this row as a potential header
                            score = 0
                            header_text = " ".join(cells)
                            
                            # Production-related terms
                            if any(term in header_text.lower() for term in ['production', 'output', 'quantity', 'produced']):
                                score += 5
                            if any(term in header_text.lower() for term in ['tyre', 'tire', 'product']):
                                score += 4
                            if any(term in header_text.lower() for term in ['date', 'period', 'week', 'month', 'year']):
                                score += 3
                            if any(term in header_text.lower() for term in ['reject', 'defect', 'scrap', 'rework', 'waste']):
                                score += 3
                            if any(term in header_text.lower() for term in ['shift', 'batch', 'line', 'target', 'plan', 'goal']):
                                score += 2
                            if any(term in header_text.lower() for term in ['efficiency', 'yield', 'rate', 'quality']):
                                score += 2
                                
                            if score > 0:
                                header_candidates.append({
                                    'row': idx,
                                    'score': score,
                                    'text': header_text,
                                    'cells': cells,
                                    'source': 'excel'
                                })
                        
                        if header_candidates:
                            # Use the most promising header row
                            best_header = max(header_candidates, key=lambda x: x['score'])
                            
                            # Re-read with proper header
                            df = pd.read_excel(fpath, sheet_name=sheet, header=best_header['row'])
                            
                            # Clean and standardize column names
                            cleaned_df, header_mapping = clean_headers(df)
                            
                            # Ensure all columns are string type first
                            cleaned_df.columns = cleaned_df.columns.astype(str)
                            
                            # Store original to cleaned column mapping for reference
                            result['column_mapping'] = header_mapping
                            
                            # Detect and standardize common column patterns
                            standard_columns = {
                                'date': ['date', 'period', 'week', 'month', 'timestamp'],
                                'production': ['production', 'output', 'produced', 'quantity'],
                                'target': ['target', 'plan', 'goal', 'forecast'],
                                'reject': ['reject', 'defect', 'scrap', 'waste'],
                                'rework': ['rework', 'repair', 'reprocess'],
                                'shift': ['shift', 'batch', 'line'],
                                'weight': ['weight', 'mass', 'kg', 'ton'],
                                'size': ['size', 'dimension', 'spec'],
                                'type': ['type', 'model', 'product', 'category']
                            }
                            
                            column_categories = {}
                            for col in cleaned_df.columns:
                                col_lower = str(col).lower()
                                for category, patterns in standard_columns.items():
                                    if any(pattern in col_lower for pattern in patterns):
                                        column_categories[col] = category
                                        break
                            
                            result['column_categories'] = column_categories
                            
                            # Convert columns to appropriate types based on category
                            for col, category in column_categories.items():
                                if category == 'date':
                                    # Try multiple date formats
                                    date_formats = [
                                        '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y',
                                        '%Y/%m/%d', '%d-%m-%y', '%Y-%m'
                                    ]
                                    for fmt in date_formats:
                                        try:
                                            cleaned_df[col] = pd.to_datetime(
                                                cleaned_df[col],
                                                format=fmt,
                                                errors='coerce'
                                            )
                                            break
                                        except:
                                            continue
                                            
                                # Numeric columns
                                elif any(term in col_lower for term in [
                                    'quantity', 'production', 'reject', 'count',
                                    'number', 'amount', 'target', 'actual'
                                ]):
                                    cleaned_df[col] = pd.to_numeric(
                                        cleaned_df[col].astype(str).str.extract('(\d+)', expand=False),
                                        errors='coerce'
                                    )
                                    
                                # Percentage columns
                                elif any(term in col_lower for term in [
                                    'rate', 'efficiency', 'yield', 'percentage'
                                ]):
                                    cleaned_df[col] = pd.to_numeric(
                                        cleaned_df[col].astype(str).str.extract('(\d+\.?\d*)', expand=False),
                                        errors='coerce'
                                    )
                            
                            # Prepare data for storage
                            sheet_data.append({
                                'sheet_name': sheet,
                                'score': best_header['score'],
                                'df': cleaned_df.copy(),
                                'row_count': len(cleaned_df.dropna(how='all')),
                                'date_range': (
                                    cleaned_df.select_dtypes(include=['datetime64']).min().min(),
                                    cleaned_df.select_dtypes(include=['datetime64']).max().max()
                                ) if not cleaned_df.select_dtypes(include=['datetime64']).empty else None
                            })
                    except Exception as e:
                        print(f"Error processing sheet {sheet}: {str(e)}")
                        continue
                
                # Select best sheet based on scoring and recency
                if sheet_data:
                    # Prioritize sheets with recent data
                    for sheet_info in sheet_data:
                        if sheet_info['date_range']:
                            sheet_info['score'] += (sheet_info['date_range'][1].year * 12 + 
                                                  sheet_info['date_range'][1].month)
                    
                    best_sheet_info = max(sheet_data, key=lambda x: x['score'])
                    best_sheet_info = max(sheet_data, key=lambda x: x['score'])
                    df = best_sheet_info['df']
                    best_sheet = best_sheet_info['sheet_name']
                    best_score = best_sheet_info['score']
                    data_start = 0
                
                # Re-read the best sheet with proper header row
                print(f"\nProcessing {fname} (Sheet: {best_sheet})...")
                print(f"Shape: {df.shape}")
                print(f"Found headers at row {data_start + 1}")
                
                # Basic data cleaning
                # Convert date-like columns to datetime
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(date_word in col_lower for date_word in ['date', 'day', 'month', 'year']):
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except:
                            pass
                
                # Remove completely empty columns and rows
                df = df.dropna(axis=1, how='all')
                df = df.dropna(axis=0, how='all')
                
                # Store processed dataframe
                # Convert DataFrame to a format that's easier to serialize
                processed_df = df.copy()
                for col in processed_df.columns:
                    if pd.api.types.is_datetime64_any_dtype(processed_df[col]):
                        processed_df[col] = processed_df[col].dt.strftime('%Y-%m-%d')
                    elif pd.api.types.is_float_dtype(processed_df[col]):
                        processed_df[col] = processed_df[col].fillna(0).astype(float)
                    elif pd.api.types.is_integer_dtype(processed_df[col]):
                        processed_df[col] = processed_df[col].fillna(0).astype(int)
                    else:
                        processed_df[col] = processed_df[col].fillna('').astype(str)
                
                result['df_json'] = processed_df.to_json(date_format='iso', orient='records')
                result['df_columns'] = processed_df.columns.tolist()
                result['sheet_name'] = best_sheet_info['sheet_name']
                result['relevance_score'] = best_score
                
                # Clean headers using GPT
                cleaned_df, header_error = clean_headers(df)
                if header_error:
                    print(f"Header cleaning warning: {header_error}")
                    result["header_cleaning_error"] = header_error
                else:
                    print("Headers cleaned successfully")
                    print(f"Cleaned columns: {list(cleaned_df.columns)}")
                
                # Compute KPIs
                try:
                    kpis = compute_kpis(cleaned_df)
                    result["kpis"] = kpis
                    print(f"Computed KPIs: {kpis}")
                except Exception as e:
                    print(f"Error computing KPIs: {e}")
                    result["kpi_error"] = str(e)
                
                # Generate summary
                try:
                    summary = generate_summary(cleaned_df, kpis if "kpis" in result else None)
                    result["summary"] = summary
                except Exception as e:
                    print(f"Error generating summary: {e}")
                    result["summary_error"] = str(e)
            
            else:
                print(f"Skipping unsupported file type: {fname}")
                result["error"] = f"Unsupported file type: {ext}"
                
        except Exception as e:
            error_msg = f"Error processing {fname}: {str(e)}"
            print(error_msg)
            result["error"] = error_msg
        
        results.append(result)
    
    # Save results
    results_path = os.path.join(data_dir, 'processed_data.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")
    return results

if __name__ == "__main__":
    print("Analyzing all files in data/ ...")
    results = analyze_data_folder()
    for r in results:
        print(f"File: {r.get('file')}, KPIs: {r.get('kpis')}, Summary: {r.get('summary')}, Error: {r.get('error')}")
