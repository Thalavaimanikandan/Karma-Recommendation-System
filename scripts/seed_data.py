#!/usr/bin/env python3
"""
Complete data seeding script - creates posts, users, and interactions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'recommendation_db'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def create_sample_users():
    """Create sample users with varied interests"""
    users = [
        {
            "user_id": "user_001",
            "username": "movie_buff",
            "email": "moviebuff@example.com",
            "created_at": datetime.now() - timedelta(days=90),
            "preferences": {
                "categories": ["movies", "entertainment"]
            }
        },
        {
            "user_id": "user_002",
            "username": "tech_enthusiast",
            "email": "techie@example.com",
            "created_at": datetime.now() - timedelta(days=85),
            "preferences": {
                "categories": ["technology", "science"]
            }
        },
        {
            "user_id": "user_003",
            "username": "sports_fan",
            "email": "sportsfan@example.com",
            "created_at": datetime.now() - timedelta(days=80),
            "preferences": {
                "categories": ["sports", "fitness"]
            }
        },
        {
            "user_id": "user_004",
            "username": "foodie_explorer",
            "email": "foodie@example.com",
            "created_at": datetime.now() - timedelta(days=75),
            "preferences": {
                "categories": ["food", "travel"]
            }
        },
        {
            "user_id": "user_005",
            "username": "music_lover",
            "email": "musiclover@example.com",
            "created_at": datetime.now() - timedelta(days=70),
            "preferences": {
                "categories": ["music", "entertainment"]
            }
        },
        {
            "user_id": "user_006",
            "username": "gamer_pro",
            "email": "gamer@example.com",
            "created_at": datetime.now() - timedelta(days=65),
            "preferences": {
                "categories": ["technology", "entertainment"]
            }
        },
        {
            "user_id": "user_007",
            "username": "travel_addict",
            "email": "traveler@example.com",
            "created_at": datetime.now() - timedelta(days=60),
            "preferences": {
                "categories": ["travel", "photography"]
            }
        },
        {
            "user_id": "user_008",
            "username": "fitness_guru",
            "email": "fitness@example.com",
            "created_at": datetime.now() - timedelta(days=55),
            "preferences": {
                "categories": ["sports", "health"]
            }
        },
        {
            "user_id": "user_009",
            "username": "art_enthusiast",
            "email": "artist@example.com",
            "created_at": datetime.now() - timedelta(days=50),
            "preferences": {
                "categories": ["hobby", "entertainment"]
            }
        },
        {
            "user_id": "user_010",
            "username": "bookworm",
            "email": "bookworm@example.com",
            "created_at": datetime.now() - timedelta(days=45),
            "preferences": {
                "categories": ["hobby", "education"]
            }
        }
    ]
    
    db.users.delete_many({})
    db.users.insert_many(users)
    logger.info(f"✅ Inserted {len(users)} sample users")
    return users


def create_sample_interactions():
    """Create realistic user interactions with posts"""
    
    # Get all posts and users
    posts = list(db.posts.find({}))
    users = list(db.users.find({}))
    
    if not posts or not users:
        logger.error("❌ No posts or users found. Run seed_data.py first!")
        return
    
    interactions = []
    interaction_types = ["view", "like", "click", "share", "comment"]
    
    # Generate interactions based on user preferences
    for user in users:
        user_id = user["user_id"]
        user_categories = user.get("preferences", {}).get("categories", [])
        
        # Each user interacts with 5-15 posts
        num_interactions = random.randint(5, 15)
        
        # 70% interactions with preferred categories, 30% random
        preferred_posts = [p for p in posts if p.get("category") in user_categories]
        random_posts = [p for p in posts if p.get("category") not in user_categories]
        
        selected_posts = []
        
        # Add preferred posts (70%)
        if preferred_posts:
            selected_posts.extend(random.sample(
                preferred_posts, 
                min(int(num_interactions * 0.7), len(preferred_posts))
            ))
        
        # Add random posts (30%)
        if random_posts and len(selected_posts) < num_interactions:
            remaining = num_interactions - len(selected_posts)
            selected_posts.extend(random.sample(
                random_posts,
                min(remaining, len(random_posts))
            ))
        
        # Create interactions with varied timestamps
        for i, post in enumerate(selected_posts):
            # More recent interactions have higher probability
            days_ago = random.randint(1, 30)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Interaction type probabilities: view (50%), like (25%), click (15%), share (5%), comment (5%)
            rand = random.random()
            if rand < 0.5:
                interaction_type = "view"
            elif rand < 0.75:
                interaction_type = "like"
            elif rand < 0.9:
                interaction_type = "click"
            elif rand < 0.95:
                interaction_type = "share"
            else:
                interaction_type = "comment"
            
            interaction = {
                "user_id": user_id,
                "post_id": post["_id"],
                "interaction_type": interaction_type,
                "timestamp": timestamp,
                "created_at": timestamp
            }
            interactions.append(interaction)
    
    # Clear existing interactions and insert new ones
    db.interactions.delete_many({})
    db.interactions.insert_many(interactions)
    logger.info(f"✅ Inserted {len(interactions)} sample interactions")
    
    # Show statistics
    logger.info("\n📊 Interaction statistics:")
    for itype in interaction_types:
        count = len([i for i in interactions if i["interaction_type"] == itype])
        logger.info(f"   {itype}: {count} interactions")


def create_user_interests():
    """Calculate and store user interests based on interactions"""
    
    users = list(db.users.find({}))
    
    for user in users:
        user_id = user["user_id"]
        
        # Get user's interactions
        interactions = list(db.interactions.find({"user_id": user_id}))
        
        # Calculate category scores
        category_scores = {}
        
        for interaction in interactions:
            post = db.posts.find_one({"_id": interaction["post_id"]})
            if post:
                category = post.get("category", "general")
                
                # Weight different interaction types
                weights = {
                    "view": 1,
                    "click": 2,
                    "like": 3,
                    "share": 4,
                    "comment": 5
                }
                weight = weights.get(interaction["interaction_type"], 1)
                
                category_scores[category] = category_scores.get(category, 0) + weight
        
        # Normalize scores
        if category_scores:
            max_score = max(category_scores.values())
            for cat in category_scores:
                category_scores[cat] = round(category_scores[cat] / max_score, 2)
        
        # Store user interests
        interests = [
            {
                "category": cat,
                "score": score
            }
            for cat, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Clear existing interests and insert new ones
        db.user_interests.delete_many({"user_id": user_id})
        
        for interest in interests:
            db.user_interests.insert_one({
                "user_id": user_id,
                "category": interest["category"],
                "score": interest["score"],
                "updated_at": datetime.now()
            })
    
    logger.info(f"✅ Calculated interests for {len(users)} users")


def show_statistics():
    """Show database statistics"""
    logger.info("\n" + "="*60)
    logger.info("📊 DATABASE STATISTICS")
    logger.info("="*60)
    
    posts_count = db.posts.count_documents({})
    users_count = db.users.count_documents({})
    interactions_count = db.interactions.count_documents({})
    interests_count = db.user_interests.count_documents({})
    
    logger.info(f"   Posts: {posts_count}")
    logger.info(f"   Users: {users_count}")
    logger.info(f"   Interactions: {interactions_count}")
    logger.info(f"   User Interests: {interests_count}")
    logger.info("="*60 + "\n")


def main():
    logger.info("="*60)
    logger.info("🌱 COMPLETE DATA SEEDING")
    logger.info("="*60)
    
    # Create users
    create_sample_users()
    
    # Create interactions
    create_sample_interactions()
    
    # Calculate user interests
    create_user_interests()
    
    # Show statistics
    show_statistics()
    
    logger.info("✅ Complete data seeding finished!")
    
    client.close()


if __name__ == "__main__":
    main()