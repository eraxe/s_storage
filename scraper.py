import os
import logging
from selenium import webdriver
from database import connect_to_database, fetch_urls
from scraper_conf import db_config, options, service
from logging_setup import setup_logging
from function import scrape_data

setup_logging()  # Ensure logging is set up once at the start

logger = logging.getLogger('scraper')

def main():
    setup_logging()  # Ensure logging is set up once at the start
    conn, cursor = connect_to_database(db_config)
    table_name = 'sitemap_prod_us_en_1'
    urls_to_scrape = fetch_urls(cursor, table_name)

    driver = webdriver.Chrome(service=service, options=options)

    attempt_number = 1
    attempt_base_dir = os.path.join('cdn', f'attempt_{attempt_number}')
    while os.path.exists(attempt_base_dir):
        attempt_number += 1
        attempt_base_dir = os.path.join('cdn', f'attempt_{attempt_number}')

    for url_id, url in urls_to_scrape:
        try:
            logger.info(f'Scraping URL: {url}')
            final_url = scrape_data(driver, url, attempt_number, url_id, cursor, conn)
            logger.debug(f'URL scraped: {final_url}')
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

    driver.quit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
