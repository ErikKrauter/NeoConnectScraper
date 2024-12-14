from enum import Enum
from dotenv import load_dotenv
import os

# Load the .env file
# it contains the password and email
load_dotenv()

# Access some private variables from env file
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
EB = os.getenv("EB")
LB = os.getenv("EB")

# Ids of google sheets
original_sheet_id = "1U754gABJNVSj4j-pyQ2C-YIWPCXGSEpPoofp1GAs1IQ"
# for testing and development
backup_sheet_id = "1pThfMBh_yRXYSuXag7cEPiSvAl8CpNuIhc5sZi5x7II"
DESTINATION_SHEET_ID = original_sheet_id # original_sheet_id
SOURCE_SHEET_ID = "1dwRGpB-uDG7MTg_NZkEKl6HfCW0Ao9NbXNrsv-3v48M"

# ids for google drive directories
original_folder =  "13BliX0dUGYjnSTeBLD1kV5tkKQtnPjFC"
# for testing and development
test_folder = "1r6IwzFcXUfLQzS6NheFgk1RWAqOxwaro"
BASE_FOLDER_ID = original_folder


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive']
NEOSS_LINK = "https://neoss.allied-star.com/"
ORDER_MANAGEMETN_LINK = "https://neoss.allied-star.com/order-management/order-management"
DOCTORS_OFFICES = { 
                    EB: "EB",
                    LB: "LB",
                    "": "DG"
                }

# Products.BRUECKE.abbrev() = B
class Products(str, Enum):
    SCHIENE = "Schiene"
    KRONE = "Krone"
    TEILKRONE = "Teilkrone"
    BRUECKE = "Brücke"
    VENEER = "Veneer"
    VERBANDPLATTE = "Verbandplatte"
    BOHRSCHABLONE = "Bohrschablone"

    def abbrev(self):
        abbreviations = {
            "Schiene": "HSchiene",
            "Krone": "K",
            "Teilkrone": "TK",
            "Brücke": "B",
            "Veneer": "V",
            "Verbandplatte": "VP",
            "Bohrschablone": "BS",
        }
        return abbreviations[self.value]

