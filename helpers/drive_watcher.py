"""Simple Google Drive watcher that syncs files when changes are detected."""

import time
from helpers.drive_sync import sync_drive_files
from helpers.drive_browser import get_drive_service
from helpers.pipeline_runner import run_full_pipeline

FOLDER_ID = "1-1b9zryLrFrS3yJVrmSQ0UlcwoPmwSEt"


def watch_drive_folder(interval: int = 60) -> None:
    """Watch the Google Drive folder for changes and sync new files."""
    service = get_drive_service()
    page_token = service.changes().getStartPageToken().execute()["startPageToken"]
    while True:
        response = service.changes().list(
            pageToken=page_token,
            spaces="drive",
            fields="nextPageToken, newStartPageToken, changes(fileId, removed, file(id, name, mimeType, parents))",
        ).execute()
        for change in response.get("changes", []):
            file = change.get("file")
            if file and not change.get("removed") and FOLDER_ID in file.get("parents", []):
                print(f"Detected change in: {file['name']}")
                files = sync_drive_files()
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

