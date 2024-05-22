import mysql.connector
import logging

logger = logging.getLogger('scraper')

def connect_to_database(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        logger.info('Connected to the MySQL database.')
        return conn, cursor
    except mysql.connector.Error as err:
        logger.error(f'Error connecting to MySQL: {err}')
        raise

def fetch_urls(cursor, table_name, limit=5):
    cursor.execute(f"SELECT id, url FROM {table_name} WHERE scraped = 0 LIMIT %s", (limit,))
    return cursor.fetchall()

def update_scrape_history(cursor, conn, table_name, url_id, current_url, updated_history):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_query = f"""
        UPDATE {table_name}
        SET last_scraped = %s, response = %s, scraped = 1, scrape_history = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (now, current_url, updated_history, url_id))
    conn.commit()
