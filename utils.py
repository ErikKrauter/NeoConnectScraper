# utils.py
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from constants import SCOPES, DESTINATION_SHEET_ID, SOURCE_SHEET_ID

def initialize_services(credentials_file):
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    gspread_client = gspread.authorize(creds)
    drive_service = build("drive", "v3", credentials=creds)
    return gspread_client, drive_service

gsheet_client, _ = initialize_services("credentials_gsheet.json")

destination_sheet = gsheet_client.open_by_key(DESTINATION_SHEET_ID)
DESTINATION_SHEET_TABLE_HEADERS = destination_sheet.sheet1.row_values(1)

source_sheet = gsheet_client.open_by_key(SOURCE_SHEET_ID)
SOURCE_SHEET_TABLE_HEADERS = source_sheet.sheet1.row_values(1)

# Map headers to column indices
COLUMN_MAPPING = {
    'Kürzel': DESTINATION_SHEET_TABLE_HEADERS.index(' '),  # doctor_office
    'Patient': DESTINATION_SHEET_TABLE_HEADERS.index('Pat ID'),  # doctor_office
    'Auftrag': DESTINATION_SHEET_TABLE_HEADERS.index('Auftrag'),  # product
    'Details': DESTINATION_SHEET_TABLE_HEADERS.index('Details'),  # tooth_number
    'Eingang': DESTINATION_SHEET_TABLE_HEADERS.index('Eingang'),  # scan_date
    'Auftragsnummer': DESTINATION_SHEET_TABLE_HEADERS.index('Auftragsnummer'), # order_number
    'Nachricht': DESTINATION_SHEET_TABLE_HEADERS.index('Nachricht'),  # remarks
    'Anhänge': DESTINATION_SHEET_TABLE_HEADERS.index('Anhänge'), # link_to_folder
}