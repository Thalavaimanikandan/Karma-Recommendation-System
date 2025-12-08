import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Service URLs
    LLAMA_URL = os.getenv("LLAMA_URL", "http://localhost:8000")
    GORSE_URL = os.getenv("GORSE_URL", "http://localhost:8087")
    NSFW_URL = os.getenv("NSFW_URL", "http://localhost:8001")
    
    # Gorse
    GORSE_API_KEY = os.getenv("GORSE_API_KEY", "")
    
    # Database
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MYSQL_URL = os.getenv("MYSQL_URL", "mysql://gorse:password@localhost:3306/gorse")
    
    # Recommendation Settings
    MAX_TAGS = 9
    TOXICITY_THRESHOLD = 0.35
    NSFW_THRESHOLD = 0.35
    DEFAULT_TOP_K = 10
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
