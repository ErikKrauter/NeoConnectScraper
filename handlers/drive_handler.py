import os
import zipfile
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from order_info import OrderInfo
from constants import BASE_FOLDER_ID
import platform

# this class handles communication with google drive

class GDriveHandler:

    def __init__(self, client):
        self.drive_client = client

    def _find_or_create_folder(self, parent_folder_id: str, folder_name: str) -> str:
        # Check if folder already exists
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        response = self.drive_client.files().list(q=query, spaces='drive').execute()

        files = response.get('files', [])
        if files:
            return files[0]['id']  # Folder exists, return its ID

        # Folder doesn't exist; create it
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        file_metadata['parents'] = [parent_folder_id]
        folder = self.drive_client.files().create(body=file_metadata, fields='id').execute()
        return folder['id']

    # Define function to handle .zip file extraction and upload of .ply files
    def _upload_ply_files(self, folder_id: str, zip_file_path: str):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            extracted_folder_path = os.path.splitext(zip_file_path)[0]  # Remove .zip extension
            extracted_folder_path = extracted_folder_path.replace("_ply", "")
            zip_ref.extractall(extracted_folder_path)  # Extract ZIP

            # Locate and upload each .ply file
            for root, _, files in os.walk(extracted_folder_path):
                #print(f"root: {root}, files: {files}")
                for file in files:
                    #print(f"file: {file}")
                    if file.endswith('.ply') or file.endswith('.mtl') or file.endswith('.jpg'):
                        file_path = os.path.join(root, file)
                        file_name = os.path.basename(file_path)
                        file_metadata = {
                            'name': file_name,
                            'parents': [folder_id]
                        }
                        media = MediaFileUpload(file_path, resumable=True)
                        google_drive_file = self.drive_client.files().create(body=file_metadata, media_body=media, fields='id').execute()
                        #print(f'Uploaded file {file_name} with ID: {google_drive_file.get("id")}')

    # Upload files to destination drive folder
    def upload(self, order_info: OrderInfo, zip_file_path: str) -> str:
        # Generate the main folder name
        suffix = order_info.patient_number if order_info.patient_number != "?" else order_info.order_number
        main_folder_name = f"{order_info.doctors_office}{suffix}"

        # Replace any invalid characters for Windows file systems
        if platform.system() == "Windows":
            main_folder_name = main_folder_name.replace("<", "_").replace(">", "_").replace(":", "_")

        # Find or create the main patient folder
        main_folder_id = self._find_or_create_folder(BASE_FOLDER_ID, main_folder_name)

        # Generate the subfolder name
        subfolder_name = f"{order_info.reverse_scan_date}_{order_info.details.replace(' ', '_')}"
        if platform.system() == "Windows":
            subfolder_name = subfolder_name.replace("<", "_").replace(">", "_").replace(":", "_")

        subfolder_id = self._find_or_create_folder(main_folder_id, subfolder_name)

        if os.path.exists(zip_file_path):
            self._upload_ply_files(subfolder_id, zip_file_path)
        else:
            print(f"Zip file not found: {zip_file_path}")

        return f"https://drive.google.com/drive/folders/{subfolder_id}"

    def _extract_file_id(self, link: str) -> str:
        """Extracts the file ID from a Google Drive link."""
        if "," in link:
            link = link.split(",")[0]
        if "id=" in link:
            return link.split("id=")[1]
        elif "drive.google.com" in link:
            # Handles URLs in the format: https://drive.google.com/file/d/<id>/view
            return link.split("/d/")[1].split("/")[0]
        else:
            raise ValueError(f"Invalid Google Drive link: {link}")

    # Download files from folder_id
    # Returns name of downloaded folder for later handling
    def download(self, link: str) -> str:
        """Downloads a zip folder from Google Drive into ~/Downloads/"""

        folder_id = self._extract_file_id(link)
        # Define the download directory
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        # Get the file metadata
        file_metadata = self.drive_client.files().get(fileId=folder_id, fields="name, mimeType").execute()
        file_name = file_metadata.get("name")
        mime_type = file_metadata.get("mimeType")

        # Validate that the file is a zip file
        if mime_type != "application/zip" and not file_name.endswith(".zip"):
            raise ValueError(f"The file is not a zip file: {file_name} (Mime Type: {mime_type})")

        # Download the file
        request = self.drive_client.files().get_media(fileId=folder_id)
        local_zip_path = os.path.join(download_dir, file_name)

        with open(local_zip_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")

        print(f"File downloaded successfully: {local_zip_path}")
        return local_zip_path
