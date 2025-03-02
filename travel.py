from playwright.sync_api import sync_playwright
import time

def scrape_momondo(leaving_airport, destination_airport, departure_date, return_date):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True during production
        page = browser.new_page()
        
        # Navigate to initial page

        url = f"https://www.momondo.com/flight-search/{leaving_airport}-{destination_airport}/{departure_date}/{return_date}?ucs=ffm4n7&sort=bestflight_a"

        print(f"Navigating to: {url}")
        page.goto(url)
        
        # Wait for 7 seconds fir flights to load
        print("Waiting for 7 seconds...")
        time.sleep(7)
        
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
        second_result = result_items.nth(1) # second element
        
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

#test for JFK to DUB on 2025-04-17 to 2025-05-06
link = scrape_momondo("JFK", "DUB", "2025-04-17", "2025-05-06")
link = "https://momondo.com" + link

print('here is the link')
print(link)

#works => https://momondo.com/book/flight?code=qKBCS0Ci9u.BZRbXb2y98ZFj024N3_sTg.50941.ca21e4cb064b72435ac153efc02805fe&h=09f019ee0dcb&cookieOverrides=x06b3gGbCKIdLNRjjfxr1TnrpEYbiRLNyoc5Hv7mdZ_4NxfiBKyFP7pKK-HmqpN0JpyWY0jcT0q5bJIkZ9FD5Rk58xQzI6Rqyrf23bvb058VlR8g2OSIX0ZWvXH2fkEGtMpnI8mMwZuEbp_9CfEs9Q&_kykmc_=AatIsHETJ4YY6ZderrI_bLVqF-iNCbikesUa52IJDIS1YpjHJvtAtgDV-NPXs7PuVlCMh5Ts1yYKL7QvqHurBI5WDAHroFBySqY8v0gbQiC1ZB3yIivjMHGsdFXCk8z7vXuqt1nwNLRAhzK6sR0ZB1iG9Yipa4XQMuOxX_OjQadrbFQhvRUsH5XFeLj_zXrXbL5cREJqcMneqvPYBo3PO3V93IerBpstpomxxUFlFkEvq75Ig1s1bGKqlpmViIuI1cz44TV1ZLQCtRPqsvRn7BWKwKDhX_42IC7nJ3fl8cGVytmmPBnH5PxYe23CrWQjlQBtyQmwG1I2umKv_cZ1CPmkwUVgJzH1ejaRwxzYmVw6-ls0vrpP53gWOveaNy_8pRoO2CTCOXQb-D83DmaM1D7PT2dHyv8qKgGkL9egVyVI&sub=F-8454452798902130173E06661f1cc94&payment=0.00:USD:MC:Mastercard:false&bucket=DN&pageOrigin=F..RP.FE.M1