from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time


def scrape_momondo(
    leaving_airport,
    destination_airport,
    departure_date,
    return_date,
    num_adults=1,
    num_seniors=0,
    num_students=0,
    children_ages=None,
    infants_on_seat=0,
    infants_on_lap=0,
):
    with sync_playwright() as p:
        # Set up browser with a more realistic configuration for headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # Build the passenger portion of the URL
        passenger_parts = []
        passenger_parts.append(f"{num_adults}adults")
        if num_seniors > 0:
            passenger_parts.append(f"{num_seniors}seniors")
        if num_students > 0:
            passenger_parts.append(f"{num_students}students")

        children_components = []
        if infants_on_seat > 0:
            children_components.append(f"{infants_on_seat}S")
        if infants_on_lap > 0:
            children_components.append(f"{infants_on_lap}L")
        if children_ages and len(children_ages) > 0:
            children_components.extend([str(age) for age in children_ages])

        if children_components:
            children_str = "children-" + "-".join(children_components)
            passenger_parts.append(children_str)

        passenger_string = "/".join(passenger_parts)
        url = f"https://www.momondo.com/flight-search/{leaving_airport}-{destination_airport}/{departure_date}/{return_date}/{passenger_string}?ucs=ffm4n7&sort=bestflight_a"

        try:
            print(f"Navigating to: {url}")
            # Increase timeout for initial page load
            page.goto(url, timeout=60000)

            # Wait longer for page to fully load
            print("Waiting for page to load completely...")
            time.sleep(10)

            try:
                # Try to click the "Cheapest" option if available
                print("Looking for 'Cheapest' option...")
                if page.locator('div[aria-label="Cheapest"]').count() > 0:
                    page.locator('div[aria-label="Cheapest"]').click(timeout=5000)
                    print("Clicked 'Cheapest' option")
                    time.sleep(3)
                else:
                    print("Cheapest option not found, using default sorting")
            except Exception as e:
                print(f"Note: Could not click Cheapest option: {e}")
                # Continue with default sorting

            # Wait for any potential updates to complete
            print("Looking for booking links...")
            page.wait_for_selector('a[href^="/book"]', timeout=10000, state="attached")

            # Find the first booking link
            booking_links = page.locator('a[href^="/book"]')

            if booking_links.count() == 0:
                print("No booking links found!")
                return None

            href = booking_links.first.get_attribute("href")
            print(f"Found booking link: {href}")

            # Create the full URL
            full_url = "https://momondo.com" + href

            # Follow the redirect in a new page
            print("Following redirect...")
            new_page = context.new_page()
            new_page.goto(full_url, timeout=60000)

            # Wait for redirects to complete
            print("Waiting for redirect to complete...")
            new_page.wait_for_load_state("networkidle", timeout=30000)

            # Get the final URL
            final_url = new_page.url
            print(f"Final URL after redirect: {final_url}")

            # Clean up
            browser.close()
            return final_url

        except Exception as e:
            print(f"Error during scraping: {e}")
            browser.close()
            return None
