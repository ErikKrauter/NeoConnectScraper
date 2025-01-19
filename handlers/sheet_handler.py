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
        # Prepare the row data as a list of empty values
        row_data = [''] * len(DESTINATION_SHEET_TABLE_HEADERS)  # Length matches the number of columns in the sheet

        # Map data to columns dynamically using COLUMN_MAPPING_DESTINATION
        row_data[COLUMN_MAPPING_DESTINATION['Kürzel']] = order_info.doctors_office
        row_data[COLUMN_MAPPING_DESTINATION['Patient']] = order_info.patient_number
        row_data[COLUMN_MAPPING_DESTINATION['Auftrag']] = order_info.product
        row_data[COLUMN_MAPPING_DESTINATION['Details']] = order_info.details
        row_data[COLUMN_MAPPING_DESTINATION['Eingang']] = order_info.scan_date.strftime("%d.%m.%Y")
        row_data[COLUMN_MAPPING_DESTINATION['Einsetztermin']] = order_info.delivery_date.strftime("%d.%m.%Y")
        row_data[COLUMN_MAPPING_DESTINATION['Auftragsnummer']] = order_info.order_number
        row_data[COLUMN_MAPPING_DESTINATION['Nachricht']] = order_info.remarks
        row_data[COLUMN_MAPPING_DESTINATION['Anhänge']] = order_info.link_to_folder

        # Get the next available row
        last_row = len(self.destination_sheet.get_all_values()) + 1

        # Update the entire row in the sheet
        range_address = f"A{last_row}:S{last_row}"  # Adjust range based on your sheet
        self.destination_sheet.update(range_address, [row_data], value_input_option="USER_ENTERED")


    def download(self) -> list[list[str]]:
        # Download all rows but exclude empty rows        
        return [row for row in self.source_sheet.get_all_values() if any(row)]

    
    def update_cell(self, row: int, col: int, value: str):
        self.source_sheet.update_cell(row, col, value)