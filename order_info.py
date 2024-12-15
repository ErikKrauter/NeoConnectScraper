from constants import DOCTORS_OFFICES, Products
import re
import datetime


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
            self._parse_remarks()
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
            month, day, year = date.split(".")
        
        month = month if len(month)==2 else f"0{month}"
        day = day if len(day)==2 else f"0{day}"
        # 2024 -> 24
        year = year[2:]
        out_date_list = [day, month, year]
        return ".".join(out_date_list)
        
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

    def _parse_remarks(self):
        # 2024-11-08 09:46:50
        remarks = self.remarks.lower()
        for product in Products:
            if product == Products.TEILKRONE:
                continue
            elif product.lower() in remarks:
                self._write_to_product(product)
        self._has_multiple_products = "+" in self.product
        
        if self.patient_number == "":
            self._extract_patient_number()
        if self.tooth_number == "":
            self._extract_tooth_numbers()
        self._extract_details()
        
    def __repr__(self):
        return f"OrderInfo(order_number='{self.order_number}', doctor_office='{self.doctors_office}', scan_date='{self.scan_date}', delivery_date='{self.delivery_date}', product='{self.product}', tooth_number='{self.tooth_number}', remarks='{self.remarks}')"
