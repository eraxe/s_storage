import os
import time
import logging
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger('scraper')

def setup_directory(attempt_number, url_id):
    base_dir = os.path.join('scrape_data', f'attempt_{attempt_number}', f'url_{url_id}')
    os.makedirs(base_dir, exist_ok=True)
    subdirs = ['html', 'pdf', 'images']
    for subdir in subdirs:
        os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)
    return base_dir

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

def mimic_human_behavior(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def download_and_replace_images(soup, base_dir, headers):
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not src.startswith('http'):
            img_url = urljoin('https://www.sigmaaldrich.com', src)
            img_content = requests.get(img_url, headers=headers).content
            img_path = os.path.join(base_dir, 'images', os.path.basename(urlparse(img_url).path))
            with open(img_path, 'wb') as f:
                f.write(img_content)
            img['src'] = f'https://azma.market/content/{os.path.relpath(img_path, base_dir)}'
    return str(soup)

def keep_specific_tags(element, tags_to_keep):
    for tag in element.find_all(True):
        if tag.name not in tags_to_keep:
            tag.unwrap()
    return str(element)
