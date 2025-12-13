#!/usr/bin/env python3
"""
Populate MongoDB with sample data for testing the recommendation system
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import random

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "recommendation_db"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Sample data
CATEGORIES = ["technology", "sports", "entertainment", "science", "politics", "health", "travel", "food"]
SUBREDDITS = ["python", "machinelearning", "datascience", "webdev", "programming", "technology", "sports", "movies"]

USER_INTERESTS = [
    ["technology", "science", "programming"],
    ["sports", "health", "travel"],
    ["entertainment", "movies", "food"],
    ["technology", "datascience", "machinelearning"],
    ["politics", "science", "health"],
    ["travel", "food", "entertainment"],
    ["programming", "webdev", "technology"],
    ["sports", "health", "fitness"]
]

POST_TITLES = [
    "Introduction to Machine Learning",
    "Best Python Libraries for Data Science",
    "How to Build a Recommendation System",
    "Top 10 Travel Destinations in 2025",
    "Healthy Meal Prep Ideas",
    "Latest Sports News and Updates",
    "Movie Reviews: Top Films This Year",
    "Getting Started with Web Development",
    "Understanding Neural Networks",
    "Tips for Better Code Quality",
    "The Future of AI Technology",
    "Workout Routines for Beginners",
    "Cooking with Seasonal Ingredients",
    "Breaking: Science Discovery",
    "Political Analysis 2025",
    "Healthcare Innovation Trends",
    "Adventure Travel Guide",
    "Restaurant Reviews",
    "Tech Gadgets Worth Buying",
    "Programming Best Practices"
]

def clear_collections():
    """Clear existing data"""
    print("🗑️  Clearing existing collections...")
    db.users.delete_many({})
    db.posts.delete_many({})
    db.interactions.delete_many({})
    db.category_scores.delete_many({})
    print("✅ Collections cleared")

def create_users(num_users=20):
    """Create sample users"""
    print(f"👥 Creating {num_users} users...")
    users = []
    for i in range(num_users):
        user = {
            "user_id": f"user_{i+1}",
            "name": f"User {i+1}",
            "username": f"username{i+1}",
            "email": f"user{i+1}@example.com",
            "interests": random.choice(USER_INTERESTS),
            "labels": random.sample(CATEGORIES, k=random.randint(2, 4)),
            "created_at": datetime.now() - timedelta(days=random.randint(1, 365))
        }
        users.append(user)
    
    result = db.users.insert_many(users)
    print(f"✅ Created {len(result.inserted_ids)} users")
    return [u["user_id"] for u in users]

def create_posts(num_posts=50):
    """Create sample posts"""
    print(f"📝 Creating {num_posts} posts...")
    posts = []
    for i in range(num_posts):
        category = random.choice(CATEGORIES)
        post = {
            "title": random.choice(POST_TITLES),
            "content": f"This is sample content for post {i+1}. " * 5,
            "category": category,
            "subreddit": random.choice(SUBREDDITS),
            "author": f"user_{random.randint(1, 10)}",
            "upvotes": random.randint(0, 1000),
            "downvotes": random.randint(0, 100),
            "created_at": datetime.now() - timedelta(days=random.randint(1, 180)),
            "tags": random.sample(CATEGORIES, k=random.randint(1, 3))
        }
        posts.append(post)
    
    result = db.posts.insert_many(posts)
    print(f"✅ Created {len(result.inserted_ids)} posts")
    return [str(pid) for pid in result.inserted_ids]

def create_interactions(user_ids, post_ids, num_interactions=200):
    """Create sample interactions"""
    print(f"🔗 Creating {num_interactions} interactions...")
    interactions = []
    interaction_types = ["view", "click", "like", "share"]
    
    for i in range(num_interactions):
        interaction = {
            "user_id": random.choice(user_ids),
            "post_id": random.choice(post_ids),
            "item_id": random.choice(post_ids),  # Alternate field name
            "interaction_type": random.choice(interaction_types),
            "timestamp": datetime.now() - timedelta(days=random.randint(1, 90)),
            "duration_seconds": random.randint(10, 600) if random.random() > 0.5 else None
        }
        interactions.append(interaction)
    
    result = db.interactions.insert_many(interactions)
    print(f"✅ Created {len(result.inserted_ids)} interactions")

def create_category_scores(user_ids, post_ids, num_scores=100):
    """Create sample category scores (as fallback)"""
    print(f"⭐ Creating {num_scores} category scores...")
    scores = []
    
    for i in range(num_scores):
        score_doc = {
            "user_id": random.choice(user_ids),
            "item_id": random.choice(post_ids),
            "post_id": random.choice(post_ids),
            "score": round(random.uniform(1.0, 5.0), 1),
            "rating": round(random.uniform(1.0, 5.0), 1),
            "timestamp": datetime.now() - timedelta(days=random.randint(1, 60)),
            "category": random.choice(CATEGORIES)
        }
        scores.append(score_doc)
    
    result = db.category_scores.insert_many(scores)
    print(f"✅ Created {len(result.inserted_ids)} category scores")

def show_stats():
    """Show database statistics"""
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)
    print(f"Users: {db.users.count_documents({})}")
    print(f"Posts: {db.posts.count_documents({})}")
    print(f"Interactions: {db.interactions.count_documents({})}")
    print(f"Category Scores: {db.category_scores.count_documents({})}")
    print("="*60)
    
    # Show sample data
    print("\n📌 Sample User:")
    user = db.users.find_one()
    if user:
        print(f"  ID: {user.get('user_id')}")
        print(f"  Name: {user.get('name')}")
        print(f"  Interests: {user.get('interests')}")
    
    print("\n📌 Sample Post:")
    post = db.posts.find_one()
    if post:
        print(f"  ID: {post.get('_id')}")
        print(f"  Title: {post.get('title')}")
        print(f"  Category: {post.get('category')}")
    
    print("\n📌 Sample Interaction:")
    interaction = db.interactions.find_one()
    if interaction:
        print(f"  User: {interaction.get('user_id')}")
        print(f"  Post: {interaction.get('post_id')}")
        print(f"  Type: {interaction.get('interaction_type')}")

def main():
    print("="*60)
    print("🚀 MONGODB SAMPLE DATA GENERATOR")
    print("="*60)
    
    # Clear existing data
    clear_collections()
    
    # Create sample data
    user_ids = create_users(num_users=20)
    post_ids = create_posts(num_posts=50)
    create_interactions(user_ids, post_ids, num_interactions=200)
    create_category_scores(user_ids, post_ids, num_scores=100)
    
    # Show statistics
    show_stats()
    
    print("\n✅ Sample data creation complete!")
    print("💡 Now run: python sync_mongodb_to_gorse.py")
    
    client.close()

if __name__ == "__main__":
    main()
