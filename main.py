from neoss_scraper import scrape_orders
from fallupload import handle_orders

if __name__ == '__main__':
    #print("starting to scrape orders from the web")
    #scrape_orders()
    print("starting to move order from fallupload to destination")
    handle_orders()