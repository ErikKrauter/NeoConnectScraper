import os
import zipfile
from googleapiclient.http import MediaFileUpload
from order_info import OrderInfo
from constants import BASE_FOLDER_ID

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
        folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        return folder['id']

    # Define function to handle .zip file extraction and upload of .ply files
    def _upload_ply_files(self, folder_id: str, zip_file_path: str):
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            extracted_folder_path = zip_file_path.replace("_ply.zip", "")
            zip_ref.extractall(extracted_folder_path)  # Extract ZIP

            # Locate and upload each .ply file
            for root, _, files in os.walk(extracted_folder_path):
                print(f"root: {root}, files: {files}")
                for file in files:
                    print(f"file: {file}")
                    if file.endswith('.ply'):
                        file_path = os.path.join(root, file)
                        file_name = os.path.basename(file_path)
                        file_metadata = {
                            'name': file_name,
                            'parents': [folder_id]
                        }
                        media = MediaFileUpload(file_path, resumable=True)
                        google_drive_file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                        print(f'Uploaded file {file_name} with ID: {google_drive_file.get("id")}')

    # uplaod files to destination drive folder
    def upload(self, order_info: OrderInfo) -> str:
        # Generate the main folder name
        suffix = order_info.patient_number if order_info.patient_number != "?" else order_info.order_number
        main_folder_name = f"{order_info.doctors_office}{suffix}"
        
        # Find or create the main patient folder
        main_folder_id = self._find_or_create_folder(BASE_FOLDER_ID, main_folder_name)
        
        # Generate the subfolder name
        subfolder_name = f"{order_info.reverse_scan_date.replace('.', '_')}_{order_info.details.replace(' ', '_')}"
        subfolder_id = self._find_or_create_folder(main_folder_id, subfolder_name)
        
        # Locate the .zip file
        zip_file_path = os.path.expanduser(f"~/Downloads/{order_info.order_number}_ply.zip")
        if os.path.exists(zip_file_path):
            self._upload_ply_files(subfolder_id, zip_file_path)
        else:
            print(f"Zip file not found: {zip_file_path}")
        
        return f"https://drive.google.com/drive/folders/{subfolder_id}"

    # download files from folder_id
    # returns name of downloaded folder later handling
    def download(self, folder_id: str) -> str:
        pass