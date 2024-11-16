from enum import Enum

# Ids of google sheets
original_sheet_id = "1U754gABJNVSj4j-pyQ2C-YIWPCXGSEpPoofp1GAs1IQ"
backup_sheet_id = "1pThfMBh_yRXYSuXag7cEPiSvAl8CpNuIhc5sZi5x7II"
DESTINATION_SHEET_ID = original_sheet_id
SOURCE_SHEET_ID = "1dwRGpB-uDG7MTg_NZkEKl6HfCW0Ao9NbXNrsv-3v48M"

# ids for google drive directories
original_folder =  "13BliX0dUGYjnSTeBLD1kV5tkKQtnPjFC" 
test_folder = "1r6IwzFcXUfLQzS6NheFgk1RWAqOxwaro"
BASE_FOLDER_ID = original_folder


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive']
NEOSS_LINK = "https://neoss.allied-star.com/"
ORDER_MANAGEMETN_LINK = "https://neoss.allied-star.com/order-management/order-management"
EMAIL = "nexam.ug@gmail.com"
PASSWORD = "?&VZsX~d;:UKF'2"
DOCTORS_OFFICES = { 
                    "Anne Szablowski, Dr. Alexander von Horn": "EB",
                    "Laureen Brandt": "LB",
                    "Anne Szablowski": "EB"
                }

class Products(Enum):
    SCHIENE = "Schiene"
    KRONE = "Krone"
    BRUECKE = "Brücke"
    VENEER = "Veneer"
    VERBANDPLATTE = "Verbandplatte"