from constants import DOCTORS_OFFICES, Products
import re


# Define a class to hold the order information
# we use OrderInfo to populate the destinatin google sheet (Druckaufträge)
class OrderInfo:
    def __init__(self, order_number: str, doctor_name: str, scan_time: str, remarks: str = "", tooth_number: str = "", patient_number: str = ""):
        self.order_number = order_number
        self.doctors_office = DOCTORS_OFFICES[doctor_name]
        self.scan_date = self._convert_time_stamp_to_date(scan_time)
        # to make sure the remark is a single line w/o line breaks
        self.remarks = remarks.replace('\n', ' ')
        self.tooth_number = tooth_number # if multiple number seperate by comma w/o blanks
        self.product = ""
        self.details = ""
        self.patient_number = patient_number
        self._has_multiple_products = False
        if self.remarks:
            self._parse_remarks()
        # 08.11.24 --> 24.11.08
        self.reverse_scan_date = ".".join(self.scan_date.split(".")[::-1])
        self.link_to_folder = None

    def _convert_time_stamp_to_date(self, time_stamp: str):
        if "-" in time_stamp:
            # this is the format that comes from NEOSS
            # 2024-11-08 09:46:50 --> 08.11.24
            date = time_stamp[:10]
            date_list = date.split("-")
            # 2024 -> 24
            date_list[0] = date_list[0][2:]
            reversed_date_list = date_list[::-1]
            out_date_list = reversed_date_list
        elif "." in time_stamp:
            # thats the format coming from Fallupload
            # 17.11.2024 16:17:14 --> 17.11.24
            date = time_stamp[:10]
            date_list = date.split(".")
            date_list[-1] = date_list[-1][2:]
            out_date_list = date_list
        return ".".join(out_date_list)
        
    def _write_to_product(self, string: str):
        self.product += string if self.product == "" else f" + {string}" 

    def _extract_patient_number(self):
        if self.patient_number != "": return
        # Define regex pattern for variations of patient number
        # Match variations like 'pat', 'Pat.', 'Pat Nr.', 'Patientennummer', followed by a number
        pattern = r'\b(?:pat(?:ientennummer)?(?:\.|\s*Nr\.|\s*nummer|nr)?\s*[.:]?\s*)(\d{2,})'
        match = re.search(pattern, self.remarks, re.IGNORECASE)
        self.patient_number = match.group(1) if match else "?"

    def _extract_details(self):
        
        details = []
        lower_remarks = self.remarks.lower()
        if self._has_multiple_products:
            details.append("multiple")

        try:
            # K, B, HSchien, TK, V
            if Products.KRONE in self.product:
                if re.search(r'\bteilkrone\b|\btk\b', lower_remarks):
                    details.append("TK")
                if re.search(r'\bkrone\b', lower_remarks) or re.search(r'\bkeramikkrone\b', lower_remarks):
                    details.append("K")
            if Products.BRUECKE in self.product:
                details.append("B")
            if Products.SCHIENE in self.product:
                details.append("HSchiene")
            if Products.VENEER in self.product:
                details.append("V")
            if Products.VERBANDPLATTE in self.product:
                details.append("VB")

            # Check for UK and OK
            has_uk = bool(re.search(r'\buk\b|unterkiefer', lower_remarks))
            has_ok = bool(re.search(r'\bok\b|oberkiefer', lower_remarks))
            
            if has_uk and has_ok:
                details.append("OK+UK")
            elif has_uk:
                details.append("UK")
            elif has_ok:
                details.append("OK")
            
            # can be ? which is fine, because that means they didnt input the
            # tooth number in the correct part of the details form
            details.append(self.tooth_number)

            tooth_colors = re.findall(r'\b(A[1-4](?:\.5|,5)?|B[1-4]|C[1-4]|D[2-4])\b', self.remarks)
            details.extend(tooth_colors)

            details_str = ' '.join(details).strip()
            self.details = details_str if details_str else "?"
        except Exception as e:
            print(f"Error constructing details: {e}")
            self.details = "?"  
    
    def _parse_remarks(self):
        # 2024-11-08 09:46:50
        remarks = self.remarks.lower()
        for product in Products:
            if product.lower() in remarks:
                self._write_to_product(product)
        self._has_multiple_products = "+" in self.product
        
        self._extract_patient_number()
        self._extract_details()
        
    def __repr__(self):
        return f"OrderInfo(order_number='{self.order_number}', doctor_office='{self.doctors_office}', scan_time='{self.scan_date}', product='{self.product}', tooth_number='{self.tooth_number}', remarks='{self.remarks}')"
