from flask import Flask, jsonify, request
from flask_cors import CORS
import pyairbnb
import requests


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
            check_in,
            check_out,
            ne_lat,
            ne_long,
            sw_lat,
            sw_long,
            zoom_value,
            currency,
            "",
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
            listings_with_images.append(
                {
                    "id": listing.get("room_id"),
                    "name": listing.get("name"),
                    "url": f"https://www.airbnb.com/rooms/{listing.get('room_id')}",
                    "rating": listing.get("rating", {}).get("value", None),
                    "price": price_details.get("amount", None),
                    "room_type": listing.get("category"),
                    "image_urls": image_urls,
                }
            )

        return jsonify(listings_with_images)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# AI STUFF
# Claude API Implementation
import requests
import json

# Fixed Claude API implementation with accurate request format
import os
import requests
import traceback
from flask import jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
CLAUDE_API_KEY = os.getenv("API_KEY")

# Claude API configuration - Note the updated URL and headers
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


def analyze_sentiment_with_claude(review_text):
    if not CLAUDE_API_KEY:
        print("API Key is missing. Please check your .env file.")
        return "NEUTRAL"

    # Updated headers to match the correct format for Claude API
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
    }

    # Corrected payload structure for Claude API
    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "max_tokens": 10,
        "messages": [
            {
                "role": "user",
                "content": f'Analyze the sentiment of this Airbnb review. Respond with exactly one word - either POSITIVE, NEGATIVE, or NEUTRAL: "{review_text}"',
            }
        ],
        "temperature": 0,
    }

    try:
        # Print request details for debugging
        print(f"Sending request to Claude API with headers: {headers.keys()}")
        print(f"Payload: {payload}")

        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)

        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:200]}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return "NEUTRAL"

        result = response.json()
        print(f"JSON response keys: {result.keys()}")

        # Extract the content from the response
        if "content" in result and len(result["content"]) > 0:
            sentiment = result["content"][0].get("text", "").strip().upper()

            # Normalize the response
            if "POSITIVE" in sentiment:
                return "POSITIVE"
            elif "NEGATIVE" in sentiment:
                return "NEGATIVE"
            else:
                return "NEUTRAL"
        else:
            print("No content found in response")
            return "NEUTRAL"

    except Exception as e:
        print(f"Error in Claude sentiment analysis: {str(e)}")
        return "NEUTRAL"  # Default to neutral if there's an error


def extract_keywords_with_claude(review_text):
    if not CLAUDE_API_KEY:
        print("API Key is missing. Please check your .env file.")
        return []

    # Updated headers for Claude API
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
    }

    # Corrected payload for Claude API
    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": f'Extract 3-5 keywords from this Airbnb review about the location, amenities, or experience. Return ONLY the keywords separated by commas with no other text or explanation: "{review_text}"',
            }
        ],
        "temperature": 0,
    }

    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print(
                f"Error in keyword extraction: {response.status_code} - {response.text}"
            )
            return []

        result = response.json()

        # Extract content from response
        if "content" in result and len(result["content"]) > 0:
            keywords_text = result["content"][0].get("text", "").strip()

            # Clean up and split the keywords
            keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
            return keywords
        else:
            print("No content found in response")
            return []

    except Exception as e:
        print(f"Error in Claude keyword extraction: {str(e)}")
        return []  # Return empty list on error


# Updated version with better debugging
@app.route("/reviews", methods=["GET"])
def get_reviews():
    # Get listing URL and proxy URL
    room_url = request.args.get(
        "room_url", "https://www.airbnb.com/rooms/1244159884004281532"
    )
    proxy_url = request.args.get("proxy_url", "")

    try:
        reviews_data = pyairbnb.get_reviews(room_url, proxy_url)

        # Limit to first 5 reviews to avoid overloading the API
        reviews_to_process = reviews_data[:5] if len(reviews_data) > 5 else reviews_data

        results = []
        for review in reviews_to_process:
            comment = review.get("comments", "")
            if comment:
                # Add debugging
                print(f"Processing review: {comment[:50]}...")

                try:
                    sentiment = analyze_sentiment_with_claude(comment)
                    print(f"Sentiment result: {sentiment}")
                except Exception as e:
                    print(f"Sentiment analysis failed: {str(e)}")
                    sentiment = "NEUTRAL"

                try:
                    keywords = extract_keywords_with_claude(comment)
                    print(f"Keywords result: {keywords}")
                except Exception as e:
                    print(f"Keyword extraction failed: {str(e)}")
                    keywords = []

                results.append(
                    {"comment": comment, "sentiment": sentiment, "keywords": keywords}
                )

        return jsonify(results)

    except Exception as e:
        print(f"Error in get_reviews: {str(e)}")
        return jsonify({"error": str(e)}), 500


