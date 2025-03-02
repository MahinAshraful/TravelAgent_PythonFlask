# from flask import Flask, jsonify, request
# from flask_cors import CORS
# import pyairbnb

# app = Flask(__name__)
# CORS(app)


# @app.route("/")
# def hello_world():
#     return jsonify({"message": "Hello Mahin 2"})

# #SEARCH AND FILTER THE JSON 
# @app.route('/search', methods=['GET'])
# def search_airbnb():
#     # Get search parameters from query string
#     check_in = request.args.get("check_in", '2025-06-01')
#     check_out = request.args.get("check_out", '2025-06-04')
#     currency = request.args.get("currency", "USD")

#     # Get optional coordinates from request, else default to New York
#     ne_lat = float(request.args.get("ne_lat", 40.7808))
#     ne_long = float(request.args.get("ne_long", -73.9653))
#     sw_lat = float(request.args.get("sw_lat", 40.7308))
#     sw_long = float(request.args.get("sw_long", -74.0005))
#     zoom_value = int(request.args.get("zoom", 2))

#     #optional private_room or entire home
#     #change the default to empty string if no preference
#     category = request.args.get("category", '')


#     if not check_in or not check_out:
#         return jsonify({"error": "Missing check-in or check-out dates"}), 400

#     try:
#         search_results = pyairbnb.search_all(check_in, check_out, ne_lat, ne_long, sw_lat, sw_long, zoom_value, currency, "")

#         # Filter results: only keep listings with rating >= 4.3
#         filtered_results = [listing for listing in search_results if float(listing.get("rating", {}).get("value", 0)) >= 4.5 and (category == '' or listing.get("category") == category)]

#         return jsonify(filtered_results)
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# #GET THE COMMENTS in reviews and put it in the list
# @app.route('/reviews', methods=['GET'])
# def get_reviews():
#     # Get listing URL and proxy URL
#     room_url = request.args.get("room_url", "https://www.airbnb.com/rooms/30931885")
#     proxy_url = request.args.get("proxy_url", "")

#     try:
#         reviews_data = pyairbnb.get_reviews(room_url, proxy_url)
#         comments = [review.get("comments", "") for review in reviews_data]

#         return jsonify(comments)
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500




# import requests

# CLAUDE_API_KEY = ''  # Replace with your API key
# CLAUDE_API_URL = 'https://api.groq.ai/v1/process'  # Replace with the actual API URL for Claude

# def analyze_sentiment_with_claude(review_text):
#     prompt = f"Analyze the sentiment of the following review. Tell me if it's positive, neutral, or negative: {review_text}"
    
#     response = requests.post(
#         CLAUDE_API_URL,
#         headers={'Authorization': f'Bearer {CLAUDE_API_KEY}'},
#         json={'prompt': prompt, 'max_tokens': 100}
#     )
    
#     sentiment = response.json().get('text', '').strip()
#     return sentiment



# def extract_keywords_with_claude(review_text):
#     prompt = f"Extract the most important keywords related to cleanliness, location, comfort, etc., from the following review: {review_text}"
    
#     response = requests.post(
#         CLAUDE_API_URL,
#         headers={'Authorization': f'Bearer {CLAUDE_API_KEY}'},
#         json={'prompt': prompt, 'max_tokens': 100}
#     )
    
#     keywords = response.json().get('text', '').strip()
#     return keywords.split(",")  # Assuming the keywords are returned in comma-separated format




# @app.route('/reviews', methods=['GET'])
# def get_reviews():
#     # Get listing URL and proxy URL
#     room_url = request.args.get("room_url", "https://www.airbnb.com/rooms/30931885")
#     proxy_url = request.args.get("proxy_url", "")

#     try:
#         reviews_data = pyairbnb.get_reviews(room_url, proxy_url)
#         comments = [review.get("comments", "") for review in reviews_data]
        
#         # Analyze sentiment and extract keywords for each review using Claude
#         results = []
#         for comment in comments:
#             sentiment = analyze_sentiment_with_claude(comment)  # Sentiment analysis with Claude
#             keywords = extract_keywords_with_claude(comment)  # Keyword extraction with Claude
#             results.append({
#                 "comment": comment,
#                 "sentiment": sentiment,
#                 "keywords": keywords
#             })

#         return jsonify(results)
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# def rank_listings(listings, reviews, user_keywords):
#     ranked_listings = []

#     for listing in listings:
#         review = reviews.get(listing["id"])  # Get reviews for the listing
#         if review:
#             sentiment = analyze_sentiment_with_claude(review)
#             keywords = extract_keywords_with_claude(review)

#             sentiment_score = 1 if sentiment == "positive" else -1 if sentiment == "negative" else 0
#             # Compare keywords with user preferences (user_keywords is a list of keywords they care about)
#             matched_keywords = [kw for kw in keywords if kw in user_keywords]
#             score = len(matched_keywords) + sentiment_score  # A basic score combining sentiment and keyword relevance
#             ranked_listings.append({"listing_id": listing["id"], "score": score})

#     # Sort listings by score (higher score = better match)
#     ranked_listings = sorted(ranked_listings, key=lambda x: x["score"], reverse=True)
#     return ranked_listings[:5]  # Top 5 listings



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


# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5001)