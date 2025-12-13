
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from models.category_manager import CategoryManager
from models.hybrid_recommender import HybridRecommender


@pytest.fixture
def category_manager():
    """Create CategoryManager instance"""
    manager = CategoryManager(
        mongo_uri='mongodb://localhost:27017/',
        mongo_db='test_recommendation_db',
        llama_api_url='http://localhost:11434'
    )
    yield manager
    manager.close()


@pytest.fixture
def recommender(category_manager):
    """Create HybridRecommender instance"""
    rec = HybridRecommender(
        mongo_uri='mongodb://localhost:27017/',
        mongo_db='test_recommendation_db',
        gorse_api_url='http://localhost:8087',
        category_manager=category_manager
    )
    yield rec
    rec.close()


def test_create_user_profile(recommender):
    """Test user profile creation"""
    
    result = recommender.create_user_profile(
        user_id='test_user_123',
        initial_interests=['movies', 'sports', 'technology']
    )
    
    assert result['user_id'] == 'test_user_123'
    assert result['status'] == 'created'


def test_get_user_interests(recommender):
    """Test getting user interests"""
    
    # Create user first
    recommender.create_user_profile(
        user_id='test_user_456',
        initial_interests=['movies', 'food']
    )
    
    # Get interests
    interests = recommender.get_user_interests('test_user_456')
    
    assert len(interests) == 2
    assert all('category' in i for i in interests)
    assert all('score' in i for i in interests)


def test_update_user_interests(recommender):
    """Test updating user interests"""
    
    # Create user
    recommender.create_user_profile(
        user_id='test_user_789',
        initial_interests=['sports']
    )
    
    # Update interest
    recommender.update_user_interests(
        user_id='test_user_789',
        category='technology',
        action='like'
    )
    
    # Check updated interests
    interests = recommender.get_user_interests('test_user_789')
    
    categories = [i['category'] for i in interests]
    assert 'technology' in categories


def test_recommend_new_user(recommender):
    """Test recommendations for new user"""
    
    # Create new user
    recommender.create_user_profile(
        user_id='test_new_user',
        initial_interests=['movies', 'technology']
    )
    
    # Get recommendations
    results, metadata = recommender.recommend(
        user_id='test_new_user',
        query='best movies',
        limit=5
    )
    
    assert isinstance(results, list)
    assert metadata['is_new_user'] == True
    assert 'movies' in metadata['user_interests']


def test_track_interaction(recommender):
    """Test interaction tracking"""
    
    # Create user
    recommender.create_user_profile(
        user_id='test_track_user',
        initial_interests=['sports']
    )
    
    # Track interaction (need a valid post_id)
    # This test requires actual post data
    # recommender.track_interaction('test_track_user', 'post_001', 'like')


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])