"""Simple Google Drive watcher that syncs files when changes are detected."""

import time
from helpers.drive_sync import sync_drive_files
from helpers.drive_browser import get_drive_service
from helpers.pipeline_runner import run_full_pipeline
from config import GOOGLE_DRIVE_FOLDER_IDS


def watch_drive_folder(interval: int = 60, folder_ids=None) -> None:
    """Watch the Google Drive folders for changes and sync new files."""
    folder_ids = folder_ids or GOOGLE_DRIVE_FOLDER_IDS
    service = get_drive_service()
    page_token = service.changes().getStartPageToken().execute()["startPageToken"]
    folder_ids_set = set(folder_ids)
    while True:
        response = service.changes().list(
            pageToken=page_token,
            spaces="drive",
            fields="nextPageToken, newStartPageToken, changes(fileId, removed, file(id, name, mimeType, parents))",
        ).execute()
        for change in response.get("changes", []):
            file = change.get("file")
            if file and not change.get("removed") and any(
                fid in file.get("parents", []) for fid in folder_ids_set
            ):
                print(f"Detected change in: {file['name']}")
                files = sync_drive_files(folder_ids)
                run_full_pipeline(files)
        if "newStartPageToken" in response:
            page_token = response["newStartPageToken"]
        elif response.get("nextPageToken"):
            page_token = response["nextPageToken"]
        time.sleep(interval)


if __name__ == "__main__":
    files = sync_drive_files()
    run_full_pipeline(files)
    watch_drive_folder()

