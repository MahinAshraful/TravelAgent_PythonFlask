from playwright.sync_api import sync_playwright
import time

def scrape_momondo(leaving_airport, destination_airport, departure_date, return_date, num_adults=1, num_seniors=0, num_students=0, children_ages=None, infants_on_seat=0, infants_on_lap=0):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True during production
        page = browser.new_page()
        
        # Build the passenger portion of the URL
        passenger_parts = []
        
        # Always include adults (with default of 1 if not specified)
        passenger_parts.append(f"{num_adults}adults")
        
        # Only add seniors and students if they're greater than 0
        if num_seniors > 0:
            passenger_parts.append(f"{num_seniors}seniors")
        
        if num_students > 0:
            passenger_parts.append(f"{num_students}students")
        
        # Handle all children types in the correct format
        children_components = []
        
        # Add infants on seat if any
        if infants_on_seat > 0:
            children_components.append(f"{infants_on_seat}S")
            
        # Add infants on lap if any
        if infants_on_lap > 0:
            children_components.append(f"{infants_on_lap}L")
        
        # Add regular children's ages
        if children_ages and len(children_ages) > 0:
            children_components.extend([str(age) for age in children_ages])
        
        # Only add the children part if there are any child passengers
        if children_components:
            children_str = "children-" + "-".join(children_components)
            passenger_parts.append(children_str)
        
        # Join the passenger parts with slashes
        passenger_string = "/".join(passenger_parts)
        
        # Construct the full URL
        url = f"https://www.momondo.com/flight-search/{leaving_airport}-{destination_airport}/{departure_date}/{return_date}/{passenger_string}?ucs=ffm4n7&sort=bestflight_a"
          
        print(f"Navigating to: {url}")
        page.goto(url)
        
        # Wait for 7 seconds for flights to load
        print("Waiting for 7 seconds...")
        time.sleep(7)
        
        # Find and click the "Cheapest" div
        print("Looking for 'Cheapest' option...")
        cheapest_button = page.locator('div[aria-label="Cheapest"]')
        cheapest_button.click()
        
        # Wait for the results to update after clicking
        print("Waiting for results to update...")
        page.wait_for_timeout(3000)  # Wait additional 3 seconds for results to refresh
        
        # Find the first link that starts with "/book"
        print("Finding the first booking link...")
        booking_links = page.locator('a[href^="/book"]')
        first_booking_link = booking_links.first
        
        # Get the href attribute
        href = first_booking_link.get_attribute('href')
        print(f"Found booking link: {href}")
        
        # Close the browser
        browser.close()
        
        return href

# Test for JFK to DUB on 2025-04-17 to 2025-05-06
link = scrape_momondo(
    "JFK", "IST", "2025-04-17", "2025-05-06",
    num_adults=1,
    num_seniors=1,
    num_students=1,
    children_ages=[11, 17, 17, 17],  # One child age 2-11 and three children age 12-17
    infants_on_seat=1,  # One infant on seat
    infants_on_lap=1    # One infant on lap
)
link = "https://momondo.com" + link

print('here is the link')
print(link)