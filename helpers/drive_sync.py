from helpers.drive_browser import list_excel_files_in_folder, download_file

FOLDER_ID = "1-1b9zryLrFrS3yJVrmSQ0UlcwoPmwSEt"

def sync_drive_files():
    files = list_excel_files_in_folder(FOLDER_ID)
    local_files = []
    for f in files:
        local_path = f"data/{f['name']}"
        download_file(f['id'], local_path)
        local_files.append(local_path)
    return local_files
