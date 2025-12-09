import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import advanced recommendation system
try:
    from adv_mongodb_recommend import AdvancedMongoDBRecommendationSystem
    logger.info("✅ Advanced MongoDB Recommendation module imported")
except ImportError as e:
    logger.error(f"❌ Import failed: {e}")
    AdvancedMongoDBRecommendationSystem = None

app = Flask(__name__)
CORS(app)

app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Configuration
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'gorse_app')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'posts')
MODEL_NAME = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

# Initialize recommender
recommender = None
if AdvancedMongoDBRecommendationSystem:
    try:
        logger.info("🔄 Initializing Advanced Recommendation System...")
        recommender = AdvancedMongoDBRecommendationSystem(
            mongo_uri=MONGO_URI,
            database_name=DATABASE_NAME,
            collection_name=COLLECTION_NAME,
            model_name=MODEL_NAME
        )
        logger.info("✅ Advanced system initialized")
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")

@app.route('/')
def index():
    stats = {}
    if recommender:
        try:
            stats = recommender.get_stats()
        except:
            pass
    
    return jsonify({
        'message': 'Advanced MongoDB Recommendation System API',
        'version': '3.0.0 - Smart Search with NLP',
        'features': [
            'Automatic keyword extraction',
            'Category auto-detection',
            'Synonym and related term matching',
            'Context-aware search'
        ],
        'status': 'running',
        'recommender_status': 'ready' if recommender else 'not initialized',
        'database': DATABASE_NAME,
        'collection': COLLECTION_NAME,
        'total_documents': stats.get('total_documents', 0),
        'endpoints': {
            'health': 'GET /api/health',
            'stats': 'GET /api/stats',
            'categories': 'GET /api/categories',
            'smart_search': 'POST /api/smart-search',
            'search': 'POST /api/search',
            'extract_keywords': 'POST /api/extract-keywords',
            'detect_category': 'POST /api/detect-category',
            'refresh': 'POST /api/refresh'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'api': 'running',
            'recommender': 'ready' if recommender else 'not initialized'
        }
    }
    
    if recommender:
        try:
            recommender.client.server_info()
            health['services']['mongodb'] = 'connected'
        except:
            health['services']['mongodb'] = 'disconnected'
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        health['services']['ollama'] = 'running' if response.status_code == 200 else 'error'
    except:
        health['services']['ollama'] = 'offline'
    
    return jsonify(health)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    if not recommender:
        return jsonify({'error': 'System not initialized'}), 503
    try:
        stats = recommender.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    if not recommender:
        return jsonify({'error': 'System not initialized'}), 503
    try:
        categories = recommender.get_categories()
        category_keywords = recommender.category_keywords
        return jsonify({
            'categories': categories,
            'count': len(categories),
            'keywords_index': category_keywords
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-keywords', methods=['POST'])
def extract_keywords():
    if not recommender:
        return jsonify({'error': 'System not initialized'}), 503
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Text parameter required'}), 400
        text = data['text']
        top_n = data.get('top_n', 10)
        keywords = recommender.extract_keywords(text, top_n=top_n)
        return jsonify({
            'text': text,
            'keywords': keywords,
            'count': len(keywords)
        })
    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect-category', methods=['POST'])
def detect_category():
    if not recommender:
        return jsonify({'error': 'System not initialized'}), 503
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Text parameter required'}), 400
        text = data['text']
        keywords = recommender.extract_keywords(text)
        category = recommender.detect_category(text)
        return jsonify({
            'text': text,
            'keywords': keywords,
            'detected_category': category,
            'confidence': 'high' if category else 'low'
        })
    except Exception as e:
        logger.error(f"Category detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/smart-search', methods=['POST'])
@app.route('/api/search', methods=['POST'])
@app.route('/api/category/recommend', methods=['POST'])
def smart_search():
    try:
        if not recommender:
            return jsonify({
                'error': 'System not initialized',
                'message': 'MongoDB connection failed or no data available'
            }), 503
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '').strip()
        top_k = data.get('top_k', 5)
        category = data.get('category', None)
        auto_detect = data.get('auto_detect', True)
        
        if not text:
            return jsonify({'error': 'Text parameter required'}), 400
        
        if not isinstance(top_k, int) or top_k < 1:
            return jsonify({'error': 'top_k must be positive integer'}), 400
        
        logger.info(f"🔍 Smart search: '{text}', top_k: {top_k}")
        
        results, keywords, detected_category = recommender.smart_search(
            query=text,
            top_k=top_k,
            auto_detect_category=auto_detect,
            category_filter=category
        )
        
        if results is not None and len(results) > 0:
            result_list = results.to_dict('records')
            
            for item in result_list:
                if 'similarity_score' in item:
                    item['similarity_score'] = float(item['similarity_score'])
                for field in ['combined_text', 'tags_str']:
                    if field in item:
                        del item[field]
            
            logger.info(f"✅ Found {len(result_list)} results")
            
            return jsonify({
                'success': True,
                'query': text,
                'extracted_keywords': keywords,
                'detected_category': detected_category,
                'filter_category': category,
                'count': len(result_list),
                'recommendations': result_list
            })
        else:
            return jsonify({
                'success': True,
                'query': text,
                'extracted_keywords': keywords,
                'detected_category': detected_category,
                'count': 0,
                'recommendations': [],
                'message': 'No recommendations found'
            })
            
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    if not recommender:
        return jsonify({'error': 'System not initialized'}), 503
    try:
        logger.info("🔄 Refreshing data...")
        recommender.refresh_data()
        stats = recommender.get_stats()
        return jsonify({
            'success': True,
            'message': 'Data refreshed',
            'total_documents': stats['total_documents'],
            'categories': stats['categories'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    test_data = {
        'message': 'Advanced API working!',
        'timestamp': datetime.now().isoformat(),
        'recommender_status': 'initialized' if recommender else 'not initialized',
        'database': DATABASE_NAME,
        'collection': COLLECTION_NAME
    }
    if recommender:
        try:
            stats = recommender.get_stats()
            test_data['total_documents'] = stats['total_documents']
            test_data['categories'] = stats['categories']
        except:
            pass
    return jsonify(test_data)

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Advanced MongoDB Recommendation System API")
    print("=" * 80)
    print(f"📍 Server: http://0.0.0.0:5000")
    print(f"📊 Database: {DATABASE_NAME}")
    print(f"📁 Collection: {COLLECTION_NAME}")
    print("=" * 80)
    
    if recommender:
        try:
            stats = recommender.get_stats()
            print(f"✅ System Ready: {stats['total_documents']} documents")
            print(f"📋 Categories: {', '.join(stats['categories'])}")
        except:
            pass
    else:
        print("⚠️  System not initialized")
    
    print("=" * 80)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
