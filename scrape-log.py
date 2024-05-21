import os
import time
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import logging
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger('scraper')
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('scraper.log', mode='a')

# Set logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Test logging setup
logger.debug('Starting the scraper script.')

# MySQL connection details
db_config = {
    'user': 'sigma',
    'password': 'password',
    'host': 'localhost',
    'port': '3306',
    'database': 'sigma'
}

# Selenium configuration
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

service = Service('/home/katana/Projects/selenium/sigma_storage/chrome/driver/chromedriver')


# Setup directories
def setup_directory(attempt_number, url_id):
    base_dir = os.path.join('scrape_data', f'attempt_{attempt_number}', f'url_{url_id}')
    os.makedirs(base_dir, exist_ok=True)
    subdirs = ['html', 'pdf', 'images']
    for subdir in subdirs:
        os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)
    return base_dir


# Save data to files
def save_data(base_dir, html, pdf_url=None, pdf_content=None, product_uid=None):
    logger.debug('Saving HTML content.')
    with open(os.path.join(base_dir, 'html', 'page.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    pdf_path = None
    if pdf_url and pdf_content and product_uid:
        logger.debug(f'Saving PDF content from {pdf_url}.')
        pdf_path = os.path.join(base_dir, 'pdf', f'{product_uid}.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
    return pdf_path


# Function to mimic human behavior
def mimic_human_behavior(driver):
    # Minimal scrolling
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def scrape_data(url, attempt_number, url_id, cursor, conn):
    logger.debug(f'Scraping data from URL: {url}')
    driver.get(url)

    # Handle potential redirects
    time.sleep(5)
    current_url = driver.current_url

    # Mimic human behavior
    mimic_human_behavior(driver)

    # Extract visible HTML content
    html = driver.page_source

    # Define headers for requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Parse HTML to find the specification sheet link
    soup = BeautifulSoup(html, 'html.parser')
    spec_sheet_link = soup.find('a', {'data-testid': 'prod-info-quick-access-specification-sheet-link'})

    pdf_url = None
    pdf_content = None
    product_uid = None
    if spec_sheet_link:
        relative_pdf_url = spec_sheet_link.get('href')
        pdf_url = urljoin('https://www.sigmaaldrich.com', relative_pdf_url)
        pdf_content = requests.get(pdf_url, headers=headers).content
        logger.debug(f'PDF content length: {len(pdf_content)} bytes')

    # Extract product data with checks
    product_name = soup.select_one('span#product-name').get_text(strip=True) if soup.select_one(
        'span#product-name') else ''
    image_element = soup.select_one('img#active-image')
    image_url = urljoin('https://www.sigmaaldrich.com', image_element.get('src')) if image_element else ''
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
        'div:nth-of-type(4) div.jss173') else ''
    pubchem_substance_id = soup.select_one('.jss173 a[target]').get_text(strip=True) if soup.select_one(
        '.jss173 a[target]') else ''
    nacres = soup.select_one('div.jss171:nth-of-type(6) div:nth-of-type(2)').get_text(strip=True) if soup.select_one(
        'div.jss171:nth-of-type(6) div:nth-of-type(2)') else ''
    properties = str(soup.select_one('div.jss235')) if soup.select_one('div.jss235') else ''
    description = str(soup.select_one('#pdp-description--div .jss231 div.MuiContainer-root')) if soup.select_one(
        '#pdp-description--div .jss231 div.MuiContainer-root') else ''
    safety_information = str(soup.select_one('#pdp-safetyInfo .jss231 div.MuiContainer-root')) if soup.select_one(
        '#pdp-safetyInfo .jss231 div.MuiContainer-root') else ''
    specification_sheet = pdf_url
    related_categories = [e.get_text(strip=True) for e in soup.select('.MuiGrid-grid-md-3 div')] if soup.select(
        '.MuiGrid-grid-md-3 div') else []
    code = soup.select_one('p.jss125').get_text(strip=True) if soup.select_one('p.jss125') else ''
    brand_image = soup.select_one('img.jss122').get('src') if soup.select_one('img.jss122') else ''
    code_sub = [e.get_text(strip=True) for e in soup.select('.jss90 span.jss652')] if soup.select(
        '.jss90 span.jss652') else []
    thumbs_images = str(soup.select_one('.jss202 div.slider-list')) if soup.select_one(
        '.jss202 div.slider-list') else ''

    # Fetch UID for the product
    cursor.execute("SELECT uid FROM sitemap_prod_us_en_1 WHERE url = %s", (url,))
    result = cursor.fetchone()
    if result:
        product_uid = result[0]

    # Save all captured data
    base_dir = setup_directory(attempt_number, url_id)
    pdf_path = save_data(base_dir, html, pdf_url, pdf_content, product_uid)

    # Save active image
    image_path = None
    if image_url and product_uid:
        image_content = requests.get(image_url, headers=headers).content
        image_path = os.path.join(base_dir, 'images', f'{product_uid}.png')
        with open(image_path, 'wb') as f:
            f.write(image_content)

    # Insert product data into the relational table
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
            product_name, image_path, str(size_select), str(synonyms), linear_formula,
            cas_number, ec_number, molecular_weight, beilstein, mdl_number,
            pubchem_substance_id, nacres, properties, description,
            safety_information, pdf_path, str(related_categories),
            code, brand_image, str(code_sub), thumbs_images, product_uid
        )
        cursor.execute(insert_query, values)
        conn.commit()

    # Update the main table with scrape details
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(f"SELECT scrape_history FROM sitemap_prod_us_en_1 WHERE id = %s", (url_id,))
    result = cursor.fetchone()
    if result:
        scrape_history = result[0] or ""
        updated_history = scrape_history + f"{now}, "
    else:
        updated_history = f"{now}, "
    update_query = f"""
        UPDATE sitemap_prod_us_en_1
        SET last_scraped = %s, response = %s, scraped = 1, scrape_history = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (now, current_url, updated_history, url_id))
    conn.commit()

    # Delete the saved HTML file to save space
    os.remove(os.path.join(base_dir, 'html', 'page.html'))

    return current_url


# Main script logic
try:
    logger.debug('Attempting to connect to MySQL database.')
    # Connect to MySQL database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    logger.info('Connected to the MySQL database.')

    # Fetch URLs from one of the tables (limited to 5 for testing)
    table_name = 'sitemap_prod_us_en_1'
    logger.debug(f'Executing SQL query to fetch URLs from {table_name}.')
    cursor.execute(f"SELECT id, url FROM {table_name} WHERE scraped = 0 LIMIT 5")
    urls_to_scrape = cursor.fetchall()
    logger.info(f'Fetched {len(urls_to_scrape)} URLs to scrape.')

    # Set up Selenium WebDriver
    logger.debug('Setting up Selenium WebDriver.')
    driver = webdriver.Chrome(service=service, options=options)
    logger.info('Selenium WebDriver has been initialized.')

    # Determine attempt number
    attempt_number = 1
    attempt_base_dir = os.path.join('scrape_data', f'attempt_{attempt_number}')
    while os.path.exists(attempt_base_dir):
        attempt_number += 1
        attempt_base_dir = os.path.join('scrape_data', f'attempt_{attempt_number}')

    # Scrape data for each URL and update the database
    for url_id, url in urls_to_scrape:
        try:
            logger.info(f'Scraping URL: {url}')
            final_url = scrape_data(url, attempt_number, url_id, cursor, conn)
            logger.debug(f'URL scraped: {final_url}')
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

finally:
    # Close connections
    if 'driver' in locals():
        driver.quit()
        logger.info('Selenium WebDriver has been closed.')
    if 'cursor' in locals():
        cursor.close()
        logger.info('Database cursor has been closed.')
    if 'conn' in locals():
        conn.close()
        logger.info('MySQL connection has been closed.')

    # Ensure handlers are flushed and closed
    for handler in logger.handlers:
        handler.flush()
        handler.close()
