"""
Enhanced data processor that combines Excel and image data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
import pytesseract
from PIL import Image
import cv2
import glob
import re
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from YAML file"""
    try:
        with open('config/portal_config.yml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def preprocess_image(image_path):
    """Preprocess image for better OCR"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gray = cv2.dilate(gray, kernel, iterations=1)
        
        return gray
    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {str(e)}")
        return None

def extract_numeric(val):
    """Extract numeric value from cell"""
    if pd.isna(val):
        return 0
    try:
        return float(str(val).replace(',', ''))
    except:
        return 0

def find_column_by_pattern(df, patterns):
    """Find column name containing any of the patterns"""
    for col in df.columns:
        col_str = str(col).lower()
        for pattern in patterns:
            if str(pattern).lower() in col_str:
                return col
            # Try removing spaces and special characters
            clean_col = ''.join(c.lower() for c in str(col) if c.isalnum())
            clean_pattern = ''.join(c.lower() for c in str(pattern) if c.isalnum())
            if clean_pattern in clean_col:
                return col
    logger.warning(f"Could not find column matching patterns: {patterns}")
    logger.info(f"Available columns: {list(df.columns)}")
    return None

def extract_data_from_image(image_path):
    """Extract data from image using OCR"""
    try:
        # Preprocess image
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            return None
            
        # Extract text using OCR
        text = pytesseract.image_to_string(processed_img)
        
        # Parse text to extract relevant data
        data = {
            'sizes': [],
            'quantities': [],
            'date': None
        }
        
        # Extract date from filename or image content
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if date_match:
            data['date'] = datetime.strptime(f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}", "%d/%m/%Y")
        
        # Extract tyre sizes and quantities
        lines = text.split('\n')
        for line in lines:
            # Look for patterns like "SIZE_PATTERN: QUANTITY"
            size_match = re.search(r'(\d{3}/\d{2}[DR]\d{2})\s*[:|-]\s*(\d+)', line)
            if size_match:
                data['sizes'].append(size_match.group(1))
                data['quantities'].append(int(size_match.group(2)))
        
        return data
    except Exception as e:
        logger.error(f"Error extracting data from image {image_path}: {str(e)}")
        return None

def validate_with_images(excel_data, image_files):
    """Cross-validate Excel data with image data"""
    try:
        image_data = []
        for img_path in image_files:
            data = extract_data_from_image(img_path)
            if data:
                image_data.append(data)
        
        if not image_data:
            return excel_data  # Return Excel data if no image data available
            
        # Compare and adjust quantities
        validated_data = excel_data.copy()
        config = load_config()
        max_variance = config.get('data_sources', {}).get('validation', {}).get('max_variance', 10)
        
        for size in validated_data['sizes']:
            excel_qty = sum(q for s, q in zip(excel_data['sizes'], excel_data['quantities']) if s == size)
            image_qty = 0
            count = 0
            
            # Get average quantity from images
            for img_data in image_data:
                if size in img_data['sizes']:
                    idx = img_data['sizes'].index(size)
                    image_qty += img_data['quantities'][idx]
                    count += 1
            
            if count > 0:
                image_avg = image_qty / count
                # If difference is more than threshold, use image data
                variance = abs(excel_qty - image_avg) / excel_qty * 100 if excel_qty > 0 else float('inf')
                if variance > max_variance:
                    idx = validated_data['sizes'].index(size)
                    validated_data['quantities'][idx] = image_avg
                    logger.info(f"Adjusted quantity for size {size} from {excel_qty} to {image_avg} based on image data (variance: {variance:.1f}%)")
        
        return validated_data
    except Exception as e:
        logger.error(f"Error validating with images: {str(e)}")
        return excel_data

def process_weekly_data(file_path, img_dir=None):
    """Process weekly production data with image validation"""
    try:
        xl = pd.ExcelFile(file_path)
        latest_sheet = sorted([s for s in xl.sheet_names if '-25' in s])[-1]
        df = pd.read_excel(file_path, sheet_name=latest_sheet)
        df.columns = [str(col).strip() for col in df.columns]
        
        data = []
        size_col = find_column_by_pattern(df, ['Size', 'Tyre', 'Pattern'])
        
        if not size_col:
            logger.warning(f"Could not find size column in weekly data")
            return pd.DataFrame()
        
        target_col = find_column_by_pattern(df, ['Target', 'Plan'])
        current_date = None
        
        # First pass to find the date
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and 'date' in str(row.iloc[0]).lower():
                try:
                    date_str = str(row.iloc[0]).split(':')[1].strip()
                    current_date = pd.to_datetime(date_str)
                except:
                    continue
        
        if current_date is None:
            current_date = pd.Timestamp.now()
        
        # Process production data
        for idx, row in df.iterrows():
            size = str(row[size_col]).strip()
            if pd.notna(size) and not any(x in size.lower() for x in ['total', 'grand', 'sum']):
                target = extract_numeric(row[target_col]) if target_col else 0
                
                # Get A, B, R values
                a_val = sum(extract_numeric(row[col]) for col in df.columns if 'A' in str(col))
                b_val = sum(extract_numeric(row[col]) for col in df.columns if 'B' in str(col))
                r_val = sum(extract_numeric(row[col]) for col in df.columns if 'R' in str(col))
                
                if a_val + b_val + r_val > 0:  # Only add rows with production
                    data.append({
                        'date': current_date,
                        'tyre_size': size,
                        'a_grade': a_val,
                        'b_grade': b_val,
                        'rework': r_val,
                        'target': target,
                        'total': a_val + b_val + r_val,
                        'quality_rate': (a_val / (a_val + b_val + r_val) * 100) if (a_val + b_val + r_val) > 0 else 0,
                        'source': 'weekly'
                    })
        
        df_data = pd.DataFrame(data)
        
        # Validate with image data if available
        if img_dir and os.path.exists(img_dir) and not df_data.empty:
            image_files = glob.glob(os.path.join(img_dir, '*.png'))
            if image_files:
                # Prepare data for validation
                excel_validation = {
                    'sizes': df_data['tyre_size'].tolist(),
                    'quantities': df_data['total'].tolist()
                }
                
                validated_data = validate_with_images(excel_validation, image_files)
                if validated_data and 'quantities' in validated_data:
                    # Update quantities based on validation
                    for i, (size, new_qty) in enumerate(zip(validated_data['sizes'], validated_data['quantities'])):
                        mask = df_data['tyre_size'] == size
                        if any(mask):
                            old_qty = df_data.loc[mask, 'total'].iloc[0]
                            if old_qty > 0:
                                ratio = new_qty / old_qty
                                df_data.loc[mask, 'a_grade'] *= ratio
                                df_data.loc[mask, 'b_grade'] *= ratio
                                df_data.loc[mask, 'rework'] *= ratio
                                df_data.loc[mask, 'total'] = new_qty
                                df_data.loc[mask, 'quality_rate'] = (df_data.loc[mask, 'a_grade'] / new_qty * 100)
        
        return df_data
    except Exception as e:
        logger.error(f"Error processing weekly data: {str(e)}")
        return pd.DataFrame()

def process_daily_data(file_path, img_dir=None):
    """Process daily production data"""
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]
        
        data = []
        current_date = None
        
        size_col = find_column_by_pattern(df, ['Size', 'Tyre Size'])
        target_col = find_column_by_pattern(df, ['Target', 'Plan'])
        
        if not size_col:
            logger.warning(f"Could not find size column in daily data")
            return pd.DataFrame()
        
        # Process each row
        for idx, row in df.iterrows():
            # Check for date rows
            if pd.notna(row.iloc[0]):
                date_str = str(row.iloc[0])
                if 'date' in date_str.lower():
                    try:
                        date_parts = date_str.split(':')[1].strip().split('/')
                        current_date = pd.Timestamp(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))
                    except:
                        continue
            
            # Skip if we haven't found a valid date yet
            if current_date is None:
                continue
            
            size = str(row[size_col]).strip()
            if pd.notna(size) and not any(x in size.lower() for x in ['total', 'grand', 'sum']):
                target = extract_numeric(row[target_col]) if target_col else 0
                
                # Get A, B, R values
                a_val = sum(extract_numeric(row[col]) for col in df.columns if 'A' in str(col))
                b_val = sum(extract_numeric(row[col]) for col in df.columns if 'B' in str(col))
                r_val = sum(extract_numeric(row[col]) for col in df.columns if 'R' in str(col))
                
                if a_val + b_val + r_val > 0:  # Only add rows with production
                    data.append({
                        'date': current_date,
                        'tyre_size': size,
                        'a_grade': a_val,
                        'b_grade': b_val,
                        'rework': r_val,
                        'target': target,
                        'total': a_val + b_val + r_val,
                        'quality_rate': (a_val / (a_val + b_val + r_val) * 100) if (a_val + b_val + r_val) > 0 else 0,
                        'source': 'daily'
                    })
        
        df_data = pd.DataFrame(data)
        
        # Validate with image data if available
        if img_dir and os.path.exists(img_dir) and not df_data.empty:
            image_files = glob.glob(os.path.join(img_dir, '*.png'))
            if image_files:
                # Prepare data for validation
                excel_validation = {
                    'sizes': df_data['tyre_size'].tolist(),
                    'quantities': df_data['total'].tolist()
                }
                
                validated_data = validate_with_images(excel_validation, image_files)
                if validated_data and 'quantities' in validated_data:
                    # Update quantities based on validation
                    for i, (size, new_qty) in enumerate(zip(validated_data['sizes'], validated_data['quantities'])):
                        mask = df_data['tyre_size'] == size
                        if any(mask):
                            old_qty = df_data.loc[mask, 'total'].iloc[0]
                            if old_qty > 0:
                                ratio = new_qty / old_qty
                                df_data.loc[mask, 'a_grade'] *= ratio
                                df_data.loc[mask, 'b_grade'] *= ratio
                                df_data.loc[mask, 'rework'] *= ratio
                                df_data.loc[mask, 'total'] = new_qty
                                df_data.loc[mask, 'quality_rate'] = (df_data.loc[mask, 'a_grade'] / new_qty * 100)
        
        return df_data
    except Exception as e:
        logger.error(f"Error processing daily data: {str(e)}")
        return pd.DataFrame()

def process_monthly_data(file_path, img_dir=None):
    """Process monthly production data"""
    try:
        xl = pd.ExcelFile(file_path)
        current_month = datetime.now().strftime('%B').lower()
        month_sheets = [s for s in xl.sheet_names if current_month in s.lower()]
        if not month_sheets:
            month_sheets = [s for s in xl.sheet_names if '-25' in s]
        
        if not month_sheets:
            logger.warning(f"Could not find sheet for {current_month}")
            return pd.DataFrame()
        
        latest_sheet = sorted(month_sheets)[-1]
        df = pd.read_excel(file_path, sheet_name=latest_sheet)
        df.columns = [str(col).strip() for col in df.columns]
        
        data = []
        size_col = find_column_by_pattern(df, ['Tyre Size', 'Size'])
        target_col = find_column_by_pattern(df, ['Target', 'Plan'])
        
        if not size_col:
            logger.warning(f"Could not find size column in monthly data")
            return pd.DataFrame()
        
        # Process data
        for idx, row in df.iterrows():
            size = str(row[size_col]).strip()
            if pd.notna(size) and not any(x in size.lower() for x in ['total', 'grand', 'sum']):
                target = extract_numeric(row[target_col]) if target_col else 0
                
                # Get daily production
                for day in range(1, 32):
                    if f'{day}' in df.columns:
                        qty = extract_numeric(row[f'{day}'])
                        if qty > 0:
                            data.append({
                                'date': pd.Timestamp(2025, datetime.now().month, day),
                                'tyre_size': size,
                                'quantity': qty,
                                'target': target / 30,  # Distribute monthly target across days
                                'source': 'monthly'
                            })
        
        df_data = pd.DataFrame(data)
        
        # Validate with image data if available
        if img_dir and os.path.exists(img_dir) and not df_data.empty:
            image_files = glob.glob(os.path.join(img_dir, '*.png'))
            if image_files:
                # Prepare data for validation
                excel_validation = {
                    'sizes': df_data['tyre_size'].tolist(),
                    'quantities': df_data['quantity'].tolist()
                }
                
                validated_data = validate_with_images(excel_validation, image_files)
                if validated_data and 'quantities' in validated_data:
                    # Update quantities based on validation
                    for i, (size, new_qty) in enumerate(zip(validated_data['sizes'], validated_data['quantities'])):
                        mask = df_data['tyre_size'] == size
                        if any(mask):
                            df_data.loc[mask, 'quantity'] = new_qty
                            if target:
                                df_data.loc[mask, 'target'] = target / 30
        
        return df_data
    except Exception as e:
        logger.error(f"Error processing monthly data: {str(e)}")
        return pd.DataFrame()

def extract_year_data(file_path):
    """Extract data from yearly Excel file"""
    try:
        df = pd.read_excel(file_path, sheet_name=None)
        yearly_data = {
            'monthly_totals': {},
            'size_trends': {},
            'yearly_total': 0,
            'projections': {}
        }
        
        for sheet_name, sheet_df in df.items():
            if '2025' in sheet_name:
                sheet_df.columns = [str(col).strip() for col in sheet_df.columns]
                
                size_col = find_column_by_pattern(sheet_df, ['Size', 'Tyre', 'Pattern'])
                if not size_col:
                    continue
                
                for idx, row in sheet_df.iterrows():
                    size = str(row[size_col]).strip()
                    if pd.notna(size) and not any(x in size.lower() for x in ['total', 'grand', 'sum']):
                        monthly_values = {}
                        for col in sheet_df.columns:
                            if isinstance(col, str):
                                month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', col.lower())
                                if month_match:
                                    month = month_match.group(1)
                                    val = row[col]
                                    if pd.notna(val):
                                        try:
                                            val = float(str(val).replace(',', ''))
                                            monthly_values[month] = val
                                        except:
                                            continue
                        
                        if monthly_values:
                            yearly_data['size_trends'][size] = monthly_values
                            
                            for month, val in monthly_values.items():
                                if month not in yearly_data['monthly_totals']:
                                    yearly_data['monthly_totals'][month] = 0
                                yearly_data['monthly_totals'][month] += val
                            
                            # Calculate projections
                            actual_months = len(monthly_values)
                            if actual_months > 0:
                                avg_monthly = sum(monthly_values.values()) / actual_months
                                yearly_projection = avg_monthly * 12
                                yearly_data['projections'][size] = yearly_projection
                                yearly_data['yearly_total'] += sum(monthly_values.values())
        
        return yearly_data
    except Exception as e:
        logger.error(f"Error processing yearly data: {str(e)}")
        return None

def get_latest_week_sheet(excel_file):
    """Get the latest week sheet from weekly data."""
    try:
        xl = pd.ExcelFile(excel_file)
        sheets = xl.sheet_names
        # Filter sheets that match week pattern (e.g., '01-25', '02-25')
        week_sheets = [s for s in sheets if s.replace('-', '').isdigit()]
        if not week_sheets:
            return None
        # Sort by week number
        latest_sheet = sorted(week_sheets, key=lambda x: int(x.split('-')[0]))[-1]
        return latest_sheet
    except Exception as e:
        logger.error(f"Error getting latest week sheet: {str(e)}")
        return None

def get_latest_production_data():
    """Get the latest production data from all sources."""
    data_dir = 'data'
    all_data = []
    
    # Process each data source
    for file in os.listdir(data_dir):
        if file.endswith('.xlsx'):
            file_path = os.path.join(data_dir, file)
            if 'Weekly' in file:
                weekly_data = process_weekly_data(file_path, os.path.join(data_dir, 'images/2025/weekly'))
                if not weekly_data.empty:
                    all_data.append(weekly_data)
            elif 'Daily' in file:
                daily_data = process_daily_data(file_path, os.path.join(data_dir, 'images/2025/daily'))
                if not daily_data.empty:
                    all_data.append(daily_data)
            elif 'year' in file.lower():
                annual_data = extract_year_data(file_path)
                if annual_data:
                    transformed_data = []
                    for size, trends in annual_data['size_trends'].items():
                        for month, qty in trends.items():
                            transformed_data.append({
                                'tyre_size': size,
                                'month': month,
                                'quantity': qty,
                                'source': 'annual'
                            })
                    if transformed_data:
                        all_data.append(pd.DataFrame(transformed_data))
    
    if not all_data:
        return pd.DataFrame()
    
    # Combine all data sources
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Add timestamp column
    if 'date' in combined_df.columns:
        combined_df['timestamp'] = pd.to_datetime(combined_df['date'])
    elif 'month' in combined_df.columns:
        combined_df['timestamp'] = pd.to_datetime('2025-' + combined_df['month'] + '-01')
    
    # Sort by date
    if 'timestamp' in combined_df.columns:
        combined_df = combined_df.sort_values('timestamp')
    
    return combined_df
