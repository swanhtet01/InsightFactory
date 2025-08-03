"""
Data validation and source comparison module.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def compare_data_sources(excel_data, image_data, date):
    """
    Compare production data from different sources for the same date.
    Returns the most reliable data based on validation rules.
    """
    if not excel_data and not image_data:
        return None
        
    # If only one source exists, use it
    if not excel_data:
        return image_data
    if not image_data:
        return excel_data
        
    # Compare values and calculate confidence
    excel_conf = 0
    image_conf = 0
    
    # Check for reasonable values
    def is_reasonable(value, field):
        if field == 'production':
            return 0 <= value <= 100000  # Adjust based on actual production capacity
        elif field == 'reject':
            return 0 <= value <= 10000
        return True
    
    # Score each source
    for field in ['production', 'reject', 'target']:
        if field in excel_data and is_reasonable(excel_data[field], field):
            excel_conf += 1
        if field in image_data and is_reasonable(image_data[field], field):
            image_conf += 1
            
        # If both sources have the field, check for large discrepancies
        if field in excel_data and field in image_data:
            excel_val = excel_data[field]
            image_val = image_data[field]
            if excel_val and image_val:
                diff_pct = abs(excel_val - image_val) / max(excel_val, image_val)
                if diff_pct <= 0.1:  # Within 10%
                    excel_conf += 1
                    image_conf += 1
                elif diff_pct <= 0.2:  # Within 20%
                    excel_conf += 0.5
                    image_conf += 0.5
    
    # Check data freshness
    excel_time = excel_data.get('timestamp')
    image_time = image_data.get('timestamp')
    if excel_time and image_time:
        # Prefer more recent data
        if excel_time > image_time:
            excel_conf += 1
        else:
            image_conf += 1
    
    # Return the source with higher confidence
    if excel_conf >= image_conf:
        result = excel_data.copy()
        result['confidence'] = (excel_conf / 6) * 100  # Normalize to percentage
        result['source'] = 'excel'
    else:
        result = image_data.copy()
        result['confidence'] = (image_conf / 6) * 100
        result['source'] = 'image'
    
    return result

def validate_and_merge_sources(data_dir):
    """
    Validate and merge data from all available sources.
    Returns a list of validated data points with source information.
    """
    # Load sync metadata
    metadata_path = os.path.join(data_dir, 'sync_metadata.json')
    if not os.path.exists(metadata_path):
        return []
        
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Group files by date
    date_files = {}
    for file_info in metadata['downloaded_files']:
        file_date = datetime.fromisoformat(file_info['createdTime'].replace('Z', '+00:00')).date()
        if file_date not in date_files:
            date_files[file_date] = {'excel': [], 'image': [], 'csv': []}
        
        ext = os.path.splitext(file_info['path'])[1].lower()
        if ext in ['.xlsx', '.xls']:
            date_files[file_date]['excel'].append(file_info)
        elif ext in ['.jpg', '.png', '.jpeg']:
            date_files[file_date]['image'].append(file_info)
        elif ext == '.csv':
            date_files[file_date]['csv'].append(file_info)
    
    # Process each date's data
    validated_data = []
    for date, sources in date_files.items():
        excel_data = None
        image_data = None
        
        # Get Excel data
        if sources['excel']:
            # Use the most recent Excel file
            latest_excel = max(sources['excel'], key=lambda x: x['createdTime'])
            try:
                df = pd.read_excel(latest_excel['path'])
                excel_data = {
                    'date': date,
                    'production': df['Production_Quantity'].sum(),
                    'reject': df['Rejected_Quantity'].sum() if 'Rejected_Quantity' in df.columns else None,
                    'target': df['Target_Quantity'].sum() if 'Target_Quantity' in df.columns else None,
                    'timestamp': datetime.fromisoformat(latest_excel['createdTime'].replace('Z', '+00:00')),
                    'source': 'excel'
                }
            except Exception as e:
                print(f"Error processing Excel file: {str(e)}")
        
        # Get image data
        if sources['image']:
            # Use the most recent image
            latest_image = max(sources['image'], key=lambda x: x['createdTime'])
            try:
                from helpers.image_processor import extract_data_from_image
                image_data = extract_data_from_image(latest_image['path'])
                if image_data:
                    image_data['timestamp'] = datetime.fromisoformat(latest_image['createdTime'].replace('Z', '+00:00'))
            except Exception as e:
                print(f"Error processing image: {str(e)}")
        
        # Compare and validate
        validated = compare_data_sources(excel_data, image_data, date)
        if validated:
            validated_data.append(validated)
    
    return validated_data
