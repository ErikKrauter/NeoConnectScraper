import helium
import platform
import os
import sys
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from typing import List

from constants import EMAIL, PASSWORD, NEOSS_LINK, ORDER_MANAGEMETN_LINK
from order_info import OrderInfo
from handlers import GDriveHandler
from handlers import GSheetHandler
from utils import initialize_services


# wait for element to be loaded on website
def wait_for_element(soup, html_type: str, class_name: str, max_attempts=10):
    attempts = 0
    while attempts < max_attempts:
        element = soup.find(html_type, {'class': class_name})
        if element:
            return element
        time.sleep(1)  # Wait a second before trying again
        attempts += 1
        soup = BeautifulSoup(helium.get_driver().page_source, 'html.parser')
    print(f"Failed to load element {html_type} of class {class_name}.")
    return None

def simple_login():
    helium.write(EMAIL, into="User Name")
    time.sleep(0.3)
    helium.write(PASSWORD, into="Password")
    # Define the WebDriver
    driver = helium.get_driver()
    
    # Wait until a post-login element appears
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-wrap"))
        )
        print("Login successful.")
    except TimeoutException:
        print("Time out: You have to solve the captcha and login within 120 seconds.")
        sys.exit()

def export_ply(driver):
    # Wait for the tools_wrap div to be present
    tools_wrap = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'tools_wrap'))
    )

    # Locate the Export button using its data-title attribute
    export_button = WebDriverWait(tools_wrap, 10).until(
        EC.element_to_be_clickable((By.XPATH, './/span[@data-title="Export"]'))
    )

    # Click the Export button
    export_button.click()
    time.sleep(1)

    dialogs = driver.find_elements(By.CLASS_NAME, 'el-dialog')
    export_dialog = None
    for dialog in dialogs:
        # Check if the dialog contains the specific content
        if "File save format" in dialog.get_attribute('outerHTML'):
            export_dialog = dialog
            break
    # Uncheck the STL checkbox
    stl_checkbox_label = export_dialog.find_element(By.XPATH, './/label[.//span[text()="STL"]]')
    # Check if the checkbox is checked
    is_checked = stl_checkbox_label.find_element(By.CLASS_NAME, 'el-checkbox__input').get_attribute('class')
    if 'is-checked' in is_checked:
        # Uncheck the checkbox
        stl_checkbox_label.click()
        print("STL checkbox unchecked.")

    # Toggle off the Prescription switch
    prescription_switch = export_dialog.find_element(By.XPATH, './/div[@role="switch"]')
    # Check if the switch is on
    is_prescription_on = prescription_switch.get_attribute('aria-checked')  # "true" or "false"
    if is_prescription_on == 'true':
        # Un-toggle the switch
        prescription_switch.click()
        print("Prescription switch toggled off.")

    # Click the Confirm button
    helium.click("Confirm")
    print("Confirm button clicked.")

    # Wait for the "Export Completed" text to be visible
    export_completed = WebDriverWait(driver, 120).until(
        EC.text_to_be_present_in_element(
            (By.CLASS_NAME, 'status_name'),  # Locator for the element
            'Export Completed'  # Text to wait for
        )
    )
    if export_completed:
        print("Export completed successfully.")

        # click the "OK" button to close the dialog
        helium.click("OK")
        print("OK button clicked.")
    else:
        print("export failed")

def construct_folder_name(order_info: OrderInfo):
    reversed_date = order_info.reverse_scan_date # 24_12_11
    reversed_date = f"20{reversed_date}".replace("_", "-")
    # 2024-12-12_Fall von Walter Ilka
    return f"{reversed_date}_{order_info.case_name}.zip"

