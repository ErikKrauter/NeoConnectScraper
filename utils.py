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

gsheet_client, _ = initialize_services("credentials.json")

destination_sheet = gsheet_client.open_by_key(DESTINATION_SHEET_ID)
DESTINATION_SHEET_TABLE_HEADERS = destination_sheet.sheet1.row_values(1)

source_sheet = gsheet_client.open_by_key(SOURCE_SHEET_ID)
SOURCE_SHEET_TABLE_HEADERS = source_sheet.sheet1.row_values(1)

# Map headers to column indices
COLUMN_MAPPING_DESTINATION = {
    'Kürzel': DESTINATION_SHEET_TABLE_HEADERS.index(' '),  # doctor_office
    'Patient': DESTINATION_SHEET_TABLE_HEADERS.index('Pat ID'),  # doctor_office
    'Auftrag': DESTINATION_SHEET_TABLE_HEADERS.index('Auftrag'),  # product
    'Details': DESTINATION_SHEET_TABLE_HEADERS.index('Details'),  # tooth_number
    'Eingang': DESTINATION_SHEET_TABLE_HEADERS.index('Eingang'),  # scan_date
    'Einsetztermin': DESTINATION_SHEET_TABLE_HEADERS.index('Einsetztermin'),
    'Auftragsnummer': DESTINATION_SHEET_TABLE_HEADERS.index('Auftragsnummer'), # order_number
    'Nachricht': DESTINATION_SHEET_TABLE_HEADERS.index('Nachricht'),  # remarks
    'Anhänge': DESTINATION_SHEET_TABLE_HEADERS.index('Anhänge'), # link_to_folder
}


# Map headers to column indices
COLUMN_MAPPING_SOURCE = {
    'Eingang': SOURCE_SHEET_TABLE_HEADERS.index('Zeitstempel'),
    'Patient': SOURCE_SHEET_TABLE_HEADERS.index('Patientennummer'),
    'Auftrag': SOURCE_SHEET_TABLE_HEADERS.index('Produkttyp'),
    'VP_Details1': SOURCE_SHEET_TABLE_HEADERS.index('Extraktionsmethode'),
    'VP_Details2': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer'),
    'VP2_Details1': SOURCE_SHEET_TABLE_HEADERS.index('Extraktionsmethode (Verbandplatte 2)'),
    'VP2_Details2': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer (Verbandplatte 2)'),
    'BS_Details': SOURCE_SHEET_TABLE_HEADERS.index('Welche Implantate sind geplant?'),
    'BS2_Details': SOURCE_SHEET_TABLE_HEADERS.index('Welche Implantate sind geplant? (Bohrschablone 2)'),
    'K_Details': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer mit Zahnfarbe (Krone)'),
    'TK_Details': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer mit Zahnfarbe (Teilkrone)'),
    'V_Details': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer mit Zahnfarbe (Veneer)'),
    'B_Details': SOURCE_SHEET_TABLE_HEADERS.index('Zahnnummer mit Zahnfarbe (Brücke)'),
    'S_Details1': SOURCE_SHEET_TABLE_HEADERS.index('Kiefer'),
    'S_Details2': SOURCE_SHEET_TABLE_HEADERS.index('Schienentyp '),
    'S2_Details1': SOURCE_SHEET_TABLE_HEADERS.index('Kiefer (Schiene 2)'),
    'S2_Details2': SOURCE_SHEET_TABLE_HEADERS.index('Schienentyp (Schiene 2)'),
    'Nachricht': SOURCE_SHEET_TABLE_HEADERS.index('Weitere Bemerkungen'),
    'Eingeliederung': SOURCE_SHEET_TABLE_HEADERS.index('Wann wird die Arbeit eingegliedert?'),
    'Link': SOURCE_SHEET_TABLE_HEADERS.index('Bitte die Falldatei hochladen'),
    'Übertragen': SOURCE_SHEET_TABLE_HEADERS.index('transferred?'),
}
