from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Dict, Any
from recommendations_system import UnifiedRecommendationSystem


app = Flask(__name__)
CORS(app)

# Initialize the unified recommendation system
recommender = UnifiedRecommendationSystem(
    llama_url=os.getenv("LLAMA_URL", "http://localhost:8000"),
    gorse_url=os.getenv("GORSE_URL", "http://localhost:8087"),
    nsfw_url=os.getenv("NSFW_URL", "http://localhost:8001")
)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "unified-recommendation-system"
    }), 200


@app.route("/api/category/extract-tags", methods=["POST"])
def extract_tags():
    """
    Extract tags from user input
    
    Request Body:
    {
        "text": "user input text"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = data["text"]
        tags = recommender.category_recommender.extract_tags(text)
        
        return jsonify({
            "success": True,
            "tags": tags
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/category/recommend", methods=["POST"])
def category_recommend():
    """
    Get category-based recommendations
    
    Request Body:
    {
        "text": "user interest or query",
        "top_k": 10
    }
    """
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = data["text"]
        top_k = data.get("top_k", 10)
        
        result = recommender.get_category_recommendations(text, top_k)
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/recommend/<user_id>", methods=["GET"])
def gorse_recommend(user_id: str):
    """
    Get Gorse-based recommendations for a user
    
    Query Parameters:
    - n: Number of recommendations (default: 10)
    - categories: Comma-separated category filters
    """
    try:
        n = request.args.get("n", 10, type=int)
        categories_str = request.args.get("categories", "")
        
        categories = None
        if categories_str:
            categories = [c.strip() for c in categories_str.split(",")]
        
        result = recommender.get_gorse_recommendations(user_id, n, categories)
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/user", methods=["POST"])
def add_user():
    """
    Add or update a user
    
    Request Body:
    {
        "user_id": "unique_user_id",
        "labels": ["label1", "label2"],
        "comment": "additional info"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "user_id" not in data:
            return jsonify({"error": "Missing 'user_id' field"}), 400
        
        user_id = data["user_id"]
        labels = data.get("labels", [])
        comment = data.get("comment", "")
        
        result = recommender.gorse_recommender.add_user(user_id, labels, comment)
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/item", methods=["POST"])
def add_item():
    """
    Add or update an item
    
    Request Body:
    {
        "item_id": "unique_item_id",
        "labels": ["tag1", "tag2"],
        "categories": ["category1"],
        "comment": "item description",
        "is_hidden": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or "item_id" not in data:
            return jsonify({"error": "Missing 'item_id' field"}), 400
        
        item_id = data["item_id"]
        labels = data.get("labels", [])
        categories = data.get("categories", [])
        comment = data.get("comment", "")
        is_hidden = data.get("is_hidden", False)
        
        result = recommender.gorse_recommender.add_item(
            item_id, labels, categories, comment, is_hidden
        )
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/feedback", methods=["POST"])
def add_feedback():
    """
    Submit user feedback/interaction
    
    Request Body:
    {
        "user_id": "user_id",
        "item_id": "item_id",
        "feedback_type": "read|like|dislike",
        "timestamp": "optional ISO timestamp"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "user_id" not in data or "item_id" not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        user_id = data["user_id"]
        item_id = data["item_id"]
        feedback_type = data.get("feedback_type", "read")
        timestamp = data.get("timestamp")
        
        result = recommender.gorse_recommender.add_feedback(
            user_id, item_id, feedback_type, timestamp
        )
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/popular", methods=["GET"])
def get_popular():
    """
    Get popular items
    
    Query Parameters:
    - n: Number of items (default: 10)
    - offset: Pagination offset (default: 0)
    """
    try:
        n = request.args.get("n", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        items = recommender.gorse_recommender.get_popular_items(n, offset)
        
        return jsonify({
            "success": True,
            "items": items
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/latest", methods=["GET"])
def get_latest():
    """
    Get latest items
    
    Query Parameters:
    - n: Number of items (default: 10)
    - offset: Pagination offset (default: 0)
    """
    try:
        n = request.args.get("n", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        items = recommender.gorse_recommender.get_latest_items(n, offset)
        
        return jsonify({
            "success": True,
            "items": items
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gorse/similar/<item_id>", methods=["GET"])
def get_similar(item_id: str):
    """
    Get similar items
    
    Query Parameters:
    - n: Number of items (default: 10)
    - offset: Pagination offset (default: 0)
    """
    try:
        n = request.args.get("n", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        items = recommender.gorse_recommender.get_similar_items(item_id, n, offset)
        
        return jsonify({
            "success": True,
            "similar_items": items
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/moderate/content", methods=["POST"])
def moderate_content():
    """
    Moderate content for safety
    
    Request Body:
    {
        "text": "text to analyze (optional)",
        "image": "base64 encoded image (optional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Empty request body"}), 400
        
        text = data.get("text")
        image = data.get("image")
        
        if not text and not image:
            return jsonify({"error": "Provide either text or image"}), 400
        
        result = recommender.moderate_content(text, image)
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hybrid/recommend", methods=["POST"])
def hybrid_recommend():
    """
    Hybrid recommendation combining category and Gorse
    
    Request Body:
    {
        "user_id": "user_id",
        "query": "user interest text",
        "n": 10,
        "weight_category": 0.5,
        "weight_gorse": 0.5
    }
    """
    try:
        data = request.get_json()
        
        if not data or "user_id" not in data:
            return jsonify({"error": "Missing 'user_id' field"}), 400
        
        user_id = data["user_id"]
        query = data.get("query", "")
        n = data.get("n", 10)
        weight_category = data.get("weight_category", 0.5)
        weight_gorse = data.get("weight_gorse", 0.5)
        
        # Get category-based recommendations
        category_result = {}
        if query:
            category_result = recommender.get_category_recommendations(query, n)
        
        # Get Gorse recommendations
        gorse_result = recommender.get_gorse_recommendations(user_id, n)
        
        # Combine results
        hybrid_result = {
            "method": "hybrid",
            "user_id": user_id,
            "category_recommendations": category_result,
            "gorse_recommendations": gorse_result,
            "weights": {
                "category": weight_category,
                "gorse": weight_gorse
            }
        }
        
        return jsonify({
            "success": True,
            "result": hybrid_result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/health",
            "/api/category/extract-tags",
            "/api/category/recommend",
            "/api/gorse/recommend/<user_id>",
            "/api/gorse/user",
            "/api/gorse/item",
            "/api/gorse/feedback",
            "/api/gorse/popular",
            "/api/gorse/latest",
            "/api/gorse/similar/<item_id>",
            "/api/moderate/content",
            "/api/hybrid/recommend"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Unified Recommendation API on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )