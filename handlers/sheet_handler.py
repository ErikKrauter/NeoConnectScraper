from order_info import OrderInfo
from constants import DESTINATION_SHEET_ID, SOURCE_SHEET_ID
from utils import COLUMN_MAPPING, DESTINATION_SHEET_TABLE_HEADERS
# class responsible for communication with google sheet

class GSheetHandler:
        
    def __init__(self, client):
        self.sheet_client = client
        self.destination_sheet = client.open_by_key(DESTINATION_SHEET_ID)
        self.source_sheet = client.open_by_key(SOURCE_SHEET_ID) 

    def upload(self, order_info: OrderInfo):
        # Prepare the row with empty values for columns not used
        row_data = [''] * len(DESTINATION_SHEET_TABLE_HEADERS)
        
        # Fill in the specific columns based on your mapping
        row_data[COLUMN_MAPPING['Kürzel']] = order_info.doctors_office
        row_data[COLUMN_MAPPING['Patient']] = order_info.patient_number
        row_data[COLUMN_MAPPING['Auftrag']] = order_info.product
        row_data[COLUMN_MAPPING['Details']] = order_info.details
        row_data[COLUMN_MAPPING['Eingang']] = order_info.scan_date
        row_data[COLUMN_MAPPING['Auftragsnummer']] = order_info.order_number
        row_data[COLUMN_MAPPING['Nachricht']] = order_info.remarks
        row_data[COLUMN_MAPPING['Anhänge']] = order_info.link_to_folder
        
        # Append the row to the sheet
        self.destination_sheet.sheet1.append_row(row_data)
        print(f"Order Info {order_info.order_number} uploaded to Google Sheet \n")

    def download(self):
        pass