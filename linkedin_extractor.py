#!/usr/bin/env python3
import json
import time
import argparse
import getpass
import logging
import sys
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LinkedInExtractor:
    def __init__(self, headless=False, keep_browser_open=False):
        self.driver = None
        self.headless = headless
        self.keep_browser_open = keep_browser_open
        self.connections = []
        
    def setup_driver(self):
        try:
            logging.info("Setting up Firefox driver...")
            
            # Check if Firefox is installed
            firefox_paths = [
                "/usr/bin/firefox",
                "/usr/bin/firefox-esr",
                "/snap/bin/firefox",
                "/usr/local/bin/firefox"
            ]
            
            firefox_binary = None
            for path in firefox_paths:
                if shutil.which(path) or (path.startswith('/') and shutil.which(path.split('/')[-1])):
                    firefox_binary = path
                    break
            
            if not firefox_binary:
                logging.error("Firefox not found. Please install Firefox browser.")
                sys.exit(1)
            
            logging.info(f"Using Firefox binary: {firefox_binary}")
            
            firefox_options = Options()
            firefox_options.binary_location = firefox_binary
            
            if self.headless:
                firefox_options.add_argument("--headless")
                
            for option in config.FIREFOX_OPTIONS:
                firefox_options.add_argument(option)
                
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            logging.info("Firefox driver setup completed successfully")
            
        except Exception as e:
            logging.error("Failed to setup Firefox driver", exc_info=True)
            raise
        
    def login(self, email, password):
        try:
            logging.info("Navigating to LinkedIn login page...")
            self.driver.get(config.LOGIN_URL)
            
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            password_field = self.driver.find_element(By.ID, "password")
            
            email_field.send_keys(email)
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            logging.info("Waiting for login to complete...")
            
            # Check for verification code requirement
            try:
                # Wait a bit to see if verification is required
                time.sleep(3)
                
                # Check for verification code input field
                verification_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[name='pin']")
                if verification_elements:
                    logging.info("Verification code required. Please check your email/phone for the code.")
                    verification_code = input("Enter the verification code: ")
                    
                    verification_field = verification_elements[0]
                    verification_field.send_keys(verification_code)
                    
                    # Submit verification
                    submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                    submit_button.click()
                    
                    logging.info("Verification code submitted, waiting for completion...")
                    
                # Wait for successful login (global nav appears)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "global-nav")))
                logging.info("Login successful!")
                
            except Exception as verification_error:
                # If verification check fails, try to continue with normal login flow
                logging.warning("Verification check failed, attempting normal login flow", exc_info=True)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "global-nav")))
                logging.info("Login successful!")
            
        except Exception as e:
            logging.error("Login failed", exc_info=True)
            raise
        
    def navigate_to_connections(self):
        try:
            logging.info("Navigating to connections page...")
            self.driver.get(config.CONNECTIONS_URL)
            
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mn-connections")))
            logging.info("Connections page loaded!")
            
        except Exception as e:
            logging.error("Failed to navigate to connections page", exc_info=True)
            raise
        
    def scroll_and_load_connections(self):
        try:
            logging.info("Loading all connections using infinite scroll...")
            
            # Get initial connection count
            initial_connections = len(self.driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card"))
            logging.info(f"Initial connections visible: {initial_connections}")
            
            last_connection_count = initial_connections
            no_change_count = 0
            scroll_attempts = 0
            
            while scroll_attempts < config.MAX_SCROLL_ATTEMPTS:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(config.SCROLL_PAUSE_TIME)
                
                # Check current connection count
                current_connections = len(self.driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card"))
                
                if current_connections > last_connection_count:
                    logging.info(f"New connections loaded: {current_connections} (was {last_connection_count})")
                    last_connection_count = current_connections
                    no_change_count = 0
                else:
                    no_change_count += 1
                    logging.info(f"No new connections after scroll attempt {scroll_attempts + 1}")
                
                # If no new connections for 3 consecutive attempts, we're done
                if no_change_count >= 3:
                    logging.info(f"No new connections loaded after {no_change_count} attempts. Finished loading.")
                    break
                
                # Also try to find and click load more buttons (fallback)
                load_more_selectors = [
                    "//button[contains(text(), 'Load more')]",
                    "//button[contains(text(), 'Cargar más')]", 
                    "//button[contains(text(), 'Cargar mas')]",
                    "//button[contains(text(), 'Show more')]",
                    "//button[contains(text(), 'Ver más')]",
                    "//button[contains(text(), 'Ver mas')]",
                    "//button[contains(@class, 'scaffold-finite-scroll__load-button')]",
                    "//button[contains(@class, 'artdeco-button--secondary')]"
                ]
                
                for selector in load_more_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                logging.info(f"Found and clicking load more button: {button.text}")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(1)
                                button.click()
                                time.sleep(config.SCROLL_PAUSE_TIME)
                                break
                    except:
                        continue
                
                scroll_attempts += 1
                
            final_connections = len(self.driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card"))
            logging.info(f"Finished loading connections. Total visible: {final_connections} (loaded {final_connections - initial_connections} new)")
                
        except Exception as e:
            logging.error("Failed to scroll and load connections", exc_info=True)
            raise
            
    def extract_connections(self):
        try:
            logging.info("Extracting connection data...")
            
            connection_elements = self.driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card")
            
            for element in connection_elements:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, ".mn-connection-card__name")
                    name = name_element.text.strip()
                    
                    occupation_element = element.find_element(By.CSS_SELECTOR, ".mn-connection-card__occupation")
                    occupation = occupation_element.text.strip()
                    
                    profile_link = element.find_element(By.CSS_SELECTOR, ".mn-connection-card__link")
                    profile_url = profile_link.get_attribute("href")
                    
                    connection_data = {
                        "name": name,
                        "occupation": occupation,
                        "profile_url": profile_url
                    }
                    
                    self.connections.append(connection_data)
                    
                except Exception as e:
                    logging.warning("Failed to extract data from connection element", exc_info=True)
                    continue
                    
            logging.info(f"Extracted {len(self.connections)} connections")
            
        except Exception as e:
            logging.error("Failed to extract connections", exc_info=True)
            raise
        
    def save_to_file(self, output_file):
        try:
            logging.info(f"Saving connections to {output_file}...")
            
            data = {
                "total_connections": len(self.connections),
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "connections": self.connections
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Successfully saved {len(self.connections)} connections to {output_file}")
            
        except Exception as e:
            logging.error("Failed to save connections to file", exc_info=True)
            raise
        
    def run(self, email, password, output_file):
        try:
            self.setup_driver()
            self.login(email, password)
            self.navigate_to_connections()
            
            # Debug pause if keep browser open is enabled
            if self.keep_browser_open:
                logging.info("Scrolling to bottom to show Load more button...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                logging.info("Browser kept open for debugging. Inspect the 'Load more' button now.")
                input("Press Enter when ready to continue with extraction...")
            
            self.scroll_and_load_connections()
            self.extract_connections()
            self.save_to_file(output_file)
            
        except Exception as e:
            logging.error("Application error occurred", exc_info=True)
            
        finally:
            if self.driver and not self.keep_browser_open:
                logging.info("Closing browser")
                self.driver.quit()
            elif self.driver and self.keep_browser_open:
                logging.info("Extraction complete. Browser kept open for final inspection.")
                input("Press Enter to close browser and exit...")

def main():
    parser = argparse.ArgumentParser(description="Extract LinkedIn connections")
    parser.add_argument("--output-file", default=config.get_output_filename(), 
                       help="Output JSON file name")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browser in headless mode")
    parser.add_argument("--keep-browser-open", action="store_true", 
                       help="Keep browser open after completion for debugging")
    
    args = parser.parse_args()
    
    email = input("Enter your LinkedIn email: ")
    password = getpass.getpass("Enter your LinkedIn password: ")
    
    extractor = LinkedInExtractor(headless=args.headless, keep_browser_open=args.keep_browser_open)
    extractor.run(email, password, args.output_file)

if __name__ == "__main__":
    main()