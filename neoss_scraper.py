import helium
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
    helium.write(EMAIL, into="Account/Phone Number/Email Address")
    time.sleep(0.3)
    helium.write(PASSWORD, into="Password")
    # Define the WebDriver
    driver = helium.get_driver()
    
    # Wait until a post-login element appears
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
        )
        print("Login successful.")
    except TimeoutException:
        print("Time out: You have to solve the captcha and login within 120 seconds.")
        exit()

def scrape_orders():

    gsheet_client, gdrive_client = initialize_services("credentials.json")
    gsheet_handler = GSheetHandler(client=gsheet_client)
    gdrive_handler = GDriveHandler(client=gdrive_client)
    order_info_list: List[OrderInfo] = []

    options = Options()
    options.add_argument("--start-maximized")  # Start Chrome in full size window
    helium.start_chrome(NEOSS_LINK, options=options)
    helium.go_to(NEOSS_LINK)
    simple_login()
    # go to site with all orders
    helium.go_to(ORDER_MANAGEMETN_LINK)
    
    driver = helium.get_driver()
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find the table body
    table_body = wait_for_element(soup, 'div', 'el-table__body-wrapper')
    if table_body is None:
        print("Table not found. EXITING")
        exit()
    rows = table_body.find_all('tr', {'class': 'el-table__row'})

    # Loop over each row in the table
    for _, row in enumerate(rows):

        # Check if the row status is unassigned
        status_cell = wait_for_element(row, 'td', 'el-table_1_column_6')
        status = status_cell.text.strip()
        
        if status in ["Assigned", "Completed"]:
            # Click the order number button to open the side panel
            order_number_button = wait_for_element(row, 'td', 'el-table_1_column_1')
            print(f"Processing order: {order_number_button.text.strip()} \n")
            helium.click(order_number_button.text.strip())
            time.sleep(2)
            # Parse the updated HTML for the side panel content
            side_panel_html = driver.page_source
            side_panel_soup = BeautifulSoup(side_panel_html, 'html.parser')

            container = wait_for_element(side_panel_soup, 'div', 'el-collapse edit-collapse')
            
            # Get the first collapsible item (Basic Information)
            basic_information_panel = container.find_all('div', class_='el-collapse-item')[0]
            basic_information = basic_information_panel.find('div', class_='el-collapse-item__wrap')

            # Get the second collapsible item (Order Details)
            order_details_panel = container.find_all('div', class_='el-collapse-item')[1]
            order_details = order_details_panel.find('div', class_='el-collapse-item__wrap')    # Panel for Order Details

            # Extract information from Basic Information
            order_number = basic_information.find('p', string='Order Number').find_next_sibling('p').text.strip()
            doctor_name = basic_information.find('p', string="Doctor's Name").find_next_sibling('p').text.strip()
            scan_time = basic_information.find('p', string='Scan Time').find_next_sibling('p').text.strip()
            
            # Extract information from Order Details
            remarks = order_details.find('p', string='Remarks').find_next_sibling('p').text.strip()
            # tooth_number is not always provided
            try:
                tooth_number = order_details.find('p', string='Tooth Number').find_next_sibling('p').text.strip()
            except AttributeError:
                tooth_number = ""
            # Find the download PLY button and execute a click event on it
            # Locate the footer element first
            footer = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'drawer-footer'))
            )
            download_element = footer.find_element(By.CSS_SELECTOR, ".down-icon.ply.bottom_icon")
            driver.execute_script("arguments[0].click();", download_element)
            time.sleep(1)
            
            # create OrderInfo object, store all info there and upload to gsheet/gdrive
            order_info = OrderInfo(
                                    order_number=order_number,
                                    doctor_name=doctor_name,
                                    scan_time=scan_time,
                                    remarks=remarks, 
                                    tooth_number=tooth_number
                                )

            order_info_list.append(order_info)

            # in order to close the side panel we simply click outside the panel
            helium.click(order_number_button.text.strip())
            # wait for panel to close
            time.sleep(2)
    
    if len(order_info_list) == 0:
        print("NO UNASSIGNED ORDERS")
        time.sleep(4)

    for order_info in order_info_list:
        # this uploads to gdrive and returns the link to the gdrive folder
        order_info.link_to_folder = gdrive_handler.upload(order_info)
        # this uploads the order_info to the gsheet
        gsheet_handler.upload(order_info)

    helium.kill_browser()
    
