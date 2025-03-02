from playwright.sync_api import sync_playwright
import time

def scrape_momondo(leaving_airport, destination_airport, departure_date, return_date):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for production
        page = browser.new_page()
        
        # Navigate to the Momondo flight search page

        url = f"https://www.momondo.com/flight-search/{leaving_airport}-{destination_airport}/{departure_date}/{return_date}?ucs=ffm4n7&sort=bestflight_a"

        print(f"Navigating to: {url}")
        page.goto(url)
        
        # Wait for 5 seconds as required
        print("Waiting for 5 seconds...")
        time.sleep(5)
        
        # Find and click the "Cheapest" div
        print("Looking for 'Cheapest' option...")
        cheapest_button = page.locator('div[aria-label="Cheapest"]')
        cheapest_button.click()
        
        # Wait for the results to update after clicking
        print("Waiting for results to update...")
        page.wait_for_timeout(3000)  # Wait additional 3 seconds for results to refresh
        
        # Find the second div with class "Fxw9-result-item-container"
        print("Finding the second flight result item...")
        result_items = page.locator('div.Fxw9-result-item-container')
        second_result = result_items.nth(1)  # 0-based indexing, so 1 is the second element
        
        # Find the price section within that result
        print("Finding price section within the result...")
        price_section = second_result.locator('div.nrc6-price-section')
        
        # Find all links within the price section and get the first one
        print("Extracting the first link...")
        links = price_section.locator('a[role="link"]')
        # Use first() to get the first element in the list
        first_link = links.first
        href = first_link.get_attribute('href')
        print(f"Full link URL: {href}")
        
        print(f"\nExtracted link: {href}")
        
        # Close the browser
        browser.close()
        
        return href


link = scrape_momondo("JFK", "DUB", "2025-04-17", "2025-05-06")
link = "momondo.com" + link

print('here is the link')
print(link)