import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List, Dict
import io
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '../credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '../token.pickle')

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(folder_id: str, mime_types: List[str]) -> List[Dict]:
    """List files in a Google Drive folder matching given MIME types."""
    service = get_drive_service()
    mime_query = " or ".join([f"mimeType='{m}'" for m in mime_types])
    query = f"'{folder_id}' in parents and ({mime_query}) and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields="files(id, name, mimeType, modifiedTime, owners, lastModifyingUser)",
        orderBy="modifiedTime desc",
    ).execute()
    return results.get('files', [])

def get_file_activity(file_id: str) -> Dict:
    """Get activity (last modified, owner, etc.) for a file."""
    service = get_drive_service()
    file = service.files().get(fileId=file_id,
                               fields="id, name, modifiedTime, owners, lastModifyingUser, webViewLink").execute()
    return file

def download_file(file_id: str, dest_path: str):
    """Download a file from Google Drive to dest_path."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {int(status.progress() * 100)}%")
