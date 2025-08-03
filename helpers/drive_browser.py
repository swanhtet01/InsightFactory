import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List, Dict

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

def list_excel_files_in_folder(folder_id: str) -> List[Dict]:
    """List Excel files in a Google Drive folder, sorted by last modified."""
    service = get_drive_service()
    query = f"'{folder_id}' in parents and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false"
    results = service.files().list(q=query,
                                   spaces='drive',
                                   fields="files(id, name, modifiedTime, owners, lastModifyingUser)",
                                   orderBy="modifiedTime desc").execute()
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
    with open(dest_path, 'wb') as f:
        downloader = build('drive', 'v3', credentials=service._http.credentials).files().get_media(fileId=file_id)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%.")
        f.write(request.execute())
