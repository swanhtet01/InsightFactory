"""
Image processing module for production data extraction.
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename patterns."""
    patterns = [
        r'(\d{4})[-_]?(\d{1,2})[-_]?(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})[-_]?(\d{1,2})[-_]?(\d{4})',  # DD-MM-YYYY
        r'(\d{4})',  # Just year
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                try:
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:  # DD-MM-YYYY
                        return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                except ValueError:
                    continue
            elif len(groups) == 1:  # Just year
                try:
                    return datetime(int(groups[0]), 1, 1)
                except ValueError:
                    continue
    return None

def preprocess_image(image_path):
    """Preprocess image for better OCR results."""
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to preprocess the image
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Apply dilation to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    gray = cv2.dilate(gray, kernel, iterations=1)
    
    return gray

def extract_data_from_image(image_path):
    """
    Extract production data from image using OCR.
    Returns dict with extracted data and confidence scores.
    """
    try:
        # Preprocess image
        processed_img = preprocess_image(image_path)
        
        # Perform OCR
        text = pytesseract.image_to_string(processed_img)
        
        # Extract data
        data = {
            'date': None,
            'production': None,
            'reject': None,
            'target': None,
            'confidence': 0,
            'source': 'image'
        }
        
        # Try to find date in image
        date_patterns = [
            r'Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Add various date parsing attempts here
                    data['date'] = datetime.strptime(date_str, '%d/%m/%Y')
                    break
                except ValueError:
                    continue
        
        # Try to find production numbers
        production_patterns = [
            r'Production[:\s]+(\d+)',
            r'Output[:\s]+(\d+)',
            r'Quantity[:\s]+(\d+)'
        ]
        for pattern in production_patterns:
            match = re.search(pattern, text)
            if match:
                data['production'] = int(match.group(1))
                break
        
        # Try to find reject numbers
        reject_patterns = [
            r'Reject[:\s]+(\d+)',
            r'Defect[:\s]+(\d+)',
            r'Scrap[:\s]+(\d+)'
        ]
        for pattern in reject_patterns:
            match = re.search(pattern, text)
            if match:
                data['reject'] = int(match.group(1))
                break
        
        # Calculate confidence score based on completeness
        found_fields = sum(1 for v in data.values() if v is not None) - 1  # Exclude 'source'
        data['confidence'] = (found_fields / 3) * 100  # Date, production, reject = 3 fields
        
        return data
    
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None
