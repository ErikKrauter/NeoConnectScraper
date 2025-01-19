from constants import DOCTORS_OFFICES, Products
import re
from openai import OpenAI
from datetime import datetime
from constants import OPENAI_KEY

client = OpenAI(
  api_key=OPENAI_KEY
)

# Define a class to hold the order information
# we use OrderInfo to populate the destinatin google sheet (Druckaufträge)
class OrderInfo:
    def __init__(self, order_number: str,
                  doctor_name: str, 
                  scan_time: str, 
                  delivery_date: str, 
                  remarks: str = "", 
                  tooth_number: str = "", 
                  patient_number: str = "", 
                  case_name: str = ""):
        
        self.order_number = order_number
        self.doctors_office = DOCTORS_OFFICES.get(doctor_name, "Unknown")  # Default to "Unknown" if not found
        self.scan_date = self._convert_time_stamp_to_date(scan_time)
        self.delivery_date = self._convert_time_stamp_to_date(delivery_date)
        # to make sure the remark is a single line w/o line breaks
        # encode/decode using utf-8 for cross-plattform robustness
        self.remarks = remarks.replace('\r\n', '\n').replace('\n', ' ').encode('utf-8').decode('utf-8') if isinstance(remarks, str) else remarks
        self.tooth_number = tooth_number # if multiple number seperate by comma w/o blanks
        self.product = ""
        self.details = ""
        self.patient_number = patient_number
        self._has_multiple_products = False
        if self.remarks:
            self._parse_remarks_with_openai()
        # 08.11.24 --> 24.11.08
        self.reverse_scan_date = "_".join(self.scan_date.split(".")[::-1])
        self.link_to_folder = None
        self.case_name = case_name 
    
    # convert to dd.mm.yy
    def _convert_time_stamp_to_date(self, time_stamp: str):
        if "/" in time_stamp:
            # this is the format that comes from NEOSS (new)
            # Format: 12/10/2024, 4:38 PM
            # Convert to: 10.12.24
            date = time_stamp.split(",")[0]
            month, day, year = date.split("/")
            month = month if len(month)==2 else f"0{month}"
        elif "-" in time_stamp:
            # this is the format that comes from NEOSS (old)
            # 2024-11-08 09:46:50 --> 08.11.24
            date = time_stamp[:10]
            month, day, year  = date.split("-")
        elif "." in time_stamp:
            # thats the format coming from Fallupload
            # 17.11.2024 16:17:14 --> 17.11.24
            date = time_stamp[:10]
            day, month, year = date.split(".")
        
        month = month if len(month)==2 else f"0{month}"
        day = day if len(day)==2 else f"0{day}"
        # 2024 -> 24
        year = year[2:]
        out_date_list = [day, month, year]
        out_date_string = ".".joint(out_date_list)
        return datetime.strptime(out_date_string, "%d.%m.%y") 
        
    def _write_to_product(self, string: str):
        self.product += string if self.product == "" else f" + {string}" 

    def _extract_patient_number(self):
        # Define regex pattern for variations of patient number
        # Match variations like 'pat', 'Pat.', 'Pat Nr.', 'Patientennummer', followed by a number
        text = self.remarks.lower()

        # Define regex patterns for different variants
        patterns = [
            (r"patientennummer\s*:?\s*(\d+)", 1),            # Variant 1
            (r"pat\.?\s*nummer\s*:?\s*(\d+)", 1),            # Variant 2
            (r"patienten-nummer\s*:?\s*(\d+)", 1),           # Variant 3
            (r"patienten\s*nmr\s*:?(\d+)", 1),               # Variant 4
            (r"pat\.?\s*(nummer|nmr|nr)\.?\s*:?(\d+)", 2),   # Variant 5
            (r"patient\s*(nummer|nmr|nr)\s*:?(\d+)", 2),     # Variant 6
            (r"pat\.?\s*nr\.?\s*:\s*(\d+)", 1),              # Variant 7
            (r"pat\.?\s*:?(\d+)", 1),                        # Variant 8
            (r"pat\s+(\d+)", 1),                             # Variant 9
            (r"pat\.?\s*(\d+),?", 1),                        # Variant 10
        ]

        # Test each pattern
        for pattern, group_index in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.patient_number = match.group(group_index)
                return
        self.patient_number = "?"

    def _append_UK_OK(self, remark, details):

            # Check for UK and OK
            has_uk = bool(re.search(r'\buk\b|unterkiefer', remark))
            has_ok = bool(re.search(r'\bok\b|oberkiefer', remark))
            
            if has_uk and has_ok:
                details.append("OK+UK")
            elif has_uk:
                details.append("UK")
            elif has_ok:
                details.append("OK")

    def _extract_details(self):
        
        details = []
        lower_remarks = self.remarks.lower()

        try:
            # K, B, HSchien, TK, V
            for product in Products:
                if product in self.product:
                    if product == Products.KRONE:
                        if re.search(r'\bteilkrone\b|\btk\b', lower_remarks):
                            details.append(Products.TEILKRONE.abbrev())
                        else:
                            details.append(Products.KRONE.abbrev())
                    else:
                        details.append(product.abbrev())
                        if product == Products.SCHIENE:
                            self._append_UK_OK(lower_remarks, details)
            
            details.append(self.tooth_number)
            tooth_colors = re.findall(r'\b(A[1-4](?:\.5|,5)?|B[1-4]|C[1-4]|D[2-4])\b', self.remarks)
            details.extend(tooth_colors)
            details_str = ' '.join(details).strip()
            self.details = details_str if details_str else "?"
        except Exception as e:
            print(f"Error constructing details: {e}")
            self.details = "?"  
    
    def _extract_tooth_numbers(self):
        text = self.remarks.lower()
        # Patterns for specific cases
        patterns = {
            "dash": r"\b\d{2}-\d{2}\b",          # Tooth numbers with dashes
            "plus": r"\b\d{2}\+\d{2}\b",         # Tooth numbers with plus
            "comma": r"\b\d{2}(,\d{2})+\b",      # Tooth numbers with commas
            "neu": r"\b\d{2}\s*neu\b",           # Tooth numbers with "neu"
            "standalone": r"\b\d{2}\b"           # Standalone two-digit tooth numbers
        }

        results = []

        for label, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                if label == "plus":
                    # Replace "+" with space for "plus" pattern
                    match = match.replace("+", " ")
                elif label == "comma":
                    # Replace "," with space for "comma" pattern
                    match = match.replace(",", " ")
                results.append(match)

        self.tooth_number = " ".join(results) if len(results) else "?"

    def _extract_product(self):
        remarks = self.remarks.lower()
        for product in Products:
            if product == Products.TEILKRONE:
                continue
            elif product.lower() in remarks:
                self._write_to_product(product)
        self._has_multiple_products = "+" in self.product

    def _parse_remarks(self):
        self._extract_product()
        if self.patient_number == "":
            self._extract_patient_number()
        if self.tooth_number == "":
            self._extract_tooth_numbers()
        self._extract_details()

    def _parse_remarks_with_openai(self):
        self._extract_product()
        try:
            response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a dental lab assistant AI. Your task is to extract the patient number from a given text. "
                                    "The patient number is a numerical identifier present in the input text. "
                                    "Always return only the patient number without any additional text. "
                                    "If no patient number is found in the text, return '?' (a question mark)."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Extract the patient number from the following text. Your response must only contain the patient number, or '?' if no patient number is found. "
                                    "Here are some examples of inputs and outputs:\n"
                                    "- Input: '1264 Schiene Uk bis 6.1' Output: 1264\n"
                                    "- Input: 'Pat:2040 Bitte um die Kronen 36, 37 Zahnfarbe: A3,5 Fertigstellungsdatum: folgt mit dem Scan am Freitag für 11+12' Output: 2040\n"
                                    "- Input: 'Pat 402 Bitte 37 Keramik Teilkrone Zahnfarbe: A3' Output: 402\n"
                                    "- Input: 'Bitte um Herstellung Teilkrone 16 Zahnfarbe : A3,5 Pat. Nr.: 1457 Fertigstellungsdatum: 21.11.' Output: 1457\n"
                                    "- Input: 'Bitte Herstellung Teilkrone 36+37 Zahnfarbe: A3 Patienten Nr.: 133' Output: 133\n"
                                    "- Input: 'Bitte Hersetllung Krone 37 A3 Pat. Nummer. : 1543' Output: 1543\n"
                                    "- Input: 'Bitte Herstellung Keramikkrone Zahnfarbe: A3' Output: ?\n"
                                    "- Input: 'Schiene UK bis morgen' Output: ?\n\n"
                                    f"This is the input: {self.remarks}"
                                ),
                            },
                        ]
                    )

            parsed_data = response.choices[0].message.content
            self.patient_number = parsed_data.strip()
            # print("open ai found patient number: ", self.patient_number)

        except Exception as e:
            print(f"Failed to parse patient number with OpenAI: {e}")
            self.patient_number = "?"
        try:
            response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a dental lab assistant AI. Your task is to extract a standardized short hand notation from a given order. "
                                    "The input is an order that specifies what the lab shall manufacture. "
                                    "The output contains the relevant iformation in a standardized short hand form. "
                                    "If you cannot construct a valid output, you must output a question mark (?)."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Extract the order details from the following order."
                                    "Here are some examples of inputs and outputs:\n"
                                    "- Input: 'Bitte Herstellung von Brücke 26,25, 24 Anhänger Zahnfarbe: A3,5' Output: B 24-26 A3,5\n"
                                    "- Input: 'Bitte Herstellung 12 Keramikkrone Zahnfarbe siehe Bild (A3,5)' Output: K 12 A3,5\n"
                                    "- Input: 'UK Brücke OK folgt, Kontrolle mit der Einschubrichtung, A3,5 aber weiße Inzisalkante' Output: B UK A3,5\n"
                                    "- Input: 'Harte Schiene OK, Z.n. Frontzahntrauma 11' Output: HSchiene OK\n"
                                    "- Input: 'Keramikkronen 16,37 Zahnfarbe A3 Fertigstellung: 29.11. 09:00' Output: K 16+37 A3,5\n"
                                    "- Input: 'Bitte Herstellung UK adj. Schiene' Output: HSchiene adj. UK\n"
                                    "- Input: 'Farbe A3 Teilkrone an 14,15,26' Output: TK 14+15+26 A3\n"
                                    "- Input: 'Bitte Herstellung Krone 17, TK 16 + 46 A3' Output: K 17 A3 TK 16+46 A3\n"
                                    "- Input: 'Bitte Herstellung 27 Keramiktable Top + 44-47 Keramikbrücke Zahnfarbe: C4' Output: B 44-47 TK 27 C4\n"
                                    "- Input: 'Bitte Herstellung 15 Teilkrone,16,17 Kronen' Output: TK 15 K 16+17 A3,5\n"
                                    "- Input: 'Bitte um Herstellung Teilkrone 16 Zahnfarbe : A3,5 Pat. Nr.: 1457 Fertigstellungsdatum: 21.11.' Output: TK 16 A3,5\n"
                                    "- Input: 'Bitte Hersetllung Krone 37 A3 Pat. Nummer. : 1543' Output: K 37 A3\n"
                                    "- Input: 'Bitte um Herstellung : 15,16, 36,37 Krone und 26-28 Brücke Zahnfarbe: A3 Brücke noch nicht gepräpt, BItte zunächst Präps sichten.' Output: K 15+16+36+37 B 26-28 A3\n"
                                    
                                    f"This is the input: {self.remarks}"
                                ),
                            },
                        ]
                    )

            parsed_data = response.choices[0].message.content
            self.details = parsed_data.strip()
            # print("open ai parsed details: ", self.details)

        except Exception as e:
            print(f"Failed to parse details with OpenAI: {e}")
            self.details = "?"
        
    def __repr__(self):
        return f"order number:\t{self.order_number}\ndoctor office:\t{self.doctors_office}\ndoctors remarks:\t{self.remarks}\ncase name:\t{self.case_name}\npatient number:\t{self.patient_number}\nscan date:\t{self.scan_date}\ndelivery date:\t{self.delivery_date}\nproduct:\t{self.product}\ntooth number:\t{self.tooth_number}\ndetails:\t{self.details}\n"
