import time
import json
import re
import logging
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract job details from the job detail page
def extract_job_details(page):
    job_details = {}

    try:
        # Extract Title
        title_element = page.query_selector('h1.position-title')
        job_details['title'] = title_element.inner_text().strip() if title_element else 'No title found'

        # Extract Location
        location_element = page.query_selector('p.position-location')
        job_details['location'] = location_element.inner_text().strip() if location_element else 'No location found'    

        # Extract Application URL
        apply_button = page.query_selector('button[data-test-id="apply-button"]')
        if apply_button:
            apply_button.click()
            page.wait_for_load_state('load') 
            application_url = page.url  
            
            job_details['applyURL'] = application_url
            logging.info(f"Extracted Apply URL: {application_url}")
        else:
            job_details['applyURL'] = 'Apply button not found'

        # Extract Description
        description_element = page.query_selector('div.position-job-description ')
        job_details['description'] = description_element.inner_text().strip() if description_element else 'No description found'

        # Extract Description
        job_details['minimum_qualifications'] = '' 

        job_details['preferred_qualifications'] = ''

        job_details ['responsibilities']  = ''

        job_details ['salary'] = ''
        # Extract Description
        json_ld_element = page.query_selector('script[type="application/ld+json"]')
        if json_ld_element:
            json_data = json_ld_element.inner_text()
            try:
                schema_data = json.loads(json_data)
                job_details['jsonSchema'] = schema_data
            except json.JSONDecodeError:
                logging.error("Error decoding JSON-LD schema")
        
        logging.debug("Extracted job details")
    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details


def scrape_jobs():
    job_listings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://modernatx.eightfold.ai/careers/')
        logging.info("Navigated to job listings page")

        try:
            page.wait_for_selector('div.card  ')
            listing_elements = page.query_selector_all('div.card  ')
            logging.info(f"Found {len(listing_elements)} job listing elements on current page")

            for listing in listing_elements:
                card_element = listing.query_selector('div.position-title')
                if card_element and card_element.is_visible():
                    try:
                        card_element.click()
                        page.wait_for_selector('h1.position-title', timeout=10000)

                        job_details = extract_job_details(page)
                        job_listings.append(job_details)

                        page.go_back()
                        page.wait_for_selector('div.card ', timeout=10000)
                        time.sleep(1)
                    except Exception as e:
                        logging.error("Error processing listing: %s", e)
                        continue

        except Exception as e:
            logging.error("Error during scraping: %s", e)

        browser.close()

    with open('moderna_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to moderna_job_listings.json')

scrape_jobs()