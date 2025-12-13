# models/user_manager.py

import logging
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING

logger = logging.getLogger(__name__)


class UserManager:
    """
    User Management Class
    
    Handles:
    - User CRUD operations
    - User statistics
    - User preferences
    """
    
    def __init__(self, mongo_uri: str, mongo_db: str):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_db]
        
        self.users_collection = self.db['users']
        self.user_interests_collection = self.db['user_interests']
        self.interactions_collection = self.db['interactions']
        
        # Create indexes
        self.users_collection.create_index([("user_id", ASCENDING)], unique=True)
        self.user_interests_collection.create_index([
            ("user_id", ASCENDING),
            ("category", ASCENDING)
        ], unique=True)
        self.interactions_collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        
        logger.info("✅ UserManager initialized")
    
    def create_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new user"""
        
        user_doc = {
            'user_id': user_id,
            'name': name,
            'email': email,
            'created_at': datetime.now(),
            'last_active': datetime.now(),
            'metadata': metadata or {}
        }
        
        try:
            self.users_collection.insert_one(user_doc)
            logger.info(f"✅ Created user: {user_id}")
            return {'status': 'created', 'user_id': user_id}
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        user = self.users_collection.find_one({'user_id': user_id})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    def update_last_active(self, user_id: str):
        """Update user's last active timestamp"""
        self.users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_active': datetime.now()}}
        )
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        
        user = self.get_user(user_id)
        if not user:
            return {'error': 'User not found'}
        
        # Get interests
        interests = list(
            self.user_interests_collection.find({'user_id': user_id})
            .sort('score', DESCENDING)
        )
        
        # Get interaction counts
        total_interactions = self.interactions_collection.count_documents({
            'user_id': user_id
        })
        
        views = self.interactions_collection.count_documents({
            'user_id': user_id,
            'action': 'view'
        })
        
        likes = self.interactions_collection.count_documents({
            'user_id': user_id,
            'action': 'like'
        })
        
        # Get category breakdown
        category_interactions = {}
        for interest in interests:
            cat = interest['category']
            count = self.interactions_collection.count_documents({
                'user_id': user_id,
                'category': cat
            })
            category_interactions[cat] = count
        
        return {
            'user_id': user_id,
            'name': user.get('name'),
            'created_at': user.get('created_at'),
            'last_active': user.get('last_active'),
            'total_interactions': total_interactions,
            'views': views,
            'likes': likes,
            'interests': [
                {
                    'category': i['category'],
                    'score': i['score'],
                    'interactions': category_interactions.get(i['category'], 0)
                }
                for i in interests
            ]
        }
    
    def delete_user(self, user_id: str) -> Dict:
        """Delete user and all associated data"""
        try:
            # Delete user document
            self.users_collection.delete_one({'user_id': user_id})
            
            # Delete interests
            self.user_interests_collection.delete_many({'user_id': user_id})
            
            # Delete interactions
            self.interactions_collection.delete_many({'user_id': user_id})
            
            logger.info(f"✅ Deleted user: {user_id}")
            return {'status': 'deleted', 'user_id': user_id}
        
        except Exception as e:
            logger.error(f"❌ Failed to delete user: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def list_users(self, limit: int = 100) -> List[Dict]:
        """List all users"""
        users = list(
            self.users_collection.find()
            .limit(limit)
            .sort('created_at', DESCENDING)
        )
        
        for user in users:
            user['_id'] = str(user['_id'])
        
        return users
    
    def close(self):
        """Close database connection"""
        if self.mongo_client:
            self.mongo_client.close()