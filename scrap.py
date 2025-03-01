from flask import Flask, jsonify, request
import pyairbnb

scrap = Flask(__name__)

@scrap.route('/search', methods=['GET'])
def search_airbnb():
    # Get search parameters from query string
    check_in = request.args.get("check_in", '2025-06-01')
    check_out = request.args.get("check_out", '2025-06-04')
    currency = request.args.get("currency", "USD")

    # Get optional coordinates from request, else default to New York
    ne_lat = float(request.args.get("ne_lat", 40.7808))
    ne_long = float(request.args.get("ne_long", -73.9653))
    sw_lat = float(request.args.get("sw_lat", 40.7308))
    sw_long = float(request.args.get("sw_long", -74.0005))
    zoom_value = int(request.args.get("zoom", 2))

    if not check_in or not check_out:
        return jsonify({"error": "Missing check-in or check-out dates"}), 400

    try:
        search_results = pyairbnb.search_all(check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, "")

        # Filter results: only keep listings with rating >= 4.3
        filtered_results = [listing for listing in search_results if float(listing.get("rating", {}).get("value", 0)) >= 4.5]

        return jsonify(filtered_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @scrap.route('/scrape', methods=['GET'])
# def scrape_airbnb():
#     # Get listing URL and dates from query string
#     room_url = request.args.get("room_url", "https://www.airbnb.com/rooms/1244159884004281532")
#     check_in = request.args.get("check_in", '2025-06-01')
#     check_out = request.args.get("check_out", '2025-06-04')
#     currency = request.args.get("currency", "USD")

#     if not room_url or not check_in or not check_out:
#         return jsonify({"error": "Missing required parameters: room_url, check_in, or check_out"}), 400

#     proxy_url = ""

#     try:
#         # Get metadata and price information
#         data, price_input, cookies = pyairbnb.get_metadata_from_url(room_url, proxy_url)
#         product_id = price_input["product_id"]
#         api_key = price_input["api_key"]

#         # Fetch price details dynamically
#         price_data = pyairbnb.get_price(
#             product_id, price_input["impression_id"], api_key, currency, cookies, check_in, check_out, proxy_url
#         )

#         return jsonify(price_data)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    scrap.run(debug=True)
