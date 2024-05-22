"""
Project Structure:

1. scraper.py
   - Main Script: Orchestrates the scraping process, initializes the WebDriver, and manages the main loop for scraping URLs.
   - Functions: scrape_data(), main()

2. scraper_conf.py
   - Configuration: Contains configuration for MySQL connection, Selenium options, and logging setup.
   - Variables: db_config, options, service, logger

3. database.py
   - Database Operations: Manages MySQL database connections and queries.
   - Functions: connect_to_database(), fetch_urls(), update_scrape_history()

4. utils.py
   - Utility Functions: Provides helper functions for setting up directories, saving data, mimicking human behavior, and handling images.
   - Functions: setup_directory(), save_data(), mimic_human_behavior(), download_and_replace_images(), keep_specific_tags()

5. logging_setup.py
   - Logging Setup: Configures the logging settings to ensure proper logging throughout the application.
   - Function: setup_logging()
"""
