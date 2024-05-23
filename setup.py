import logging
import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin


def setup_logging():
    logger = logging.getLogger('scraper')
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('scraper.log', mode='a')

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logger.debug('Logging setup complete.')

# setup.py



def get_text_or_empty(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else ''

def get_attribute_or_empty(soup, selector, attribute):
    element = soup.select_one(selector)
    return element.get(attribute) if element else ''

def get_variations_to_json(driver, xpath):
    try:
        parent_element = driver.find_element(By.XPATH, xpath)
        return extract_variations_to_json(parent_element)
    except Exception:
        return json.dumps([])

def get_element_text_or_empty(driver, xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip() if element else ''
    except NoSuchElementException:
        return ''