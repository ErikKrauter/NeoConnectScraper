from order_info import OrderInfo
from constants import DESTINATION_SHEET_ID, SOURCE_SHEET_ID
from utils import COLUMN_MAPPING_DESTINATION, DESTINATION_SHEET_TABLE_HEADERS
# class responsible for communication with google sheet

class GSheetHandler:
        
    def __init__(self, client):
        self.sheet_client = client
        self.destination_sheet = client.open_by_key(DESTINATION_SHEET_ID).sheet1
        self.source_sheet = client.open_by_key(SOURCE_SHEET_ID).sheet1

    def upload(self, order_info: OrderInfo):
        # Prepare the row with empty values for columns not used
        row_data = [''] * len(DESTINATION_SHEET_TABLE_HEADERS)
        
        # Fill in the specific columns based on your mapping
        row_data[COLUMN_MAPPING_DESTINATION['Kürzel']] = order_info.doctors_office
        row_data[COLUMN_MAPPING_DESTINATION['Patient']] = order_info.patient_number
        row_data[COLUMN_MAPPING_DESTINATION['Auftrag']] = order_info.product
        row_data[COLUMN_MAPPING_DESTINATION['Details']] = order_info.details
        row_data[COLUMN_MAPPING_DESTINATION['Eingang']] = order_info.scan_date
        row_data[COLUMN_MAPPING_DESTINATION['Auftragsnummer']] = order_info.order_number
        row_data[COLUMN_MAPPING_DESTINATION['Nachricht']] = order_info.remarks
        row_data[COLUMN_MAPPING_DESTINATION['Anhänge']] = order_info.link_to_folder

        # Append the row to the sheet
        self.destination_sheet.append_row(row_data)
        print(f"Order Info {order_info.order_number} uploaded to Google Sheet \n")

    def download(self) -> list[list[str]]:
        # Download all rows but exclude empty rows        
        return [row for row in self.source_sheet.get_all_values() if any(row)]

    
    def update_cell(self, row: int, col: int, value: str):
        self.source_sheet.update_cell(row, col, value)