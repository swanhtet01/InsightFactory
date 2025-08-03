"""
Google Drive watcher and sync module.
"""

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import io
import datetime
import os
import json
import sys
import re
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from helpers.analyze_folder import analyze_data_folder

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'  # You must download this from Google Cloud Console
TOKEN_PICKLE = 'token.pickle'
FOLDER_ID = '1-1b9zryLrFrS3yJVrmSQ0UlcwoPmwSEt'  # Hardcode the Google Drive folder ID for all users
DOWNLOAD_DIR = 'data/'
DOWNLOADED_RECORD = 'downloaded_files.json'
LATEST_FILE_RECORD = 'latest_file.json'

# Helper: Authenticate and build Drive service

def get_drive_service():
    """Initialize and authenticate Google Drive service."""
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def get_file_metadata(service, file_id):
    """Get detailed metadata for a file."""
    try:
        return service.files().get(
            fileId=file_id, 
            fields='id, name, mimeType, modifiedTime, createdTime, version, size'
        ).execute()
    except Exception as e:
        print(f"Error getting metadata for file {file_id}: {e}")
        return None

def validate_excel_structure(file_path):
    """Validate Excel file structure and find the correct sheet."""
    try:
        xl = pd.ExcelFile(file_path)
        sheets = xl.sheet_names
        
        # Priority patterns for sheet names
        patterns = [
            r'(?i)(production|prod)\s*data',
            r'(?i)(daily|weekly|monthly)\s*report',
            r'(?i)(kpi|metrics|dashboard)',
            r'(?i)(raw|main|primary)\s*data'
        ]
        
        for pattern in patterns:
            for sheet in sheets:
                if re.search(pattern, sheet):
                    # Preview the sheet to validate structure
                    df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
                    if len(df.columns) >= 3:  # Basic validation
                        return sheet
                        
        # If no pattern matched, return first non-empty sheet
        for sheet in sheets:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
            if not df.empty:
                return sheet
                
        return sheets[0]  # Fallback to first sheet
    except Exception as e:
        print(f"Error validating Excel structure: {e}")
        return None

def get_latest_files(service, folder_id, file_types=None):
    """Get latest versions of all relevant files."""
    if file_types is None:
        file_types = {
            'excel': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'image': ['image/png', 'image/jpeg'],
            'csv': ['text/csv']
        }
    
    files = {}
    for category, mime_types in file_types.items():
        try:
            query = f"'{folder_id}' in parents and ("
            query += " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            query += ")"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, createdTime, version)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files[category] = results.get('files', [])
        except Exception as e:
            print(f"Error fetching {category} files: {e}")
            files[category] = []
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

# Main: Sync latest week of files
def get_latest_version(files):
    """Get the latest version of each file based on name and date."""
    latest_versions = {}
    for file in files:
        name_base = file['name'].split(' (')[0]  # Remove version numbers like " (1)"
        created_time = datetime.datetime.strptime(file['createdTime'][:19], '%Y-%m-%dT%H:%M:%S')
        
        if name_base not in latest_versions or created_time > latest_versions[name_base]['created_time']:
            latest_versions[name_base] = {
                'file': file,
                'created_time': created_time
            }
    
    return [info['file'] for info in latest_versions.values()]

def sync_drive(download_all=False):
    """
    Sync and download all files (Excel, CSV, images, etc.) from Google Drive.
    If download_all is True, download all files in the folder. Otherwise, only the last week.
    Returns:
        tuple: List of downloaded file paths, new files, and all downloaded files.
    """
    service = get_drive_service()
    
    # Get all production-related files (Excel, images, etc.)
    query = f"'{FOLDER_ID}' in parents and trashed=false and ("
    query += " or ".join([
        "mimeType contains 'spreadsheet'",
        "mimeType contains 'excel'",
        "mimeType contains 'image'",
        "mimeType contains 'csv'"
    ])
    query += ")"
    results = service.files().list(q=query, fields="files(id, name, mimeType, createdTime)").execute()
    files = results.get('files', [])
    if not download_all:
        week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        files = [f for f in files if datetime.datetime.strptime(f['createdTime'][:19], '%Y-%m-%dT%H:%M:%S') >= week_ago]
    downloaded = []
    for file in files:
        mime = file['mimeType']
        file_id = file['id']
        file_name = file['name']
        out_path = os.path.join(DOWNLOAD_DIR, file_name)
        fh = io.BytesIO()
        try:
            # Skip Google Drive folders
            if mime == 'application/vnd.google-apps.folder':
                print(f"[SKIP] Unsupported Google file type: {file_name} ({mime})")
                continue
            # Handle Google Docs/Sheets/Slides export
            if mime == 'application/vnd.google-apps.document':
                export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                if not file_name.lower().endswith('.docx'):
                    out_path += '.docx'
            elif mime == 'application/vnd.google-apps.spreadsheet':
                export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                if not file_name.lower().endswith('.xlsx'):
                    out_path += '.xlsx'
            elif mime == 'application/vnd.google-apps.presentation':
                export_mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                if not file_name.lower().endswith('.pptx'):
                    out_path += '.pptx'
            elif mime.startswith('application/vnd.google-apps'):  # Other Google types not supported
                print(f"[SKIP] Unsupported Google file type: {file_name} ({mime})")
                continue
            else:
                request = service.files().get_media(fileId=file_id)
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            with open(out_path, 'wb') as f:
                f.write(fh.getbuffer())
            downloaded.append({'path': out_path, 'createdTime': file['createdTime'], 'name': file_name, 'mimeType': mime})
        except Exception as e:
            print(f"[ERROR] Failed to download {file_name} ({mime}): {e}")
            continue
    # Track new files
    prev_files = []
    if os.path.exists(DOWNLOADED_RECORD):
        with open(DOWNLOADED_RECORD, 'r') as f:
            prev_files = json.load(f)
    prev_names = set(f['name'] for f in prev_files)
    new_files = [f for f in downloaded if f['name'] not in prev_names]
    if downloaded:
        with open(DOWNLOADED_RECORD, 'w') as f:
            json.dump(downloaded, f, indent=2)
    # Save latest file info
    if downloaded:
        latest = max(downloaded, key=lambda x: x['createdTime'])
        with open(LATEST_FILE_RECORD, 'w') as f:
            json.dump(latest, f, indent=2)
    return [f['path'] for f in downloaded], new_files, downloaded

# On-demand: Download a specific file by name
def download_file_by_name(filename):
    service = get_drive_service()
    query = f"'{FOLDER_ID}' in parents and name='{filename}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if not files:
        return None
    file = files[0]
    request = service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    out_path = os.path.join(DOWNLOAD_DIR, file['name'])
    with open(out_path, 'wb') as f:
        f.write(fh.getbuffer())
    return out_path

# Analyze all files in the samples/ folder
def analyze_samples_folder():
    """
    Analyze all files in the samples/ folder for KPIs and summaries.
    Results are saved to data/processed_data.json.
    """
