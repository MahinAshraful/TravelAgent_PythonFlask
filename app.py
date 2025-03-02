
from flask import Flask, jsonify, request
from flask_cors import CORS
import pyairbnb

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello Mahin 2"})


@app.route("/search", methods=["GET"])
def search_airbnb():
    # Get search parameters
    check_in = request.args.get("check_in", "2025-06-01")
    check_out = request.args.get("check_out", "2025-06-04")
    currency = request.args.get("currency", "USD")

    # Get optional coordinates from request, else default to New York
    ne_lat = float(request.args.get("ne_lat", 40.7808))
    ne_long = float(request.args.get("ne_long", -73.9653))
    sw_lat = float(request.args.get("sw_lat", 40.7308))
    sw_long = float(request.args.get("sw_long", -74.0005))
    zoom_value = int(request.args.get("zoom", 2))

    # Get category preference (private room, entire home, or no preference)
    category = request.args.get("category", None)

    if not check_in or not check_out:
        return jsonify({"error": "Missing check-in or check-out dates"}), 400

    try:
        # Fetch Airbnb listings
        search_results = pyairbnb.search_all(
            check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, ""
        )

        listings_with_images = []
        for listing in search_results:
            # Check rating filter (>=4.3)
            if float(listing.get("rating", {}).get("value", 0)) < 4.3:
                continue  # Skip listings with low ratings

            # Check category filter (if set)
            if category and listing.get("category") != category:
                continue  # Skip listings that don’t match the user’s category preference

            # Extract image URLs
            image_urls = [image["url"] for image in listing.get("images", [])]

            # Extract price breakdown
            price_details = listing.get("price", {}).get("total", {})

            # Add listing with images & price breakdown to the result
            listings_with_images.append({
                "id": listing.get("room_id"),
                "name": listing.get("name"),
                "url": f"https://www.airbnb.com/rooms/{listing.get('room_id')}",
                "rating": listing.get("rating", {}).get("value", None),
                "price": price_details.get("amount", None),
                "room_type": listing.get("category"),
                "image_urls": image_urls
            })

        return jsonify(listings_with_images)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