# # Test route to verify API connection
# @app.route('/test-claude-api', methods=['GET'])
# def test_claude_api():
#     test_review = "The location was perfect, close to the beach and restaurants. The apartment was clean and the host was very friendly and responsive."

#     try:
#         # Test API key
#         if not CLAUDE_API_KEY:
#             return jsonify({
#                 "error": "API key not found",
#                 "help": "Make sure you have an .env file with API_KEY set correctly"
#             }), 400

#         # Test API directly with minimal request
#         headers = {
#             'anthropic-version': '2023-06-01',
#             'content-type': 'application/json',
#             'x-api-key': CLAUDE_API_KEY
#         }

#         simple_payload = {
#             "model": "claude-3-7-sonnet-20250219",
#             "max_tokens": 10,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": "Say hello"
#                 }
#             ]
#         }

#         test_response = requests.post(CLAUDE_API_URL, headers=headers, json=simple_payload)

#         if test_response.status_code != 200:
#             return jsonify({
#                 "error": f"API test failed with status {test_response.status_code}",
#                 "details": test_response.text,
#                 "api_key_format": f"{CLAUDE_API_KEY[:5]}...{CLAUDE_API_KEY[-5:]}" if CLAUDE_API_KEY else None
#             }), 400

#         # Test sentiment and keywords
#         sentiment = analyze_sentiment_with_claude(test_review)
#         keywords = extract_keywords_with_claude(test_review)

#         return jsonify({
#             "status": "success",
#             "test_review": test_review,
#             "sentiment_result": sentiment,
#             "keywords_result": keywords,
#             "api_key_loaded": bool(CLAUDE_API_KEY),
#             "api_key_format": f"{CLAUDE_API_KEY[:5]}...{CLAUDE_API_KEY[-5:]}" if CLAUDE_API_KEY else None
#         })

#     except Exception as e:
#         return jsonify({
#             "error": str(e),
#             "trace": traceback.format_exc()
#         }), 500