def scrape_orders():

    gsheet_client, gdrive_client = initialize_services(os.path.abspath("credentials.json"))
    gsheet_handler = GSheetHandler(client=gsheet_client)
    gdrive_handler = GDriveHandler(client=gdrive_client)
    order_info_list: List[OrderInfo] = []

    options = Options()
    options.add_argument("--start-maximized")  # Start Chrome in full size window
    if platform.system() == "Windows":
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
    helium.start_chrome(NEOSS_LINK, options=options)
    helium.go_to(NEOSS_LINK)
    simple_login()
    # go to site with all orders
    helium.go_to(ORDER_MANAGEMETN_LINK)
    time.sleep(5)
    
    driver = helium.get_driver()
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find the table body
    table_body = wait_for_element(soup, 'div', 'el-table__body-wrapper')
    if table_body is None:
        print("Table not found. EXITING")
        sys.exit()

    rows = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.el-table__row'))
        )

    # Loop over each row in the table
    for index, row in enumerate(rows):
        WebDriverWait(driver, 10).until(
            lambda d: len(row.find_elements(By.TAG_NAME, 'td')) > 0
        )
        # Fetch the <td> elements
        td_elements = row.find_elements(By.TAG_NAME, 'td')

        # Access the last <td> element
        last_td = td_elements[-1]

        # Check if the row status is unassigned
        status_span = wait_for_element(last_td, 'span', 'text')
        status = status_span.get_text(strip=True)

        case_name_td = td_elements[1]

        name_span = wait_for_element(case_name_td, 'span', 'nowrap')
        case_text = name_span.get_text(strip=True)

        if status in ["Accepted", "Shipped", "Completed", "Ready", "Pending"]:
            print(f"Case: {case_text}")
            selenium_rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.el-table__row'))
            )
            selenium_row = selenium_rows[index]  # Find the row by index
            selenium_row.click() 
            time.sleep(2)
            # Parse the updated HTML for the side panel content
            side_panel_html = driver.page_source
            side_panel_soup = BeautifulSoup(side_panel_html, 'html.parser')

            table = wait_for_element(side_panel_soup, 'div', 'desc_list')
            list_items = table.find_all('div', class_='list_item')

            # Map variables to specific list items
            order_number = list_items[0].find('div', class_='value').find('span', class_='nowrap').text.strip()
            doctor_name = list_items[3].find('div', class_='value').find('span', class_='nowrap').text.strip()
            scan_time = list_items[5].find('div', class_='value').find('span', class_='nowrap').text.strip()
            requested_delivery_date = list_items[6].find('div', class_='value').find('span', class_='nowrap').text.strip()

            # Print the extracted values
            print(f"Order ID: {order_number}")
            print(f"Dentist Name: {doctor_name}")
            print(f"Order Date: {scan_time}")
            print(f"Requested Delivery Date: {requested_delivery_date} \n")

            # Wait for the memo_wrap to be visible
            memo_wrap = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'memo_wrap'))
            )

            # Locate the textarea inside the memo_wrap
            textarea = memo_wrap.find_element(By.CLASS_NAME, 'el-textarea__inner')

            # Get the value of the textarea
            memo_text = textarea.get_attribute('value')
            print(f"Memo: \n {memo_text} \n")

            order_info = OrderInfo(
                        order_number=order_number,
                        doctor_name=doctor_name,
                        scan_time=scan_time,
                        delivery_date=requested_delivery_date,
                        remarks=memo_text,
                        case_name=case_text
                    )

            order_info_list.append(order_info)

            export_ply(driver)

            # Wait for the back button to be visible and clickable
            back_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'arrow_left_btn'))
            )

            # Click the back button
            back_button.click()
            print("clicked back button. Proceeding with next order \n\n")

            time.sleep(3)

    if len(order_info_list) == 0:
        print("NO UNASSIGNED ORDERS")
        time.sleep(4)

    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    for order_info in order_info_list:
        # this uploads to gdrive and returns the link to the gdrive folder
        zip_file_path = os.path.join(download_dir, construct_folder_name(order_info))
        order_info.link_to_folder = gdrive_handler.upload(order_info, zip_file_path)
        # this uploads the order_info to the gsheet
        gsheet_handler.upload(order_info)

    try:
        helium.kill_browser()
    except Exception as e:
        print(f"Error closing browser: {e}")
    
