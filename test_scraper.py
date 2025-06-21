# main.py
# A Python script to scrape lawyer data from Avvo search results page.
# This script uses Selenium to interactively perform a search and BeautifulSoup to parse the HTML.
#
# --- ONE-TIME SETUP ---
# You need to install the required libraries. Open your terminal or command prompt and run:
# pip install selenium webdriver-manager beautifulsoup4 requests

import requests
from bs4 import BeautifulSoup
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def perform_search_and_get_page_source(search_query, location):
    """
    Automates a browser to perform a search on Avvo.com and returns the results page HTML.
    This mimics human behavior to avoid being blocked.
    
    Args:
        search_query (str): The practice area to search for.
        location (str): The location to search in.

    Returns:
        str: The page source HTML of the search results, or None if an error occurs.
    """
    # Setup Chrome options
    chrome_options = Options()
    # To see what the browser is doing, comment out the line below
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    driver = None
    try:
        print("Setting up Selenium WebDriver...")
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # --- Step 1: Go to the homepage ---
        print("Navigating to Avvo homepage...")
        driver.get("https://www.avvo.com")
        
        # Wait for page to load
        time.sleep(3)

        # --- Step 2: Find input fields and type search terms ---
        wait = WebDriverWait(driver, 10)
        
        print("Finding search input fields...")
        
        # Try multiple strategies to find the search inputs
        try:
            # Strategy 1: Try by name attributes
            search_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            location_input = driver.find_element(By.NAME, "loc")
        except:
            try:
                # Strategy 2: Try by placeholder text
                search_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'legal issue') or contains(@placeholder, 'practice area')]")
                location_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'city') or contains(@placeholder, 'location') or contains(@placeholder, 'address')]")
            except:
                # Strategy 3: Try by common class names or IDs
                search_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']:first-of-type")
                location_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']:nth-of-type(2)")

        print(f"Typing '{search_query}' and '{location}' into fields...")
        search_input.clear()
        search_input.send_keys(search_query)
        location_input.clear()
        location_input.send_keys(location)
        
        # --- Step 3: Submit the search ---
        print("Submitting search...")
        
        # Try multiple ways to submit
        try:
            # Method 1: Look for any button with search-related text
            search_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Find') or contains(text(), 'Search') or contains(text(), 'Go')]")
            search_button.click()
        except:
            try:
                # Method 2: Look for submit button by type
                search_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                search_button.click()
            except:
                try:
                    # Method 3: Look for any clickable element with search icon
                    search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .search-button, .submit-button")
                    search_button.click()
                except:
                    # Method 4: Press Enter in the location field
                    print("Clicking search button failed, trying Enter key...")
                    location_input.send_keys(Keys.RETURN)
        
        # --- Step 4: Wait for results and get page source ---
        print("Waiting for search results page to load...")
        
        # Wait for URL change or results to appear
        time.sleep(5)  # Give it time to load
        
        # Check if we're on a results page
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        # Wait for lawyer cards or any results indicator
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa-id='lawyer-card'], .lawyer-card, .search-results, .results-list")))
        except:
            print("Warning: Could not find expected result elements, but continuing anyway...")

        print("Retrieving page source...")
        page_source = driver.page_source

        # --- DEBUGGING STEP ---
        screenshot_filename = "debug_screenshot.png"
        driver.save_screenshot(screenshot_filename)
        print(f"--> DEBUG: Screenshot saved to '{screenshot_filename}'")
        
        # Save HTML for debugging
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("--> DEBUG: Page HTML saved to 'debug_page.html'")
        # --- END DEBUGGING STEP ---

        return page_source
    except Exception as e:
        print(f"An error occurred with Selenium: {e}")
        if driver:
            error_screenshot_filename = "error_screenshot.png"
            driver.save_screenshot(error_screenshot_filename)
            print(f"--> DEBUG: Error screenshot saved to '{error_screenshot_filename}'")
            
            # Save error page HTML
            try:
                with open("error_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("--> DEBUG: Error page HTML saved to 'error_page.html'")
            except:
                pass
        return None
    finally:
        if driver:
            print("Closing the Selenium driver.")
            driver.quit()


def scrape_lawyers(search_query, location):
    """
    Scrapes lawyer data from a search results page using Selenium.

    Args:
        search_query (str): The practice area to search for (e.g., "Immigration").
        location (str): The location to search in (e.g., "New York").

    Returns:
        list: A list of dictionaries, where each dictionary represents a lawyer's profile.
    """

    # --- Step 1: Perform the interactive search ---
    html_content = perform_search_and_get_page_source(search_query, location)
    
    if not html_content:
        print("Failed to fetch page content with Selenium.")
        return []

    # --- Step 2: Parse the HTML ---
    soup = BeautifulSoup(html_content, 'html.parser')
    
    lawyers_data = []

    # --- Step 3: Find and Extract the Data ---
    # Check if this is a "no results" page
    no_results_indicators = soup.find_all(string=lambda text: text and any(phrase in text.lower() for phrase in [
        "try browsing in common practice areas",
        "no results found",
        "didn't find any lawyers",
        "are you a lawyer?"
    ]))
    
    if no_results_indicators:
        print("No lawyers found for this search. The search may be too specific.")
        print("Consider using broader search terms like 'Immigration' instead of 'EB-1 Visa'")
        return []
    
    # Try multiple selectors for lawyer cards
    lawyer_cards = soup.find_all('div', {'data-qa-id': 'lawyer-card'})
    
    if not lawyer_cards:
        # Try alternative selectors
        lawyer_cards = soup.find_all('div', class_='lawyer-card')
    
    if not lawyer_cards:
        # Try more generic selectors
        lawyer_cards = soup.find_all(['article', 'div'], class_=lambda x: x and ('lawyer' in x.lower() or 'attorney' in x.lower() or 'result' in x.lower()))

    print(f"Found {len(lawyer_cards)} lawyer profiles on the page.")

    if not lawyer_cards:
        print("No lawyer cards found. Checking for alternative formats...")
        
        # Look for lawyer profile links directly
        lawyer_links = soup.find_all('a', href=lambda x: x and ('/lawyer/' in x or '/professional/' in x))
        
        if lawyer_links:
            print(f"Found {len(lawyer_links)} lawyer profile links")
            # Try to extract basic info from links
            for link in lawyer_links[:10]:  # Limit to first 10
                try:
                    name = link.get_text(strip=True)
                    profile_link = link['href']
                    if not profile_link.startswith('http'):
                        profile_link = "https://www.avvo.com" + profile_link
                    
                    lawyers_data.append({
                        'Name': name,
                        'Profile Link': profile_link,
                        'Location': location,  # Use search location as default
                        'Avvo Rating': 'See profile',
                        'Details Snippet': 'Visit profile for details'
                    })
                except Exception as e:
                    continue
            return lawyers_data
        else:
            print("No lawyer profiles found on this page.")
            return []

    for card in lawyer_cards:
        try:
            # Extract Lawyer Name and Profile Link
            name_tag = card.find('a', {'data-qa-id': 'lawyer-name-link'})
            if not name_tag:
                # Try to find any link with attorney/lawyer in the href
                name_tag = card.find('a', href=lambda x: x and ('/attorneys/' in x or '/lawyer/' in x))
            if not name_tag:
                # Try finding h2, h3, or h4 tags with lawyer name
                name_tag = card.find(['h2', 'h3', 'h4'])
            
            name = name_tag.get_text(strip=True) if name_tag else "Name not found"
            
            # Extract profile link
            if name_tag and name_tag.name == 'a':
                profile_link = name_tag.get('href', 'Link not found')
            else:
                # If name wasn't in a link, find the profile link separately
                link_tag = card.find('a', href=lambda x: x and ('/attorneys/' in x or '/lawyer/' in x))
                profile_link = link_tag.get('href', 'Link not found') if link_tag else "Link not found"
            
            if profile_link != "Link not found" and not profile_link.startswith('http'):
                profile_link = "https://www.avvo.com" + profile_link

            # Extract Location
            location_tag = card.find('div', {'data-qa-id': 'lawyer-location'})
            if not location_tag:
                # Look for location in address or span tags
                location_tag = card.find(['address', 'span', 'div'], string=lambda x: x and (', ' in x and 
                    any(state in x for state in ['NY', 'New York', 'CA', 'FL', 'TX', 'PA', 'NJ'])))
            location_text = location_tag.get_text(strip=True) if location_tag else location

            # Extract Avvo Rating and Review Count
            rating_text = "Rating not found"
            review_count = ""
            
            # Look for rating spans
            rating_spans = card.find_all('span', class_=['sr-only', 'text-truncate'])
            for span in rating_spans:
                text = span.get_text(strip=True)
                if 'Avvo Rating' in text:
                    # Extract rating number
                    import re
                    rating_match = re.search(r'(\d+\.?\d*)', text)
                    if rating_match:
                        rating_text = rating_match.group(1)
                elif 'review' in text.lower():
                    review_count = f" ({text})"
            
            # Alternative: look for rating in strong tags
            if rating_text == "Rating not found":
                strong_tag = card.find('strong')
                if strong_tag:
                    rating_text = strong_tag.get_text(strip=True)
            
            full_rating = rating_text + review_count
            
            # Extract Snippet / Experience
            snippet_tag = card.find('div', {'data-qa-id': 'lawyer-snippet'})
            if not snippet_tag:
                # Look for practice areas or description
                snippet_tag = card.find(['p', 'div'], class_=lambda x: x and any(word in str(x).lower() 
                    for word in ['practice', 'area', 'description', 'experience', 'focus']))
            
            # If still not found, get any paragraph text
            if not snippet_tag:
                snippet_tag = card.find('p')
                
            experience_snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Licensed for X years"

            lawyers_data.append({
                'Name': name,
                'Profile Link': profile_link,
                'Location': location_text,
                'Avvo Rating': full_rating,
                'Details Snippet': experience_snippet
            })

        except Exception as e:
            print(f"Error parsing a lawyer card: {e}")
            continue
            
    return lawyers_data

def save_to_csv(data, filename="lawyers.csv"):
    """
    Saves the extracted lawyer data to a CSV file.

    Args:
        data (list): A list of lawyer dictionaries.
        filename (str): The name of the file to save the data to.
    """
    if not data:
        print("No data to save.")
        return

    fieldnames = data[0].keys()

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Data successfully saved to {filename}")

def scrape_lawyers_direct_url(practice_area_slug, location_slug):
    """
    Alternative approach: Navigate directly to practice area page.
    
    Args:
        practice_area_slug (str): URL slug for practice area (e.g., "immigration-lawyer")
        location_slug (str): URL slug for location (e.g., "ny/new_york")
    
    Returns:
        list: A list of lawyer dictionaries
    """
    url = f"https://www.avvo.com/{practice_area_slug}/{location_slug}.html"
    print(f"\nTrying direct URL approach: {url}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    
    driver = None
    try:
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Parse the page using the same extraction logic
        lawyers_data = []
        lawyer_cards = soup.find_all('div', {'data-qa-id': 'lawyer-card'})
        
        if not lawyer_cards:
            lawyer_cards = soup.find_all('div', class_='lawyer-card')
        
        print(f"Found {len(lawyer_cards)} lawyer profiles")
        
        for card in lawyer_cards:
            try:
                name_tag = card.find(['a', 'h2', 'h3'], class_=lambda x: x and 'lawyer' in x.lower())
                if not name_tag:
                    name_tag = card.find('a')
                
                name = name_tag.get_text(strip=True) if name_tag else "Name not found"
                profile_link = name_tag.get('href', 'Link not found') if name_tag else "Link not found"
                
                if profile_link != "Link not found" and not profile_link.startswith('http'):
                    profile_link = "https://www.avvo.com" + profile_link
                
                lawyers_data.append({
                    'Name': name,
                    'Profile Link': profile_link,
                    'Location': 'New York, NY',
                    'Avvo Rating': 'See profile',
                    'Details Snippet': 'Visit profile for details'
                })
            except Exception as e:
                print(f"Error parsing lawyer card: {e}")
                continue
                
        return lawyers_data
        
    except Exception as e:
        print(f"Error with direct URL approach: {e}")
        return []
    finally:
        if driver:
            driver.quit()


# --- Main execution block ---
if __name__ == "__main__":
    # Try a more common practice area that's likely to have results
    PRACTICE_AREA = "Immigration"  # Changed from "EB-1 Visa" to broader "Immigration"
    LOCATION = "New York, NY"

    print("Attempting search form approach...")
    scraped_data = scrape_lawyers(PRACTICE_AREA, LOCATION)

    if not scraped_data:
        print("\nSearch form approach didn't work. Trying direct URL approach...")
        # Try direct URL approach
        scraped_data = scrape_lawyers_direct_url("immigration-lawyer", "ny/new_york")
    
    if scraped_data:
        save_to_csv(scraped_data)
    else:
        print("\nScraping finished with no data.")
        print("\nAlternative: You can also try browsing lawyers directly:")
        print("- Immigration lawyers in NY: https://www.avvo.com/immigration-lawyer/ny/new_york.html")
        print("- All lawyers in NY: https://www.avvo.com/all-lawyers/ny/new_york.html")