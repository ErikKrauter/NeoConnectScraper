from neoss_scraper import scrape_orders
from fallupload import handle_orders

# just comment out scrape_orders or hanled_orders if you do not want to scrape neoss or handle orders from fallupload
if __name__ == '__main__':
    print("starting to scrape orders from the web")
    scrape_orders()
    print("starting to move order from fallupload to destination")
    handle_orders()