# Updated recommend_listings function to use Claude API
@app.route("/recommend", methods=["GET"])
def recommend_listings():
    # Get user preferences from query parameters
    min_price = float(request.args.get("min_price", 0))
    max_price = float(request.args.get("max_price", 1000))

    # Get keywords as a comma-separated list and convert to lowercase for case-insensitive matching
    user_keywords_raw = request.args.get("keywords", "clean,quiet,spacious")
    user_keywords = [
        k.strip().lower() for k in user_keywords_raw.split(",") if k.strip()
    ]

    # Get search parameters (same as in search_airbnb function)
    check_in = request.args.get("check_in", "2025-06-01")
    check_out = request.args.get("check_out", "2025-06-04")
    currency = request.args.get("currency", "USD")

    # Location parameters (default to New York)
    ne_lat = float(request.args.get("ne_lat", 40.7808))
    ne_long = float(request.args.get("ne_long", -73.9653))
    sw_lat = float(request.args.get("sw_lat", 40.7308))
    sw_long = float(request.args.get("sw_long", -74.0005))
    zoom_value = int(request.args.get("zoom", 2))

    try:
        # Fetch Airbnb listings (reusing code from search_airbnb)
        search_results = pyairbnb.search_all(
            check_in,
            check_out,
            ne_lat,
            ne_long,
            sw_lat,
            sw_long,
            zoom_value,
            currency,
            "",
        )

        # Filter by price range first
        filtered_listings = []
        for listing in search_results:
            # Extract price and convert to float
            price = listing.get("price", {}).get("total", {}).get("amount", 0)
            if price is None:
                continue

            price = float(price)

            # Skip listings outside the price range
            if price < min_price or price > max_price:
                continue

            # Basic listing info
            listing_info = {
                "id": listing.get("room_id"),
                "name": listing.get("name"),
                "url": f"https://www.airbnb.com/rooms/{listing.get('room_id')}",
                "rating": listing.get("rating", {}).get("value", None),
                "price": price,
                "room_type": listing.get("category"),
                "image_urls": [image["url"] for image in listing.get("images", [])],
            }

            filtered_listings.append(listing_info)

        # List to store ranking results
        ranked_listings = []

        # Process up to 10 listings to avoid overloading
        listings_to_process = (
            filtered_listings[:10] if len(filtered_listings) > 10 else filtered_listings
        )

        # Score and rank each listing
        for listing in listings_to_process:
            try:
                # Get reviews for this listing
                room_url = f"https://www.airbnb.com/rooms/{listing['id']}"
                reviews_data = pyairbnb.get_reviews(room_url, "")

                # Process only first 3 reviews for efficiency
                reviews_to_process = (
                    reviews_data[:3] if len(reviews_data) > 3 else reviews_data
                )

                # Score this listing based on reviews
                sentiment_score = 0
                keyword_matches = 0
                review_count = 0

                for review in reviews_to_process:
                    comment = review.get("comments", "")
                    if not comment:
                        continue

                    review_count += 1

                    # Analyze sentiment using Claude
                    sentiment = analyze_sentiment_with_claude(comment)
                    # Add to sentiment score
                    if sentiment == "POSITIVE":
                        sentiment_score += 1
                    elif sentiment == "NEGATIVE":
                        sentiment_score -= 1

                    # Extract and match keywords using Claude
                    keywords = extract_keywords_with_claude(comment)
                    # Convert to lowercase for case-insensitive matching
                    keywords_lower = [k.lower() for k in keywords]

                    # Count matches with user keywords
                    for user_keyword in user_keywords:
                        for keyword in keywords_lower:
                            if user_keyword in keyword or keyword in user_keyword:
                                keyword_matches += 1
                                break

                # Calculate final score
                # If no reviews, give a neutral base score
                if review_count == 0:
                    final_score = 0
                else:
                    # Normalize sentiment score to range of -1 to 1
                    normalized_sentiment = sentiment_score / review_count

                    # Give more weight to keyword matches (multiply by 2)
                    final_score = (normalized_sentiment * 5) + (keyword_matches * 10)

                # Add to ranked listings
                ranked_listings.append(
                    {
                        "listing": listing,
                        "score": final_score,
                        "sentiment_score": sentiment_score,
                        "keyword_matches": keyword_matches,
                        "review_count": review_count,
                    }
                )

            except Exception as e:
                print(f"Error processing listing {listing['id']}: {str(e)}")
                # Still add the listing but with a low score
                ranked_listings.append(
                    {
                        "listing": listing,
                        "score": -100,  # Give a very low score to listings with errors
                        "error": str(e),
                    }
                )

        # Sort by score (highest first)
        ranked_listings = sorted(
            ranked_listings, key=lambda x: x["score"], reverse=True
        )

        # Return top 3 listings with their scores
        top_listings = (
            ranked_listings[:3] if len(ranked_listings) >= 3 else ranked_listings
        )

        # Format the response
        response = []
        for item in top_listings:
            listing_data = item["listing"]
            response.append(
                {
                    "id": listing_data["id"],
                    "name": listing_data["name"],
                    "url": listing_data["url"],
                    "price": listing_data["price"],
                    "rating": listing_data["rating"],
                    "image_urls": listing_data["image_urls"][
                        :1
                    ],  # Just the first image to keep response smaller
                    "score": item["score"],
                    "match_reasons": {
                        "sentiment_score": item.get("sentiment_score", 0),
                        "keyword_matches": item.get("keyword_matches", 0),
                    },
                }
            )

        return jsonify(
            {
                "results": response,
                "user_preferences": {
                    "price_range": {"min": min_price, "max": max_price},
                    "keywords": user_keywords,
                },
            }
        )

    except Exception as e:
        print(f"Error in recommend_listings: {str(e)}")
        return jsonify({"error": str(e)}), 500


from travel import scrape_momondo


