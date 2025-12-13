from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from pymongo import MongoClient
import os
from datetime import datetime
import traceback
from config.config import Config
from models.category_manager import CategoryManager
from utils.database_manager import DatabaseManager
from models.hybrid_recommender import HybridRecommender
from services.mongodb_recommendation import MongoDBService

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
recommender = None
category_manager = None
db_manager = None
BLOCKED_TERMS = {
    'porn', 'pornhub', 'xxx', 'sex', 'nude', 'nsfw', 
    'adult', 'explicit', 'erotic', 'naked', 'xvideos',
    'redtube', 'youporn'
}

SKIP_CATEGORIES = ['general', 'other', 'unknown', 'misc']

app = Flask(__name__)
CORS(app)

# Configuration from environment or defaults
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGO_DB', 'recommendation_db')
GORSE_API_URL = os.getenv('GORSE_API_URL', 'http://localhost:8087 ')
LLAMA_API_URL = os.getenv('LLAMA_API_URL', 'http://localhost:11434')

# MongoDB Connection - CORRECT WAY ✅
try:
    client = MongoClient(MONGO_URI)  # MongoClient-ஐ use பண்ணு, MONGO_URI-ஐ இல்ல!
    db = client[MONGO_DB]  # Use MONGO_DB variable
    # Test connection
    client.server_info()
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None
    db = None

# Initialize services (Singleton pattern)
category_manager = None
recommender = None
db_manager = None  


def is_safe_query(query: str) -> tuple:
    """Check if query is safe for processing"""
    if not query or len(query.strip()) == 0:
        return False, "Empty query"
    
    query_lower = query.lower().strip()
    
    # Check blocked terms
    for term in BLOCKED_TERMS:
        if term in query_lower:
            return False, "Inappropriate content detected"
    
    # Check length
    if len(query) > 500:
        return False, "Query too long (max 500 characters)"
    
    return True, "OK"

