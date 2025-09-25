from __future__ import annotations

import io
import json
import pickle
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_IMPERSONATE_SUBJECT,
    GOOGLE_TOKEN_FILE,
)

SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

LEGACY_TOKEN_FILE = GOOGLE_TOKEN_FILE.with_suffix(".pickle")


def _read_credentials_file() -> dict:
    if not GOOGLE_CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google credentials file not found at {GOOGLE_CREDENTIALS_FILE}. "
            "Provide a service-account JSON or OAuth client secrets file."
        )
    with GOOGLE_CREDENTIALS_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_service_account_credentials(payload: dict) -> Optional[Credentials]:
    if payload.get("type") != "service_account":
        return None
    creds = service_account.Credentials.from_service_account_info(payload, scopes=SCOPES)
    if GOOGLE_IMPERSONATE_SUBJECT:
        creds = creds.with_subject(GOOGLE_IMPERSONATE_SUBJECT)
    return creds


def _load_authorized_user_credentials(payload: dict) -> Credentials:
    creds: Optional[Credentials] = None
    if GOOGLE_TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), SCOPES)
        except Exception:
            creds = None
    elif LEGACY_TOKEN_FILE.exists():
        with LEGACY_TOKEN_FILE.open("rb") as token_handle:
            creds = pickle.load(token_handle)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(GOOGLE_CREDENTIALS_FILE), SCOPES
        )
        creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        GOOGLE_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_drive_service():
    payload = _read_credentials_file()
    creds = _load_service_account_credentials(payload)
    if creds is None:
        creds = _load_authorized_user_credentials(payload)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

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
