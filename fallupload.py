from handlers import GSheetHandler, GDriveHandler
from utils import initialize_services, COLUMN_MAPPING_SOURCE, SOURCE_SHEET_TABLE_HEADERS
from order_info import OrderInfo
from typing import List
from constants import Products

def write_to_product(product: str, string: str) -> str:
    """Add a string to the product description."""
    return product + (string if product == "" else f"+{string}")


def clean_semicolons(input_str: str) -> str:
    """Remove semicolons and ensure consistent spacing."""
    split_list = input_str.split(";")
    cleaned_list = [item.strip() for item in split_list]
    return " ".join(cleaned_list)


def add_details(abbrev, details_list, row, *columns):
    """Helper to add details for a specific product type."""
    if any(row[column] for column in columns if column):
        details_list.append(f"{abbrev} " + " ".join(row[column] for column in columns if column))


def extract_order_info(row: list[str]) -> OrderInfo:
    scan_time = row[COLUMN_MAPPING_SOURCE["Eingang"]]
    doctor_name = ""  # Have no doctor's name; defaults to DG.
    patient_number = row[COLUMN_MAPPING_SOURCE["Patient"]]
    order_number = patient_number

    product = ""
    details_list = []
    processed_products = set()

    # Define mapping of product types to their columns
    product_details_mapping = [
        (Products.VERBANDPLATTE, [COLUMN_MAPPING_SOURCE["VP_Details1"], COLUMN_MAPPING_SOURCE["VP_Details2"]]),
        (Products.VERBANDPLATTE, [COLUMN_MAPPING_SOURCE["VP2_Details1"], COLUMN_MAPPING_SOURCE["VP2_Details2"]]),
        (Products.BOHRSCHABLONE, [COLUMN_MAPPING_SOURCE["BS_Details"]]),
        (Products.BOHRSCHABLONE, [COLUMN_MAPPING_SOURCE["BS2_Details"]]),
        (Products.KRONE, [COLUMN_MAPPING_SOURCE["K_Details"]]),
        (Products.TEILKRONE, [COLUMN_MAPPING_SOURCE["TK_Details"]]),
        (Products.VENEER, [COLUMN_MAPPING_SOURCE["V_Details"]]),
        (Products.BRUECKE, [COLUMN_MAPPING_SOURCE["B_Details"]]),
        (Products.SCHIENE, [COLUMN_MAPPING_SOURCE["S_Details1"], COLUMN_MAPPING_SOURCE["S_Details2"]]),
        (Products.SCHIENE, [COLUMN_MAPPING_SOURCE["S2_Details1"], COLUMN_MAPPING_SOURCE["S2_Details2"]]),
    ]

    # Process each product type and its details
    for product_type, columns in product_details_mapping:
        if any(row[column] for column in columns if column):
            # we make sure that product only contains a product once, even if we order the product twice
            if product_type not in processed_products:
                product = write_to_product(product, product_type)
                processed_products.add(product_type)
            # the details however contain the product details for each product even if we order same product twice
            add_details(product_type.abbrev(), details_list, row, *columns)

    # Join and clean details
    details = clean_semicolons(" ".join(details_list))

    # Create OrderInfo object
    order_info = OrderInfo(
        order_number=order_number,
        doctor_name=doctor_name,
        scan_time=scan_time,
        patient_number=patient_number
    )
    order_info.product = product
    order_info.remarks = row[COLUMN_MAPPING_SOURCE["Nachricht"]]
    order_info.details = details
    order_info.link_to_folder = row[COLUMN_MAPPING_SOURCE["Link"]]
    
    return order_info

def handle_orders():
    # first we download orders from source sheet
    # loop through rows
    # for every row that has not been transferred convert information into OrderInfo class and download files from source drive
    # then upload files to destination drive and get link to it
    # update OrderInfo with link
    # Once looped through all rows loop through the list of OrderInfo
    # upload every individual OrderInfo to destination sheet.
    gsheet_client, gdrive_client = initialize_services("credentials.json")
    gsheet_handler = GSheetHandler(client=gsheet_client)
    gdrive_handler = GDriveHandler(client=gdrive_client)
    order_info_list: List[OrderInfo] = []
    source_rows = gsheet_handler.download()

    folder_paths = []
    for index, row in enumerate(source_rows):
        if row[COLUMN_MAPPING_SOURCE["Übertragen"]]:
            continue
        order_info = extract_order_info(row)
        column_index = COLUMN_MAPPING_SOURCE["Übertragen"] + 1  # gsheet uses 1 based indexing
        gsheet_handler.update_cell(index+1, column_index, "yes")
        folder_path = gdrive_handler.download(order_info.link_to_folder)
        folder_paths.append(folder_path)
        order_info_list.append(order_info)
    
    if len(order_info_list) == 0:
        print("NO ORDERS")
        return
    
    for order_info, folder_path in zip(order_info_list, folder_paths):
        # this uploads to gdrive and returns the link to the gdrive folder
        order_info.link_to_folder = gdrive_handler.upload(order_info, folder_path)
        # this uploads the order_info to the gsheet
        gsheet_handler.upload(order_info)
        