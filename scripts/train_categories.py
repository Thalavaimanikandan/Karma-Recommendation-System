import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.category_manager import CategoryManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_categories(dataset_path='data/llama_dataset.json'):
    """Train categories from dataset"""
    
    logger.info(f"🤖 Training categories from: {dataset_path}")
    
    if not os.path.exists(dataset_path):
        logger.error(f"❌ Dataset not found: {dataset_path}")
        logger.info("💡 Run 'python scripts/seed_data.py' first to create sample data")
        return
    
    manager = CategoryManager(
        mongo_uri='mongodb://localhost:27017/',
        mongo_db='recommendation_db',
        llama_api_url='http://localhost:11434'
    )
    
    try:
        manager.train_categories_from_dataset(dataset_path)
        logger.info("✅ Training complete!")
        
        # Show categories
        categories = manager.get_all_categories()
        logger.info(f"\n📊 Available categories: {len(categories)}")
        for cat in categories:
            logger.info(f"   - {cat['name']}: {cat.get('post_count', 0)} posts")
    
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
    
    finally:
        manager.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    else:
        dataset_path = 'data/llama_dataset.json'
    
    train_categories(dataset_path)
