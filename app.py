
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


#GET THE COMMENTS in reviews and put it in the list
# @app.route('/reviews', methods=['GET'])
# def get_reviews():
#     # Get listing URL and proxy URL
#     room_url = request.args.get("room_url", "https://www.airbnb.com/rooms/1244159884004281532")
#     proxy_url = request.args.get("proxy_url", "")

#     try:
#         reviews_data = pyairbnb.get_reviews(room_url, proxy_url)
#         comments = [review.get("comments", "") for review in reviews_data]

#         return jsonify(comments)
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



#AI STUFF
# Corrected Groq API implementation
import requests

GROQ_API_KEY = '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'  # Replace with your Groq API key
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'



def analyze_sentiment_with_groq(review_text):
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": "llama3-70b-8192",  # Or another model Groq supports
        "messages": [
            {"role": "system", "content": "You are a sentiment analysis assistant. Classify the sentiment as POSITIVE, NEGATIVE, or NEUTRAL. Reply with just one word."},
            {"role": "user", "content": f"Analyze the sentiment of this review: {review_text}"}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()
        sentiment = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip().upper()
        
        # Normalize the response to ensure it's one of our expected values
        if 'POSITIVE' in sentiment:
            return 'POSITIVE'
        elif 'NEGATIVE' in sentiment:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        return 'NEUTRAL'  # Default to neutral if there's an error




def extract_keywords_with_groq(review_text):
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": "llama3-70b-8192",  # Or another model Groq supports
        "messages": [
            {"role": "system", "content": "Extract at most 5 important keywords from the review. Respond with just the keywords separated by commas, no additional text. Think of things people want to hear about a listing when going on a trip."},
            {"role": "user", "content": review_text}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        keywords_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        # Clean up and split the keywords
        keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        return keywords
    except Exception as e:
        print(f"Error in keyword extraction: {str(e)}")
        return []  # Return empty list on error




@app.route('/reviews', methods=['GET'])
def get_reviews():
    # Get listing URL and proxy URL
    room_url = request.args.get("room_url", "https://www.airbnb.com/rooms/1244159884004281532")
    proxy_url = request.args.get("proxy_url", "")

    try:
        reviews_data = pyairbnb.get_reviews(room_url, proxy_url)
        
        # Limit to first 5 reviews to avoid overloading the API
        reviews_to_process = reviews_data[:5] if len(reviews_data) > 5 else reviews_data
        
        results = []
        for review in reviews_to_process:
            comment = review.get("comments", "")
            if comment:
                sentiment = analyze_sentiment_with_groq(comment)
                keywords = extract_keywords_with_groq(comment)
                results.append({
                    "comment": comment,
                    "sentiment": sentiment,
                    "keywords": keywords
                })

        return jsonify(results)
    
    except Exception as e:
        print(f"Error in get_reviews: {str(e)}")
        return jsonify({"error": str(e)}), 500

# def rank_listings(listings, reviews, user_keywords):
#     ranked_listings = []

#     for listing in listings:
#         review = reviews.get(listing["id"])  # Get reviews for the listing
#         if review:
#             sentiment = analyze_sentiment_with_groq(review)
#             keywords = extract_keywords_with_groq(review)

#             sentiment_score = 1 if sentiment == "positive" else -1 if sentiment == "negative" else 0
#             # Compare keywords with user preferences (user_keywords is a list of keywords they care about)
#             matched_keywords = [kw for kw in keywords if kw in user_keywords]
#             score = len(matched_keywords) + sentiment_score  # A basic score combining sentiment and keyword relevance
#             ranked_listings.append({"listing_id": listing["id"], "score": score})

#     # Sort listings by score (higher score = better match)
#     ranked_listings = sorted(ranked_listings, key=lambda x: x["score"], reverse=True)
#     # return ranked_listings[:5]  # Top 5 listings
#     print(ranked_listings[:5]) 

@app.route('/recommend', methods=['GET'])
def recommend_listings():
    # Get user preferences from query parameters
    min_price = float(request.args.get("min_price", 0))
    max_price = float(request.args.get("max_price", 1000))
    
    # Get keywords as a comma-separated list and convert to lowercase for case-insensitive matching
    user_keywords_raw = request.args.get("keywords", "[\"clean\", \"quiet\", \"spacious\"]")
    user_keywords = [k.strip().lower() for k in user_keywords_raw.split(',') if k.strip()]
    
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
            check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, ""
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
                "image_urls": [image["url"] for image in listing.get("images", [])]
            }
            
            filtered_listings.append(listing_info)
        
        # List to store ranking results
        ranked_listings = []
        
        # Process up to 10 listings to avoid overloading
        listings_to_process = filtered_listings[:10] if len(filtered_listings) > 10 else filtered_listings
        
        # Score and rank each listing
        for listing in listings_to_process:
            try:
                # Get reviews for this listing
                room_url = f"https://www.airbnb.com/rooms/{listing['id']}"
                reviews_data = pyairbnb.get_reviews(room_url, "")
                
                # Process only first 3 reviews for efficiency
                reviews_to_process = reviews_data[:3] if len(reviews_data) > 3 else reviews_data
                
                # Score this listing based on reviews
                sentiment_score = 0
                keyword_matches = 0
                review_count = 0
                
                for review in reviews_to_process:
                    comment = review.get("comments", "")
                    if not comment:
                        continue
                        
                    review_count += 1
                    
                    # Analyze sentiment
                    sentiment = analyze_sentiment_with_groq(comment)
                    # Add to sentiment score
                    if sentiment == "POSITIVE":
                        sentiment_score += 1
                    elif sentiment == "NEGATIVE":
                        sentiment_score -= 1
                    
                    # Extract and match keywords
                    keywords = extract_keywords_with_groq(comment)
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
                ranked_listings.append({
                    "listing": listing,
                    "score": final_score,
                    "sentiment_score": sentiment_score,
                    "keyword_matches": keyword_matches,
                    "review_count": review_count
                })
                
            except Exception as e:
                print(f"Error processing listing {listing['id']}: {str(e)}")
                # Still add the listing but with a low score
                ranked_listings.append({
                    "listing": listing,
                    "score": -100,  # Give a very low score to listings with errors
                    "error": str(e)
                })
        
        # Sort by score (highest first)
        ranked_listings = sorted(ranked_listings, key=lambda x: x["score"], reverse=True)
        
        # Return top 3 listings with their scores
        top_listings = ranked_listings[:3] if len(ranked_listings) >= 3 else ranked_listings
        
        # Format the response
        response = []
        for item in top_listings:
            listing_data = item["listing"]
            response.append({
                "id": listing_data["id"],
                "name": listing_data["name"],
                "url": listing_data["url"],
                "price": listing_data["price"],
                "rating": listing_data["rating"],
                "image_urls": listing_data["image_urls"][:1],  # Just the first image to keep response smaller
                "score": item["score"],
                "match_reasons": {
                    "sentiment_score": item.get("sentiment_score", 0),
                    "keyword_matches": item.get("keyword_matches", 0)
                }
            })
        
        return jsonify({
            "results": response,
            "user_preferences": {
                "price_range": {"min": min_price, "max": max_price},
                "keywords": user_keywords
            }
        })
        
    except Exception as e:
        print(f"Error in recommend_listings: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)