import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from models.category_manager import CategoryManager


@pytest.fixture
def category_manager():
    """Create CategoryManager instance for testing"""
    manager = CategoryManager(
        mongo_uri='mongodb://localhost:27017/',
        mongo_db='test_recommendation_db',
        llama_api_url='http://localhost:11434'
    )
    yield manager
    manager.close()


def test_detect_query_category(category_manager):
    """Test category detection from query"""
    
    test_cases = [
        ("best action movies 2024", "movies"),
        ("cricket world cup", "sports"),
        ("smartphones under 20000", "technology"),
        ("pasta recipes", "food")
    ]
    
    for query, expected_category in test_cases:
        detected = category_manager.detect_query_category(query)
        assert len(detected) > 0
        assert detected[0]['category'] == expected_category


def test_get_category_top_posts(category_manager):
    """Test getting top posts for a category"""
    
    # This test requires trained data
    posts = category_manager.get_category_top_posts('movies', limit=5)
    
    # Should return posts (if data exists)
    assert isinstance(posts, list)


def test_get_all_categories(category_manager):
    """Test getting all categories"""
    
    categories = category_manager.get_all_categories()
    assert isinstance(categories, list)