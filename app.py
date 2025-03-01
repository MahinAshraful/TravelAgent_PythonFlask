from flask import Flask, jsonify, request
from flask_cors import CORS
import pyairbnb

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello Mahin 2"})

#SEARCH AND FILTER THE JSON 
@app.route('/search', methods=['GET'])
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





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
