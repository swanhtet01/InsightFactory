import os
from helpers.drive_browser import list_files_in_folder, download_file

FOLDER_ID = "1-1b9zryLrFrS3yJVrmSQ0UlcwoPmwSEt"

EXCEL_MIME_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
]
IMAGE_MIME_TYPES = [
    "image/png",
]

DOCUMENT_MIME_TYPES = [
    "application/pdf",
    "text/plain",
]


def sync_drive_files():
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/documents", exist_ok=True)
    files = list_files_in_folder(
        FOLDER_ID, EXCEL_MIME_TYPES + IMAGE_MIME_TYPES + DOCUMENT_MIME_TYPES
    )
    local_files = []
    for f in files:
        mime = f.get("mimeType", "")
        if mime in EXCEL_MIME_TYPES:
            local_path = os.path.join("data", f["name"])
        elif mime in IMAGE_MIME_TYPES:
            local_path = os.path.join("data/images", f["name"])
        elif mime in DOCUMENT_MIME_TYPES:
            local_path = os.path.join("data/documents", f["name"])
        else:
            continue
        download_file(f["id"], local_path)
        local_files.append(local_path)
    return local_files
