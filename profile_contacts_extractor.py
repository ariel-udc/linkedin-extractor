#!/usr/bin/env python3
import json
import time
import argparse
import getpass
import logging
import sys
import shutil
import os
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
import config

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not installed. Install with: pip install python-dotenv")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProfileContactsExtractor:
    def __init__(self, headless=False, keep_browser_open=False):
        self.driver = None
        self.headless = headless
        self.keep_browser_open = keep_browser_open
        self.contacts = []
        
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
        
    def navigate_to_profile(self, profile_url):
        try:
            logging.info(f"Navigating to profile: {profile_url}")
            self.driver.get(profile_url)
            
            # Just wait a moment for page to load
            time.sleep(3)
            logging.info("Profile loaded successfully!")
            
        except Exception as e:
            logging.error("Failed to navigate to profile", exc_info=True)
            raise
            
    def click_contacts_link(self):
        try:
            logging.info("Looking for contacts link...")
            
            # Primary selector - look for the connectionOf URL pattern
            contacts_selectors = [
                "//a[contains(@href, '/search/results/people/?connectionOf=')]",
                "//a[contains(@href, 'connectionOf')]",
                "//a[contains(text(), 'contactos')]",
                "//a[contains(text(), 'contacts')]",
                "//span[contains(text(), 'contactos')]/parent::*/parent::a",
                "//span[contains(text(), 'contacts')]/parent::*/parent::a"
            ]
            
            contacts_link = None
            for selector in contacts_selectors:
                try:
                    logging.info(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(f"Found {len(elements)} elements with selector")
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            contacts_link = element
                            href = element.get_attribute("href")
                            text = element.text
                            logging.info(f"Found contacts link - Text: '{text}', URL: {href}")
                            break
                    if contacts_link:
                        break
                except Exception as selector_error:
                    logging.warning(f"Selector failed: {selector_error}")
                    continue
            
            if not contacts_link:
                logging.error("Contacts link not found. Make sure you're on a profile page.")
                # Try to find all links on the page for debugging
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                logging.info(f"Found {len(all_links)} total links on the page")
                for link in all_links[:10]:  # Show first 10 links
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        if href and ("contact" in href.lower() or "connection" in href.lower()):
                            logging.info(f"Potential contact link: '{text}' -> {href}")
                    except:
                        continue
                raise Exception("Contacts link not found")
            
            # Click the contacts link
            contacts_link.click()
            
            # Wait for contacts page to load
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container")))
            except:
                # Fallback selectors for search results
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".reusable-search__result-container")))
                except:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results")))
            
            logging.info("Contacts page loaded successfully!")
            
        except Exception as e:
            logging.error("Failed to click contacts link", exc_info=True)
            raise
            
    def load_all_contacts_with_pagination(self):
        try:
            logging.info("Loading all contacts with pagination...")
            
            page_count = 1
            
            while True:
                logging.info(f"Processing page {page_count}...")
                
                # Wait for current page to load
                time.sleep(config.SCROLL_PAUSE_TIME)
                
                # Extract contacts from current page
                self.extract_contacts_from_current_page(page_count)
                
                # Look for next page button
                next_button = None
                try:
                    # Try different selectors for next page button
                    next_selectors = [
                        "//button[@aria-label='Next']",
                        "//button[contains(@class, 'artdeco-pagination__button--next')]",
                        "//button[contains(@aria-label, 'Next')]",
                        "//button[contains(@aria-label, 'Siguiente')]",
                        "//li[@class='artdeco-pagination__indicator artdeco-pagination__indicator--number']/following-sibling::li/button",
                        "//use[@href='#chevron-right-small']/ancestor::button"
                    ]
                    
                    for selector in next_selectors:
                        try:
                            buttons = self.driver.find_elements(By.XPATH, selector)
                            for button in buttons:
                                if button.is_displayed() and button.is_enabled():
                                    next_button = button
                                    break
                            if next_button:
                                break
                        except:
                            continue
                            
                except Exception as e:
                    logging.warning(f"Error looking for next button: {e}")
                
                if next_button:
                    try:
                        logging.info(f"Found next page button, clicking to load page {page_count + 1}...")
                        
                        # Scroll to button and click
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(1)
                        next_button.click()
                        
                        # Wait for page to load
                        time.sleep(config.SCROLL_PAUSE_TIME)
                        page_count += 1
                        
                    except Exception as click_error:
                        logging.warning(f"Failed to click next button: {click_error}")
                        break
                else:
                    logging.info("No more pages found. Pagination complete.")
                    break
                    
            logging.info(f"Finished loading all contacts. Total pages processed: {page_count}")
                
        except Exception as e:
            logging.error("Failed to load contacts with pagination", exc_info=True)
            raise
            
    def extract_contacts_from_current_page(self, page_number):
        try:
            logging.info(f"Extracting contacts from page {page_number}...")
            
            # Find all mb1 containers on current page
            mb1_containers = self.driver.find_elements(By.XPATH, "//*[@class='mb1']")
            logging.info(f"Found {len(mb1_containers)} mb1 containers on page {page_number}")
            
            page_contacts = 0
            
            for container in mb1_containers:
                try:
                    # Look for LinkedIn profile link within this container
                    profile_links = container.find_elements(By.XPATH, ".//a[contains(@href, 'linkedin.com/in/')]")
                    
                    if not profile_links:
                        continue  # Skip if no profile link found
                    
                    profile_link = profile_links[0]  # Take the first one
                    profile_url = profile_link.get_attribute("href")
                    
                    if not profile_url:
                        continue
                    
                    # Check if we already have this contact (avoid duplicates)
                    if any(contact['profile_url'] == profile_url for contact in self.contacts):
                        continue
                    
                    # Extract name from the link text
                    name = ""
                    spans = profile_link.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        span_text = span.text.strip()
                        if (span_text and 
                            not span_text.startswith("Ver el perfil") and 
                            not span_text.startswith("View") and
                            span_text != "• 2º" and 
                            span_text != "Contacto de 2.º grado" and
                            len(span_text) > 2):
                            name = span_text
                            break
                    
                    if not name:
                        link_text = profile_link.text.strip()
                        if link_text and not link_text.startswith("Ver el perfil"):
                            name = link_text
                    
                    # Extract additional info from mb1 container divs
                    alternative_name = ""
                    job_position = ""
                    location = ""
                    
                    try:
                        # Get all direct div children of the mb1 container
                        divs = container.find_elements(By.XPATH, "./div")
                        
                        # div[0] = alternative name
                        if len(divs) > 0:
                            alt_name_text = divs[0].text.strip()
                            if alt_name_text:
                                alternative_name = alt_name_text
                        
                        # div[1] = job position
                        if len(divs) > 1:
                            job_text = divs[1].text.strip()
                            if job_text:
                                job_position = job_text
                        
                        # div[2] = location
                        if len(divs) > 2:
                            location_text = divs[2].text.strip()
                            if location_text:
                                location = location_text
                                
                    except Exception as div_error:
                        logging.warning(f"Failed to extract div info for {name}: {div_error}")
                    
                    if not name or not profile_url:
                        continue
                    
                    # Create contact data with all extracted information
                    contact_data = {
                        "name": name,
                        "alternative_name": alternative_name,
                        "job_position": job_position,
                        "location": location,
                        "profile_url": profile_url
                    }
                    
                    self.contacts.append(contact_data)
                    page_contacts += 1
                    logging.info(f"Page {page_number} - Extracted: {name} | Alt: {alternative_name} | Job: {job_position} | Location: {location}")
                    
                except Exception as e:
                    logging.warning("Failed to extract data from mb1 container", exc_info=True)
                    continue
                    
            logging.info(f"Extracted {page_contacts} new contacts from page {page_number}. Total so far: {len(self.contacts)}")
            
        except Exception as e:
            logging.error(f"Failed to extract contacts from page {page_number}", exc_info=True)
            raise
            
    def extract_contacts(self):
        try:
            logging.info("Extracting contact data...")
            
            # Find all LinkedIn profile links directly
            profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'linkedin.com/in/')]")
            logging.info(f"Found {len(profile_links)} LinkedIn profile links")
            
            for profile_link in profile_links:
                try:
                    # Extract profile URL
                    profile_url = profile_link.get_attribute("href")
                    if not profile_url:
                        continue
                    
                    # Extract name from the link text - look for spans with actual names
                    name = ""
                    
                    # Get all spans within the link
                    spans = profile_link.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        span_text = span.text.strip()
                        # Look for the actual name (not the "Ver el perfil" text)
                        if (span_text and 
                            not span_text.startswith("Ver el perfil") and 
                            not span_text.startswith("View") and
                            span_text != "• 2º" and 
                            span_text != "Contacto de 2.º grado" and
                            len(span_text) > 2):  # Names should be longer than 2 characters
                            name = span_text
                            break
                    
                    if not name:
                        # Fallback: try to get name from the link text directly
                        link_text = profile_link.text.strip()
                        if link_text and not link_text.startswith("Ver el perfil"):
                            name = link_text
                    
                    if not name or not profile_url:
                        continue  # Skip if we can't find basic info
                    
                    # For now, just extract name and profile URL
                    contact_data = {
                        "name": name,
                        "profile_url": profile_url
                    }
                    
                    self.contacts.append(contact_data)
                    logging.info(f"Extracted contact: {name} | URL: {profile_url}")
                    
                except Exception as e:
                    logging.warning("Failed to extract data from profile link", exc_info=True)
                    continue
                    
            logging.info(f"Extracted {len(self.contacts)} contacts total")
            
        except Exception as e:
            logging.error("Failed to extract contacts", exc_info=True)
            raise
        
    def save_to_file(self, output_file, profile_url):
        try:
            logging.info(f"Saving contacts to {output_file}...")
            
            data = {
                "profile_url": profile_url,
                "total_contacts": len(self.contacts),
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "contacts": self.contacts
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Successfully saved {len(self.contacts)} contacts to {output_file}")
            
        except Exception as e:
            logging.error("Failed to save contacts to file", exc_info=True)
            raise
        
    def run(self, email, password, profile_url, output_file):
        try:
            self.setup_driver()
            self.login(email, password)
            self.navigate_to_profile(profile_url)
            
            # Debug pause if keep browser open is enabled
            if self.keep_browser_open:
                logging.info("Browser kept open for debugging. Check the profile page now.")
                input("Press Enter when ready to continue with extraction...")
            
            self.click_contacts_link()
            self.load_all_contacts_with_pagination()
            self.save_to_file(output_file, profile_url)
            
        except Exception as e:
            logging.error("Application error occurred", exc_info=True)
            
        finally:
            if self.driver:
                logging.info("Extraction complete. Browser kept open for inspection.")
                input("Press Enter to close browser and exit...")
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Extract contacts from a LinkedIn profile")
    parser.add_argument("profile_url", help="LinkedIn profile URL")
    parser.add_argument("--output-file", default=None, help="Output JSON file name")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--keep-browser-open", action="store_true", help="Keep browser open after completion for debugging")
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if not args.output_file:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.output_file = f"profile_contacts_{timestamp}.json"
    
    # Try to get credentials from environment variables
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if email and password:
        logging.info("Using credentials from .env file")
    else:
        logging.info("No .env file found or credentials missing, asking for manual input")
        if not email:
            email = input("Enter your LinkedIn email: ")
        if not password:
            password = getpass.getpass("Enter your LinkedIn password: ")
    
    extractor = ProfileContactsExtractor(headless=args.headless, keep_browser_open=args.keep_browser_open)
    extractor.run(email, password, args.profile_url, args.output_file)

if __name__ == "__main__":
    main()