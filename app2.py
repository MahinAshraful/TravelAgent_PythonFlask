from flask import Flask, jsonify, request
from flask_cors import CORS
import pyairbnb
import requests
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Get API key from environment variables
CLAUDE_API_KEY = os.getenv("API_KEY")

# Claude API configuration
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Airport to coordinate mapping (simplified for common destinations)
# Format: [ne_lat, ne_long, sw_lat, sw_long, city_name]
# Using wider coordinate ranges to ensure we capture more Airbnb listings
AIRPORT_COORDINATES = {
    "JFK": [40.8508, -73.8553, 40.6308, -74.0505, "New York"],
    "LAX": [34.1522, -118.1437, 33.9422, -118.4537, "Los Angeles"],
    "ORD": [42.0781, -87.5298, 41.7681, -87.8398, "Chicago"],
    "LHR": [51.6074, -0.0278, 51.3974, -0.2378, "London"],
    "CDG": [48.9566, 2.4522, 48.7466, 2.2422, "Paris"],
    "IST": [41.1082, 29.0784, 40.8982, 28.8684, "Istanbul"],
    "MIA": [25.8617, -80.0918, 25.6517, -80.3018, "Miami"],
    "SFO": [37.8749, -122.3194, 37.6649, -122.5294, "San Francisco"],
    "NRT": [35.7762, 139.7503, 35.5662, 139.5403, "Tokyo"],
    "DXB": [25.3048, 55.3708, 25.0948, 55.1608, "Dubai"],
    # Add more airports as needed
}

# Default coordinates (New York) if airport not found
DEFAULT_COORDINATES = [40.7808, -73.9653, 40.7308, -74.0005, "New York"]


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

    # Payload structure for Claude API
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
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return "NEUTRAL"

        result = response.json()

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
    """
    Extract keywords from a review text using Claude API.
    Falls back to basic extraction if API fails.
    """
    if not CLAUDE_API_KEY:
        print("API Key is missing. Using fallback keyword extraction.")
        return fallback_keyword_extraction(review_text)

    # Updated headers for Claude API
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
    }

    # Payload for Claude API
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
            print(f"Error in keyword extraction: {response.status_code} - {response.text}")
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
        return fallback_keyword_extraction(review_text)  # Use fallback method
        
        
def fallback_keyword_extraction(review_text):
    """
    Simple keyword extraction fallback when Claude API is unavailable.
    Uses common amenity keywords for Airbnb listings.
    """
    common_keywords = [
        "clean", "spacious", "comfortable", "quiet", "view", "location", 
        "convenient", "modern", "cozy", "pool", "beach", "kitchen", 
        "bathroom", "bedroom", "host", "communication", "check-in", 
        "parking", "wifi", "amenities", "restaurants", "transportation",
        "downtown", "private", "safe", "value", "price", "luxury"
    ]
    
    # Convert review to lowercase for case-insensitive matching
    review_lower = review_text.lower()
    
    # Find keywords that appear in the review
    found_keywords = []
    for keyword in common_keywords:
        if keyword in review_lower:
            found_keywords.append(keyword)
    
    # Return at most 5 keywords
    return found_keywords[:5]


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
    
    For dates specified as "next week", "next month", etc., calculate the actual dates based on today's date (it is 03/02/2025).
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
                    404
                )

        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse AI response"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/integrated_travel_search", methods=["POST"])
def integrated_travel_search():
    """
    Integrated endpoint that takes a natural language query,
    extracts flight information, finds the best flight,
    and recommends Airbnb listings at the destination.
    """
    data = request.json
    query = data.get("query")
    
    # Optional filters for Airbnb
    min_price = float(data.get("min_price", 0))
    max_price = float(data.get("max_price", 1000))
    keywords = data.get("keywords", "clean,comfortable,convenient")
    
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    if not CLAUDE_API_KEY:
        return jsonify({"error": "Missing API key configuration"}), 500

    # 1. Extract flight search parameters using Claude
    flight_params = extract_flight_params(query)
    if "error" in flight_params:
        return jsonify(flight_params), 400

    # 2. Find flight using Momondo
    try:
        flight_result = scrape_momondo(
            leaving_airport=flight_params["leaving_airport"],
            destination_airport=flight_params["destination_airport"],
            departure_date=flight_params["departure_date"],
            return_date=flight_params["return_date"],
            num_adults=flight_params.get("num_adults", 1),
            num_seniors=flight_params.get("num_seniors", 0),
            num_students=flight_params.get("num_students", 0),
            children_ages=flight_params.get("children_ages", []),
            infants_on_seat=flight_params.get("infants_on_seat", 0),
            infants_on_lap=flight_params.get("infants_on_lap", 0),
        )
    except Exception as e:
        print(f"Error scraping Momondo: {str(e)}")
        flight_result = None

    # 3. Get destination coordinates from airport code
    destination_code = flight_params["destination_airport"]
    
    if destination_code in AIRPORT_COORDINATES:
        ne_lat, ne_long, sw_lat, sw_long, destination_name = AIRPORT_COORDINATES[destination_code]
    else:
        ne_lat, ne_long, sw_lat, sw_long, destination_name = DEFAULT_COORDINATES
        print(f"Warning: No coordinates found for airport {destination_code}, using default.")
    
    # 4. Search for Airbnb listings at the destination
    try:
        # Add a fallback mechanism in case the first search returns no results
        # First try with the exact coordinates from the airport mapping
        print("Attempting first Airbnb search with exact coordinates...")
        airbnb_results = search_and_rank_airbnbs(
            check_in=flight_params["departure_date"],
            check_out=flight_params["return_date"],
            ne_lat=ne_lat,
            ne_long=ne_long,
            sw_lat=sw_lat,
            sw_long=sw_long,
            min_price=min_price,
            max_price=max_price,
            keywords=keywords
        )
        
        # If no results found, try with a wider search area
        if not airbnb_results.get("results") and not airbnb_results.get("error"):
            print("No results found. Attempting second Airbnb search with wider area...")
            # Calculate wider coordinates (approximately doubling the search area)
            center_lat = (ne_lat + sw_lat) / 2
            center_long = (ne_long + sw_long) / 2
            lat_radius = abs(ne_lat - sw_lat) * 2
            long_radius = abs(ne_long - sw_long) * 2
            
            wider_ne_lat = center_lat + lat_radius
            wider_ne_long = center_long + long_radius
            wider_sw_lat = center_lat - lat_radius
            wider_sw_long = center_long - long_radius
            
            airbnb_results = search_and_rank_airbnbs(
                check_in=flight_params["departure_date"],
                check_out=flight_params["return_date"],
                ne_lat=wider_ne_lat,
                ne_long=wider_ne_long,
                sw_lat=wider_sw_lat,
                sw_long=wider_sw_long,
                min_price=min_price,
                max_price=max_price,
                keywords=keywords
            )
    except Exception as e:
        print(f"Error searching Airbnb: {str(e)}")
        airbnb_results = {"error": str(e), "message": "Failed to search for Airbnb listings"}
    
    # 5. Combine results and return
    return jsonify({
        "flight": {
            "success": flight_result is not None,
            "booking_url": flight_result if flight_result else None,
            "params": flight_params
        },
        "destination": {
            "name": destination_name,
            "airport_code": destination_code,
            "coordinates": {
                "ne_lat": ne_lat,
                "ne_long": ne_long,
                "sw_lat": sw_lat,
                "sw_long": sw_long
            }
        },
        "accommodations": airbnb_results
    })


