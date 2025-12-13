#!/usr/bin/env python3
"""
Debug script to test user creation directly
"""

import sys
sys.path.insert(0, '/home/thalavai-manikandan/Desktop/Recommendation_System')

from pymongo import MongoClient
from datetime import datetime

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "recommendation_db"

def test_direct_insert():
    """Test direct MongoDB insert"""
    
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    print("=" * 60)
    print("🔍 DIRECT MONGODB INSERT TEST")
    print("=" * 60)
    
    # Delete test user
    db.users.delete_one({"user_id": "direct_test_user"})
    
    # Insert directly
    user_doc = {
        'user_id': 'direct_test_user',
        'interests': ['movies', 'sports', 'food'],
        'created_at': datetime.now(),
        'onboarding_completed': True,
        'updated_at': datetime.now()
    }
    
    result = db.users.insert_one(user_doc)
    print(f"\n✅ Insert result: {result.inserted_id}")
    
    # Retrieve and verify
    user = db.users.find_one({"user_id": "direct_test_user"})
    print(f"\n📄 Retrieved user:")
    print(f"   user_id: {user.get('user_id')}")
    print(f"   interests: {user.get('interests')}")
    print(f"   created_at: {user.get('created_at')}")
    print(f"   onboarding_completed: {user.get('onboarding_completed')}")
    
    # Check if interests field exists
    if 'interests' in user:
        print(f"\n✅ SUCCESS: interests field saved correctly!")
        print(f"   Length: {len(user['interests'])}")
    else:
        print(f"\n❌ FAILED: interests field missing!")
    
    print("=" * 60)


def test_via_recommender():
    """Test via HybridRecommender class"""
    
    try:
        from models.hybrid_recommender import HybridRecommender
        from models.category_manager import CategoryManager
        from config.config import Config
        
        print("\n" + "=" * 60)
        print("🔍 HYBRID RECOMMENDER TEST")
        print("=" * 60)
        
        # Initialize
        category_manager = CategoryManager(
            mongo_uri=MONGO_URI,
            mongo_db=MONGO_DB
        )
        
        recommender = HybridRecommender(
            mongo_uri=MONGO_URI,
            mongo_db=MONGO_DB,
            gorse_api_url="http://localhost:8087",
            category_manager=category_manager,
            embedding_model=Config.EMBEDDING_MODEL
        )
        
        print(f"\n✅ Recommender initialized")
        print(f"   Users collection: {recommender.users_collection.name}")
        print(f"   Database: {recommender.db.name}")
        
        # Create user
        result = recommender.create_user_profile(
            user_id="recommender_test_user",
            initial_interests=["technology", "sports", "food"]
        )
        
        print(f"\n✅ create_user_profile returned:")
        print(f"   {result}")
        
        # Check in database
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        user = db.users.find_one({"user_id": "recommender_test_user"})
        
        print(f"\n📄 Database check:")
        if user:
            print(f"   user_id: {user.get('user_id')}")
            print(f"   interests: {user.get('interests')}")
            
            if 'interests' in user:
                print(f"\n✅ SUCCESS: Recommender saves interests correctly!")
            else:
                print(f"\n❌ FAILED: Recommender doesn't save interests!")
                print(f"   Full document: {user}")
        else:
            print(f"\n❌ User not found in database!")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting debug tests...\n")
    
    # Test 1: Direct MongoDB insert
    test_direct_insert()
    
    # Test 2: Via HybridRecommender
    test_via_recommender()
    
    print("\n✅ Debug tests complete!")