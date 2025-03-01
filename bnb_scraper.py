import pyairbnb
import json

# Define search parameters
currency = "USD"
check_in = "2025-04-10"
check_out = "2025-04-12"
ne_lat = 40.7808  # Example: North-East latitude (New York)
ne_long = -73.9653
sw_lat = 40.7308  # Example: South-West latitude (New York)
sw_long = -74.0005
zoom_value = 2

# Perform search
search_results = pyairbnb.search_all(check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, "")

# Save results
with open("search_results.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(search_results))

print("Search results saved to search_results.json")