@app.route("/api/search_flights", methods=["POST"])
def search_flights():
    data = request.json

    # Extract parameters from request
    try:
        leaving_airport = data.get("leaving_airport")
        destination_airport = data.get("destination_airport")
        departure_date = data.get("departure_date")
        return_date = data.get("return_date")
        num_adults = int(data.get("num_adults", 1))
        num_seniors = int(data.get("num_seniors", 0))
        num_students = int(data.get("num_students", 0))
        children_ages = data.get("children_ages", [])
        infants_on_seat = int(data.get("infants_on_seat", 0))
        infants_on_lap = int(data.get("infants_on_lap", 0))

        # Validate required fields
        if not all([leaving_airport, destination_airport, departure_date, return_date]):
            return jsonify({"error": "Missing required fields"}), 400

        # Call the scraper function
        result = scrape_momondo(
            leaving_airport=leaving_airport,
            destination_airport=destination_airport,
            departure_date=departure_date,
            return_date=return_date,
            num_adults=num_adults,
            num_seniors=num_seniors,
            num_students=num_students,
            children_ages=children_ages,
            infants_on_seat=infants_on_seat,
            infants_on_lap=infants_on_lap,
        )

        if result:
            return jsonify({"success": True, "booking_url": result})
        else:
            return jsonify({"success": False, "message": "No booking links found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ai_flight_search", methods=["POST"])
def ai_flight_search():
    # Get natural language query from request
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    if not CLAUDE_API_KEY:
        return jsonify({"error": "Missing API key configuration"}), 500

    # Set up Claude API request
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
    }

    # System prompt to guide Claude's extraction
    system_prompt = """
    Extract flight search parameters from the user's natural language query.
    Return a JSON object with the following fields (all lowercase):
    - leaving_airport: Airport code (3 letters, e.g., "JFK")
    - destination_airport: Airport code (3 letters, e.g., "LAX")
    - departure_date: In YYYY-MM-DD format
    - return_date: In YYYY-MM-DD format
    - num_adults: Integer (default to 1 if not specified)
    - num_seniors: Integer (default to 0 if not specified)
    - num_students: Integer (default to 0 if not specified)
    - children_ages: Array of integers representing ages 2-17 (default to empty array if not specified)
    - infants_on_seat: Integer (default to 0 if not specified)
    - infants_on_lap: Integer (default to 0 if not specified)
    
    If information is missing or unclear, make a reasonable assumption based on the query context.
    Only return the JSON object with no additional text.
    
    If the user provides city names instead of airport codes, use these common mappings:
    - New York: JFK (or LGA or EWR if context suggests)
    - Los Angeles: LAX
    - Chicago: ORD
    - London: LHR
    - Paris: CDG
    - Istanbul: IST
    - Miami: MIA
    - San Francisco: SFO
    - Tokyo: NRT
    - Dubai: DXB
    
    For dates specified as "next week", "next month", etc., calculate the actual dates based on today's date (consider today is the date this request is being processed).
    """

    # Construct the prompt that will be sent to Claude
    claude_payload = {
        "model": "claude-3-7-sonnet-20250219",
        "max_tokens": 500,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": f"Extract flight search parameters from this query: {query}",
            }
        ],
    }

    try:
        # Make request to Claude API
        response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_payload)

        if response.status_code != 200:
            print(f"Claude API error: {response.text}")
            return (
                jsonify({"error": f"AI processing error: {response.status_code}"}),
                500,
            )

        # Parse Claude's response
        result = response.json()

        if "content" not in result or len(result["content"]) == 0:
            return jsonify({"error": "Empty response from AI"}), 500

        # Extract JSON content from Claude's response
        ai_response = result["content"][0]["text"].strip()
        print(f"Claude extracted parameters: {ai_response}")

        try:
            # Parse the JSON content
            flight_params = json.loads(ai_response)

            # Validate required fields
            required_fields = [
                "leaving_airport",
                "destination_airport",
                "departure_date",
                "return_date",
            ]
            missing_fields = [
                field for field in required_fields if field not in flight_params
            ]

            if missing_fields:
                return (
                    jsonify(
                        {
                            "error": f"Missing required parameters: {', '.join(missing_fields)}"
                        }
                    ),
                    400,
                )

            # Now use the extracted parameters to call the flight search
            if "children_ages" not in flight_params:
                flight_params["children_ages"] = []

            # Set defaults
            flight_params.setdefault("num_adults", 1)
            flight_params.setdefault("num_seniors", 0)
            flight_params.setdefault("num_students", 0)
            flight_params.setdefault("infants_on_seat", 0)
            flight_params.setdefault("infants_on_lap", 0)

            # Convert airport codes to uppercase
            flight_params["leaving_airport"] = flight_params["leaving_airport"].upper()
            flight_params["destination_airport"] = flight_params[
                "destination_airport"
            ].upper()

            # Call the scraper function
            result = scrape_momondo(
                leaving_airport=flight_params["leaving_airport"],
                destination_airport=flight_params["destination_airport"],
                departure_date=flight_params["departure_date"],
                return_date=flight_params["return_date"],
                num_adults=flight_params["num_adults"],
                num_seniors=flight_params["num_seniors"],
                num_students=flight_params["num_students"],
                children_ages=flight_params["children_ages"],
                infants_on_seat=flight_params["infants_on_seat"],
                infants_on_lap=flight_params["infants_on_lap"],
            )

            if result:
                return jsonify(
                    {
                        "success": True,
                        "booking_url": result,
                        "extracted_params": flight_params,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "No booking links found",
                            "extracted_params": flight_params,
                        }
                    ),
                    404,
                )

        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse AI response"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