def extract_flight_params(query):
    """Helper function to extract flight parameters from natural language query"""
    if not CLAUDE_API_KEY:
        return {"error": "Missing API key configuration"}

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
    
    For dates specified as "next week", "next month", etc., calculate the actual dates based on today's date (it is 03/02/2025).
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
            return {"error": f"AI processing error: {response.status_code}"}

        # Parse Claude's response
        result = response.json()

        if "content" not in result or len(result["content"]) == 0:
            return {"error": "Empty response from AI"}

        # Extract JSON content from Claude's response
        ai_response = result["content"][0]["text"].strip()
        
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
                return {"error": f"Missing required parameters: {', '.join(missing_fields)}"}

            # Set defaults
            if "children_ages" not in flight_params:
                flight_params["children_ages"] = []
                
            flight_params.setdefault("num_adults", 1)
            flight_params.setdefault("num_seniors", 0)
            flight_params.setdefault("num_students", 0)
            flight_params.setdefault("infants_on_seat", 0)
            flight_params.setdefault("infants_on_lap", 0)

            # Convert airport codes to uppercase
            flight_params["leaving_airport"] = flight_params["leaving_airport"].upper()
            flight_params["destination_airport"] = flight_params["destination_airport"].upper()

            return flight_params

        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}

    except Exception as e:
        return {"error": str(e)}


def search_and_rank_airbnbs(check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, min_price=0, max_price=1000, keywords="clean,convenient,comfortable"):
    """Helper function to search and rank Airbnb listings"""
    currency = "USD"
    zoom_value = 15  # Using a higher zoom value for better results
    
    # Convert keywords to list if string
    if isinstance(keywords, str):
        user_keywords = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    else:
        user_keywords = [k.strip().lower() for k in keywords if k.strip()]
    
    # Debug information    
    print(f"Searching Airbnb with coordinates: NE({ne_lat}, {ne_long}), SW({sw_lat}, {sw_long})")
    print(f"Date range: {check_in} to {check_out}")
    print(f"Price range: ${min_price} - ${max_price}")
    print(f"Keywords: {user_keywords}")
        
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
        
        # Debug information
        print(f"Found {len(search_results)} Airbnb listings in the area")

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

        # Debug information
        print(f"After price filtering: {len(filtered_listings)} listings remain")
        
        # If no listings were found after filtering, return early with informative message
        if len(filtered_listings) == 0:
            return {
                "results": [],
                "user_preferences": {
                    "price_range": {"min": min_price, "max": max_price},
                    "keywords": user_keywords,
                },
                "message": "No Airbnb listings found in this area matching your price range. Try expanding your search criteria."
            }
            
        # Process up to 10 listings to avoid overloading
        listings_to_process = (
            filtered_listings[:10] if len(filtered_listings) > 10 else filtered_listings
        )

        # Score and rank each listing
        for listing in listings_to_process:
            try:
                # Get reviews for this listing
                try:
                    room_url = f"https://www.airbnb.com/rooms/{listing['id']}"
                    reviews_data = pyairbnb.get_reviews(room_url, "")
                    print(f"Successfully retrieved {len(reviews_data)} reviews for listing {listing['id']}")
                except Exception as review_error:
                    print(f"Error retrieving reviews for listing {listing['id']}: {str(review_error)}")
                    reviews_data = []

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
                    "image_urls": listing_data["image_urls"][:1],  # Just the first image
                    "score": item["score"],
                    "match_reasons": {
                        "sentiment_score": item.get("sentiment_score", 0),
                        "keyword_matches": item.get("keyword_matches", 0),
                    },
                }
            )

        return {
            "results": response,
            "user_preferences": {
                "price_range": {"min": min_price, "max": max_price},
                "keywords": user_keywords,
            },
        }

    except Exception as e:
        print(f"Error in search_and_rank_airbnbs: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)