def init_services():
    """Initialize recommendation services"""
    global recommender, db_manager, category_manager
    try:
        if db is None:
            logger.error("Database not connected, cannot initialize services")
            return False
        
        # MongoDB configuration
        MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        MONGO_DB = os.getenv('MONGO_DB', 'recommendation_db')
        
        # Gorse configuration
        GORSE_API_URL = os.getenv('GORSE_API_URL', 'http://localhost:8089')
        
        # Initialize CategoryManager first
        from models.category_manager import CategoryManager
        category_manager = CategoryManager(
            mongo_uri=MONGO_URI,
            mongo_db=MONGO_DB
        )
        
        # Initialize HybridRecommender with correct parameters
        recommender = HybridRecommender(
            mongo_uri=MONGO_URI,
            mongo_db=MONGO_DB,
            gorse_api_url=GORSE_API_URL,
            category_manager=category_manager,
            embedding_model=Config.EMBEDDING_MODEL
        )
        
        # Initialize MongoDB service (replace SQLite DatabaseManager)
       
        db_manager = MongoDBService(
            mongo_uri=MONGO_URI,
            db_name=MONGO_DB
        )
        
        logger.info("✅ Services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False

@app.before_request
def before_request():
    """Initialize services before handling requests"""
    try:
        init_services()
    except Exception as e:
        logger.error(f"Service initialization error: {e}")


# ============================================================
# ENDPOINTS
# ============================================================


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'api': 'operational'
            }
        }
        
        if recommender is None:
            status['status'] = 'degraded'
            status['services']['recommender'] = 'failed'
            status['error'] = 'Recommender service failed to initialize'
            return jsonify(status), 503
        
        status['services']['recommender'] = 'operational'
        status['services']['database'] = 'operational' if db_manager else 'unavailable'
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/user/onboard', methods=['POST'])
def user_onboarding():
    """
    New user onboarding with 3 interests
    
    Request:
    {
        "user_id": "user_123",
        "interests": ["movies", "sports", "technology"]
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        interests = data.get('interests', [])
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        if len(interests) != 3:
            return jsonify({'error': 'Exactly 3 interests required'}), 400
        
        # Create user profile
        result = recommender.create_user_profile(user_id, interests)
        
        # Get initial recommendations based on interests
        recommendations, metadata = recommender.recommend(
            user_id=user_id,
            query=None,
            limit=10
        )
        
        return jsonify({
            'status': 'success',
            'user': result,
            'initial_recommendations': recommendations,
            'metadata': metadata
        })
    
    except Exception as e:
        logger.error(f"❌ Onboarding error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend/simple', methods=['POST'])
def simple_recommend():
    """Simple category-based recommendations (for testing)"""
    try:
        data = request.json
        user_id = data.get('user_id')
        limit = data.get('n', 10)
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Get user interests
        user = db.users.find_one({'user_id': user_id})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        interests = user.get('interests', [])
        
        # Get articles from interested categories
        recommendations = []
        
        for interest in interests:
            articles = list(db.articles.find({'category': interest}).limit(limit // len(interests)))
            for article in articles:
                article['_id'] = str(article['_id'])
                article['score'] = 1.0
                article['reason'] = f"Matches your interest: {interest}"
                recommendations.append(article)
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations[:limit],
            'metadata': {
                'user_interests': interests,
                'total_results': len(recommendations)
            }
        })
    
    except Exception as e:
        logger.error(f"Simple recommend error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/track', methods=['POST'])
def track_interaction():
    """
    Track user interaction
    
    Request:
    {
        "user_id": "user_123",
        "post_id": "post_456",
        "action": "like"  // view, click, like, share
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        post_id = data.get('post_id')
        action = data.get('action', 'view')
        
        if not user_id or not post_id:
            return jsonify({'error': 'user_id and post_id required'}), 400
        
        # Track interaction
        recommender.track_interaction(user_id, post_id, action)
        
        return jsonify({
            'status': 'success',
            'message': f'Tracked {action} for {post_id}'
        })
    
    except Exception as e:
        logger.error(f"❌ Tracking error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<user_id>/interests', methods=['GET'])
def get_user_interests(user_id):
    """Get user's current interests"""
    try:
        interests = recommender.get_user_interests(user_id)
        
        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'interests': interests
        })
    
    except Exception as e:
        logger.error(f"❌ Get interests error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        if db_manager is None:
            return jsonify({"error": "Database manager not initialized"}), 500
        
        # Get counts from database
        articles_count = db_manager.db.articles.count_documents({})
        users_count = db_manager.db.users.count_documents({})
        interactions_count = db_manager.db.interactions.count_documents({})
        
        # Get category breakdown
        category_counts = {}
        if articles_count > 0:
            pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}}
            ]
            category_data = list(db_manager.db.articles.aggregate(pipeline))
            category_counts = {item['_id']: item['count'] for item in category_data}
        
        return jsonify({
            "status": "success",
            "total_articles": articles_count,
            "total_users": users_count,
            "total_interactions": interactions_count,
            "categories": category_counts,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Get articles with optional filtering"""
    try:
        if db_manager is None:
            return jsonify({"error": "Database manager not initialized"}), 500
        
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        query = {}
        if category:
            query['category'] = category
        
        articles = list(db.articles.find(query).skip(skip).limit(limit))
        total = db.articles.count_documents(query)
        
        for article in articles:
            article['_id'] = str(article['_id'])
        
        return jsonify({
            "status": "success",
            "total": total,
            "count": len(articles),
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all available categories"""
    try:
        if category_manager is None:
            return jsonify({"error": "Category manager not initialized"}), 500
        
        categories = category_manager.get_all_categories()
        
        return jsonify({
            "status": "success",
            "categories": categories,
            "count": len(categories)
        })
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/category/<category_name>/posts', methods=['GET'])
def get_category_posts(category_name):
    """Get top posts for a specific category"""
    try:
        limit = int(request.args.get('limit', 10))
        min_score = float(request.args.get('min_score', 0.5))
        
        posts = category_manager.get_category_top_posts(
            category=category_name,
            limit=limit,
            min_score=min_score
        )
        
        return jsonify({
            'status': 'success',
            'category': category_name,
            'posts': posts
        })
    
    except Exception as e:
        logger.error(f"❌ Get category posts error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/train', methods=['POST'])
def train_categories():
    """
    Admin endpoint to train categories from dataset
    
    Request:
    {
        "dataset_path": "data/llama_dataset.json"
    }
    """
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path', 'data/llama_dataset.json')
        
        # Train categories (this may take time)
        category_manager.train_categories_from_dataset(dataset_path)
        
        return jsonify({
            'status': 'success',
            'message': f'Categories trained from {dataset_path}'
        })
    
    except Exception as e:
        logger.error(f"❌ Training error: {e}")
        return jsonify({'error': str(e)}), 500


# app.py - Update /api/search endpoint
# app.py - /api/search endpoint fix

# app.py - Replace entire /api/search endpoint

# app.py - /api/search endpoint

@app.route('/api/search', methods=['GET'])
def search():
    """
    Search posts with category detection and dynamic interest learning
    
    GET /api/search?q=farmer&user_id=user_123&limit=10
    
    Features:
    - Detects category from query
    - Adds new interests to user profile
    - Returns relevant posts
    - Fallback to user interests if no matches
    - Content filtering for inappropriate queries
    """
    try:
        # 1. Get parameters
        query = request.args.get('q', '').strip()
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter (q) is required'
            }), 400
        
        # 2. Safety check
        is_safe, reason = is_safe_query(query)
        if not is_safe:
            logger.warning(f"⚠️ Blocked query: {query} - {reason}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid query',
                'reason': reason
            }), 400
        
        logger.info(f"🔍 Search: '{query}' by user: {user_id}")
        
        # 3. Detect category from query
        try:
            detected_categories = category_manager.detect_query_category(query)
        except Exception as e:
            logger.error(f"Category detection error: {e}")
            detected_categories = []
        
        # Handle different response formats (dict or list)
        if isinstance(detected_categories, dict):
            detected_categories = [detected_categories]
        
        if not detected_categories or len(detected_categories) == 0:
            detected_categories = [{'category': 'general', 'confidence': 0.5}]
        
        # Get primary category
        primary_category = detected_categories[0].get('category', 'general')
        confidence = detected_categories[0].get('confidence', detected_categories[0].get('score', 0.5))
        
        logger.info(f"📊 Detected category: {primary_category} (confidence: {confidence})")
        
        # 4. Update user interests (if valid category)
        interest_added = False
        if user_id and primary_category not in SKIP_CATEGORIES:
            try:
                user = db.users.find_one({'user_id': user_id})
                
                if user:
                    current_interests = user.get('interests', [])
                    
                    # Add if not already present
                    if primary_category not in current_interests:
                        logger.info(f"➕ Adding new interest '{primary_category}' for user {user_id}")
                        
                        # Update users collection
                        db.users.update_one(
                            {'user_id': user_id},
                            {
                                '$addToSet': {'interests': primary_category},
                                '$set': {'updated_at': datetime.now()}
                            }
                        )
                        
                        # Update user_interests collection
                        db.user_interests.update_one(
                            {'user_id': user_id, 'category': primary_category},
                            {
                                '$set': {
                                    'score': 5.0,  # Lower than initial interests (10.0)
                                    'last_updated': datetime.now(),
                                    'interaction_count': 1,
                                    'learned_from': 'search'
                                }
                            },
                            upsert=True
                        )
                        
                        interest_added = True
                        logger.info(f"✅ Interest '{primary_category}' added to user profile")
                    else:
                        logger.info(f"ℹ️ User already has interest: {primary_category}")
                else:
                    logger.warning(f"⚠️ User {user_id} not found in database")
                    
            except Exception as e:
                logger.warning(f"Failed to update user interests: {e}")
        
        # 5. Get recommendations
        recommendations = []
        match_strategy = None
        
        # Strategy 1: Try to find posts in detected category
        if primary_category not in SKIP_CATEGORIES:
            try:
                articles = list(db.articles.find({'category': primary_category}).limit(limit))
                
                if articles:
                    for article in articles:
                        article['_id'] = str(article['_id'])
                        article['match_reason'] = f"Matches category: {primary_category}"
                    recommendations = articles
                    match_strategy = "primary_category"
                    logger.info(f"✅ Found {len(recommendations)} posts in '{primary_category}'")
            except Exception as e:
                logger.error(f"Article fetch error: {e}")
        
        # Strategy 2: Fallback to user's existing interests
        if not recommendations and user_id:
            try:
                user = db.users.find_one({'user_id': user_id})
                
                if user:
                    user_interests = user.get('interests', [])
                    
                    if user_interests:
                        articles = list(db.articles.find({
                            'category': {'$in': user_interests}
                        }).limit(limit))
                        
                        if articles:
                            for article in articles:
                                article['_id'] = str(article['_id'])
                                article['match_reason'] = f"From your interests: {article.get('category')}"
                            recommendations = articles
                            match_strategy = "user_interests"
                            logger.info(f"✅ Fallback: Found {len(recommendations)} from user interests")
            except Exception as e:
                logger.error(f"Fallback error: {e}")
        
        # Strategy 3: Show popular posts (last resort)
        if not recommendations:
            try:
                articles = list(db.articles.find().sort('views', -1).limit(limit))
                
                for article in articles:
                    article['_id'] = str(article['_id'])
                    article['match_reason'] = "Popular posts"
                recommendations = articles
                match_strategy = "popular"
                logger.info(f"✅ Popular fallback: {len(recommendations)} posts")
            except Exception as e:
                logger.error(f"Popular posts error: {e}")
        
        # 6. Return response
        return jsonify({
            'status': 'success',
            'query': query,
            'detected_categories': detected_categories,
            'results': recommendations,
            'metadata': {
                'user_id': user_id,
                'query_category': primary_category,
                'category_confidence': confidence,
                'interest_added': interest_added,
                'total_results': len(recommendations),
                'match_strategy': match_strategy,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
    
@app.route('/api/posts/create', methods=['POST'])
def create_post():
    """Create new post"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        title = data.get('title')
        body = data.get('body')
        declared_category = data.get('category')
        
        if not user_id or not title or not body:
            return jsonify({'error': 'user_id, title, and body required'}), 400
        
        # 1. Create post in MongoDB
        post = {
            'title': title,
            'body': body,
            'category': declared_category or 'general',
            'author_id': user_id,
            'created_at': datetime.now(),
            'likes': 0,
            'views': 0
        }
        
        result = db.articles.insert_one(post)  # 'articles' collection-ல store பண்ணு
        post_id = str(result.inserted_id)
        
        logger.info(f"✅ Post created: {post_id}")
        
        # 2. Auto-detect category (if not provided)
        if not declared_category:
            try:
                detected = category_manager.detect_query_category(f"{title} {body}")
                if detected:
                    detected_category = detected[0]['category']
                    db.articles.update_one(
                        {'_id': result.inserted_id},
                        {'$set': {'category': detected_category}}
                    )
                    post['category'] = detected_category
                    logger.info(f"🎯 Auto-detected category: {detected_category}")
            except Exception as e:
                logger.warning(f"Category detection failed: {e}")
        
        # 3. ❌ SKIP TRAINING FOR NOW - Comment out this section
        # logger.info(f"🤖 Training post: {post_id}")
        # category_manager._train_single_post({
        #     '_id': result.inserted_id,
        #     **post
        # })
        
        # 4. Create embedding (if recommender available)
        try:
            full_text = f"{title} {body}"
            embedding = recommender.embedding_model.encode(
                full_text,
                normalize_embeddings=True
            )
            
            from qdrant_client.models import PointStruct
            
            recommender.qdrant_client.upsert(
                collection_name=recommender.collection_name,
                points=[
                    PointStruct(
                        id=post_id,
                        vector=embedding.tolist(),
                        payload={
                            'title': title,
                            'category': post['category'],
                            'author_id': user_id
                        }
                    )
                ]
            )
            logger.info(f"💾 Embedding stored in Qdrant")
        except Exception as e:
            logger.warning(f"Embedding storage failed: {e}")
        
        return jsonify({
            'status': 'success',
            'post_id': post_id,
            'category': post['category'],
            'message': 'Post created successfully'
        })
    
    except Exception as e:
        logger.error(f"❌ Create post error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/retrain', methods=['POST'])
def retrain_all_posts():
    """
    Admin endpoint to retrain all posts
    Use this when you update category keywords or LLaMA model
    """
    try:
        # Train from MongoDB directly (no JSON needed)
        category_manager.train_categories_from_mongodb(
            skip_already_trained=False  # Retrain everything
        )
        
        return jsonify({
            'status': 'success',
            'message': 'All posts retrained successfully'
        })
    
    except Exception as e:
        logger.error(f"❌ Retrain error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/train-new', methods=['POST'])
def train_new_posts():
    """
    Train only new posts that haven't been trained yet
    Call this periodically (e.g., via cron job)
    """
    try:
        category_manager.train_new_posts_only()
        
        return jsonify({
            'status': 'success',
            'message': 'New posts trained successfully'
        })
    
    except Exception as e:
        logger.error(f"❌ Train new posts error: {e}")
        return jsonify({'error': str(e)}), 500
    

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    logger.info("🚀 Starting Flask Recommendation API on http://localhost:5000")
    logger.info(f"   MongoDB: {MONGO_DB}")
    logger.info(f"   Gorse: {GORSE_API_URL}")
    logger.info(f"   LLaMA: {LLAMA_API_URL}")
    
    init_services()
    
    # ADD THIS LINE:
    init_services()
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )