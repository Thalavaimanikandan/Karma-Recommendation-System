# config.py - Centralized Configuration

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    """Application configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Database
    DB_PATH = os.getenv('DB_PATH', str(BASE_DIR / 'data' / 'reddit_posts.db'))
    
    # Qdrant
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'recommendation_db_posts')
    
    # Model settings
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    EMBEDDING_DIM = 384
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Recommendation settings
    DEFAULT_RECOMMENDATIONS = 10
    MAX_RECOMMENDATIONS = 50


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # In production, ensure all sensitive data is from environment
    MONGO_URI = os.getenv('MONGO_URI')  # Must be set
    GORSE_API_KEY = os.getenv('GORSE_API_KEY')  # Must be set


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_DB = 'test_recommendation_db'


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env='development'):
    """Get configuration based on environment"""
    return config.get(env, DevelopmentConfig)

