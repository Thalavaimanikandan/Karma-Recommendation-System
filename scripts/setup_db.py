
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_mongodb_collections(
    mongo_uri='mongodb://localhost:27017/',
    db_name='recommendation_db',
    drop_existing=False
):
    """Setup MongoDB collections with indexes"""
    
    logger.info(f"🔧 Setting up MongoDB database: {db_name}")
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    collections = {
        'posts': [
            ('_id', 1),
            ('category', 1),
            ('created_at', -1)
        ],
        'users': [
            ('user_id', 1),
            ('created_at', -1)
        ],
        'user_interests': [
            ('user_id', 1),
            ('category', 1),
            ('score', -1)
        ],
        'categories': [
            ('name', 1)
        ],
        'category_scores': [
            ('post_id', 1),
            ('category', 1),
            ('relevance_score', -1)
        ],
        'interactions': [
            ('user_id', 1),
            ('post_id', 1),
            ('timestamp', -1)
        ],
        'recommendation_log': [
            ('user_id', 1),
            ('timestamp', -1)
        ]
    }
    
    for collection_name, indexes in collections.items():
        if drop_existing and collection_name in db.list_collection_names():
            db[collection_name].drop()
            logger.info(f"   Dropped collection: {collection_name}")
        
        collection = db[collection_name]
        
        # Create indexes
        for index_field, order in indexes:
            collection.create_index([(index_field, order)])
        
        logger.info(f"✅ Setup collection: {collection_name} with {len(indexes)} indexes")
    
    client.close()
    logger.info("✅ MongoDB setup complete!")


if __name__ == '__main__':
    setup_mongodb_collections(drop_existing=True)
