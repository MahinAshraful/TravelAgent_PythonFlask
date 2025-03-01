from flask import Flask, jsonify, request
import pyairbnb

scrap = Flask(__name__)

@scrap.route('/search', methods=['GET'])
def search_airbnb():
    check_in = request.args.get("check_in", "2025-04-10")
    check_out = request.args.get("check_out", "2025-04-12")
    currency = request.args.get("currency", "USD")

    # Example coordinates (New York)
    ne_lat, ne_long = 40.7808, -73.9653
    sw_lat, sw_long = 40.7308, -74.0005
    zoom_value = 2

    search_results = pyairbnb.search_all(check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, "")

    return jsonify(search_results)

@scrap.route('/price', methods=['GET'])
def scrape_airbnb():
    room_url = "https://www.airbnb.com/rooms/1244159884004281532"
    check_in = "2025-04-10"
    check_out = "2025-04-12"
    proxy_url = ""

    try:
        # Get metadata and price information
        data, price_input, cookies = pyairbnb.get_metadata_from_url(room_url, proxy_url)
        product_id = price_input["product_id"]
        api_key = price_input["api_key"]
        currency = "USD"
        
        # Fetch price details
        price_data = pyairbnb.get_price(
            product_id, price_input["impression_id"], api_key, currency, cookies, check_in, check_out, proxy_url
        )

        return jsonify(price_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    scrap.run(debug=True)
