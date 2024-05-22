import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse

from database import connect_to_database, fetch_urls, update_scrape_history
from utils import setup_directory, save_data, mimic_human_behavior, download_and_replace_images, keep_specific_tags, \
    download_and_replace_safety_images, save_html, save_pdf, download_and_save_file
from scraper_conf import db_config, options, service
from logging_setup import setup_logging

setup_logging()  # Ensure logging is set up once at the start

logger = logging.getLogger('scraper')


def scrape_data(driver, url, attempt_number, url_id, cursor, conn):
    logger.debug(f'Scraping data from URL: {url}')
    driver.get(url)
    time.sleep(5)
    current_url = driver.current_url
    mimic_human_behavior(driver)
    html = driver.page_source

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    soup = BeautifulSoup(html, 'html.parser')
    spec_sheet_link = soup.find('a', {'data-testid': 'prod-info-quick-access-specification-sheet-link'})
    pdf_url = None
    pdf_content = None
    product_uid = None
    image_url = None

    if spec_sheet_link:
        relative_pdf_url = spec_sheet_link.get('href')
        pdf_url = urljoin('https://www.sigmaaldrich.com', relative_pdf_url)
        pdf_content = requests.get(pdf_url, headers=headers).content
        logger.debug(f'PDF content length: {len(pdf_content)} bytes')

    cursor.execute("SELECT uid FROM sitemap_prod_us_en_1 WHERE url = %s", (url,))
    result = cursor.fetchone()
    if result:
        product_uid = result[0]

    base_dir = setup_directory(attempt_number, url_id)
    pdf_path = save_pdf(pdf_url, pdf_content, product_uid, headers)
    save_html(base_dir, html)

    tags_to_keep = ['h3', 'p', 'br', 'div']

    product_name = soup.select_one('span#product-name').get_text(strip=True) if soup.select_one(
        'span#product-name') else ''
    image_element = soup.select_one('img#active-image')
    if image_element:
        image_url = urljoin('https://www.sigmaaldrich.com', image_element.get('src'))
    logger.debug(f'image_url: {image_url}')

    size_select = [e.get_text(strip=True) for e in soup.select('.jss449 span.jss441')] if soup.select(
        '.jss449 span.jss441') else []
    synonyms = [e.get_text(strip=True) for e in soup.select('.jss167 span')] if soup.select('.jss167 span') else []
    linear_formula = soup.select_one('div.jss169').get_text(strip=True) if soup.select_one('div.jss169') else ''
    cas_number = soup.select_one('div.jss171:nth-of-type(1) div.jss173').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(1) div.jss173') else ''
    ec_number = soup.select_one('div.jss171:nth-of-type(3) div.jss173').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(3) div.jss173') else ''
    molecular_weight = soup.select_one('div.jss171:nth-of-type(2) span').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(2) span') else ''
    beilstein = soup.select_one('div.jss171:nth-of-type(3) span').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(3) span') else ''
    mdl_number = soup.select_one('div:nth-of-type(4) div.jss173').get_text(strip=True) if soup.select_one(
        'div.jss173:nth-of-type(4) div.jss173') else ''
    pubchem_substance_id = soup.select_one('.jss173 a[target]').get_text(strip=True) if soup.select_one(
        '.jss173 a[target]') else ''
    nacres = soup.select_one('div.jss171:nth-of-type(6) div:nth-of-type(2)').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(6) div.jss173:nth-of-type(2)') else ''
    properties = str(soup.select_one('div.jss235')) if soup.select_one('div.jss235') else ''

    description_element = soup.select_one('[data-testid="pdp-description"]')
    description_html = keep_specific_tags(description_element, tags_to_keep) if description_element else ''
    description = download_and_replace_images(BeautifulSoup(description_html, 'html.parser'), headers) if description_html else ''

    safety_info_element = soup.select_one('[data-testid="pdp-safety-info"]')
    safety_information = download_and_replace_safety_images(safety_info_element, headers) if safety_info_element else ''

    specification_sheet = pdf_url
    related_categories = [e.get_text(strip=True) for e in soup.select('.MuiGrid-grid-md-3 div')] if soup.select(
        '.MuiGrid-grid-md-3 div') else []
    code = soup.select_one('p.jss125').get_text(strip=True) if soup.select_one('p.jss125') else ''
    brand_image = soup.select_one('img.jss122').get('src') if soup.select_one('img.jss122') else ''
    code_sub = [e.get_text(strip=True) for e in soup.select('.jss90 span.jss652')] if soup.select(
        '.jss90 span.jss652') else []
    thumbs_images = str(soup.select_one('.jss202 div.slider-list')) if soup.select_one(
        '.jss202 div.slider-list') else ''

    image_path = None
    if image_url and product_uid:
        logger.debug(f'Downloading image from {image_url}')
        image_path = download_and_save_file(image_url, headers)
        logger.debug(f'Saved image to {image_path}')
    else:
        logger.warning(f'image_url or product_uid is not set. image_url: {image_url}, product_uid: {product_uid}')

    if product_uid:
        insert_query = f"""
            INSERT INTO sitemap_prod_us_en_1_DATA (
                product_name, image, size_select, synonyms, linear_formula, 
                cas_number, ec_number, molecular_weight, beilstein, mdl_number, 
                pubchem_substance_id, nacres, properties, description, 
                safety_information, specification_sheet, related_categories, 
                code, brand_image, code_sub, thumbs_images, uid
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            product_name, image_path, ', '.join(size_select), ', '.join(synonyms), linear_formula,
            cas_number, ec_number, molecular_weight, beilstein, mdl_number,
            pubchem_substance_id, nacres, properties, description,
            safety_information, pdf_path, ', '.join(related_categories),
            code, brand_image, ', '.join(code_sub), thumbs_images, product_uid
        )
        cursor.execute(insert_query, values)
        conn.commit()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(f"SELECT scrape_history FROM sitemap_prod_us_en_1 WHERE id = %s", (url_id,))
    result = cursor.fetchone()
    if result:
        scrape_history = result[0] or ""
        updated_history = scrape_history + f"{now}, "
    else:
        updated_history = f"{now}, "

    update_scrape_history(cursor, conn, 'sitemap_prod_us_en_1', url_id, current_url, updated_history)
    os.remove(os.path.join(base_dir, 'html', 'page.html'))
    return current_url

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
