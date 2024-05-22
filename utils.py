import os
import time
import logging
import requests
from urllib.parse import urljoin, urlparse

logger = logging.getLogger('scraper')

def setup_directory(attempt_number, url_id):
    base_dir = os.path.join('cdn', f'attempt_{attempt_number}', f'url_{url_id}')
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

def save_pdf(pdf_url, pdf_content, product_uid, headers):
    if pdf_url and pdf_content and product_uid:
        parsed_url = urlparse(pdf_url)
        pdf_path = os.path.join('cdn', parsed_url.path.lstrip('/'))
        pdf_dir = os.path.dirname(pdf_path)

        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)

        if not os.path.exists(pdf_path):
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
        return pdf_path
    return None

def save_html(base_dir, html):
    logger.debug('Saving HTML content.')
    with open(os.path.join(base_dir, 'html', 'page.html'), 'w', encoding='utf-8') as f:
        f.write(html)

def mimic_human_behavior(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def download_and_save_file(file_url, headers):
    parsed_url = urlparse(file_url)
    file_path = os.path.join('cdn', parsed_url.path.lstrip('/'))
    file_dir = os.path.dirname(file_path)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)

    if not os.path.exists(file_path):
        file_content = requests.get(file_url, headers=headers).content
        with open(file_path, 'wb') as f:
            f.write(file_content)
    return file_path

def download_and_replace_images(soup, headers):
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not src.startswith('http'):
            img_url = urljoin('https://www.sigmaaldrich.com', src)
            img_path = download_and_save_file(img_url, headers)
            img['src'] = f'https://azma.market/content/{os.path.relpath(img_path, "cdn")}'
    return str(soup)

def keep_specific_tags(element, tags_to_keep):
    for tag in element.find_all(True):
        if tag.name not in tags_to_keep:
            tag.unwrap()
    return str(element)

def download_and_replace_safety_images(soup, headers):
    table_html = '<table>'
    for div in soup.select('div.MuiGrid-item'):
        header = div.select_one('h3').get_text(strip=True)
        content = []
        for elem in div.select('div.jss304 img, div.jss305 a, div.jss305 p'):
            if elem.find('img'):
                src = elem['src']
                img_url = urljoin('https://www.sigmaaldrich.com', src)
                img_path = download_and_save_file(img_url, headers)
                content.append(f'<img src="https://azma.market/content/safety/{os.path.relpath(img_path, "cdn")}"/>')
            else:
                content.append(elem.get_text(strip=True))
        content_html = ' '.join(content)
        table_html += f'<tr><th>{header}</th><td>{content_html}</td></tr>'
    table_html += '</table>'
    return table_html
