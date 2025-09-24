from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from helpers.drive_browser import list_files_in_folder, download_file
from helpers.source_registry import record_sync_snapshot, slugify_label
from config import GOOGLE_DRIVE_FOLDER_IDS, resolve_drive_folder_label

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

def _target_directory(base: Path, category: str) -> Path:
    path = base / category
    path.mkdir(parents=True, exist_ok=True)
    return path


def _extract_last_modified(user: Dict | None) -> str | None:
    if not user or not isinstance(user, dict):
        return None
    return user.get("emailAddress") or user.get("displayName")


def sync_drive_files(folder_ids: Iterable[str] | None = None) -> List[str]:
    base_dir = Path("data")
    base_dir.mkdir(exist_ok=True)

    folder_ids = list(folder_ids or GOOGLE_DRIVE_FOLDER_IDS)
    local_files: List[str] = []
    metadata: List[Dict[str, Any]] = []

    for folder_id in folder_ids:
        label = resolve_drive_folder_label(folder_id)
        slug = slugify_label(label)
        folder_root = base_dir / slug
        spreadsheets_dir = _target_directory(folder_root, "spreadsheets")
        images_dir = _target_directory(folder_root, "images")
        documents_dir = _target_directory(folder_root, "documents")

        files = list_files_in_folder(
            folder_id, EXCEL_MIME_TYPES + IMAGE_MIME_TYPES + DOCUMENT_MIME_TYPES
        )
        for f in files:
            mime = f.get("mimeType", "")
            if mime in EXCEL_MIME_TYPES:
                dest_dir = spreadsheets_dir
            elif mime in IMAGE_MIME_TYPES:
                dest_dir = images_dir
            elif mime in DOCUMENT_MIME_TYPES:
                dest_dir = documents_dir
            else:
                continue

            dest_path = dest_dir / f["name"]
            download_file(f["id"], str(dest_path))
            local_files.append(str(dest_path))
            metadata.append(
                {
                    "folder_id": folder_id,
                    "folder_label": label,
                    "folder_slug": slug,
                    "file_id": f.get("id"),
                    "name": f.get("name"),
                    "mime_type": mime,
                    "local_path": str(dest_path),
                    "modified_time": f.get("modifiedTime"),
                    "owners": f.get("owners"),
                    "last_modified_by": _extract_last_modified(
                        f.get("lastModifyingUser")
                    ),
                }
            )

    record_sync_snapshot(metadata)
    return local_files
