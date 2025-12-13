import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
import re
from typing import List, Dict
import requests
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class CategoryManager:
    """
    CLASS 1: Category Management + LLaMA Training
    
    Responsibilities:
    1. Train categories using LLaMA on dataset
    2. Detect category from user query/content
    3. Calculate relevance scores for posts in each category
    4. Store category_scores in MongoDB
    """
    
    def __init__(
        self,
        mongo_uri: str,
        mongo_db: str,
        llama_api_url: str = 'http://localhost:11434',
        embedding_model: str = 'all-MiniLM-L6-v2'
    ):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_db]
        
        # Collections
        self.categories_collection = self.db['categories']
        self.posts_collection = self.db['posts']
        self.category_scores_collection = self.db['category_scores']
        
        # Services
        self.llama_api_url = llama_api_url
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Predefined categories with keywords
        self.category_keywords = {
            'movies': ['movie', 'film', 'cinema', 'actor', 'director', 'hollywood', 'bollywood'],
            'sports': ['sports', 'game', 'cricket', 'football', 'basketball', 'tennis', 'match'],
            'technology': ['tech', 'software', 'programming', 'code', 'ai', 'computer', 'app'],
            'food': ['food', 'recipe', 'cooking', 'restaurant', 'meal', 'cuisine', 'diet'],
            'travel': ['travel', 'trip', 'vacation', 'destination', 'tourism', 'hotel'],
            'music': ['music', 'song', 'concert', 'band', 'album', 'singer', 'festival'],
            'fashion': ['fashion', 'style', 'clothing', 'outfit', 'designer', 'trend'],
            'health': ['fitness', 'exercise', 'diet', 'nutrition', 'wellness', 'medical', 'doctor', 'hospital'],
            'education': ['education', 'learning', 'study', 'course', 'university', 'tutorial'],
            'business': ['business', 'startup', 'entrepreneur', 'marketing', 'company']
        }
        
        logger.info("✅ CategoryManager initialized")
        self.categories = list(self.category_keywords.keys())

    def train_categories_from_dataset(self, dataset_path: str):
        """
        Train categories using LLaMA on dataset
        Creates category_scores for all posts
        """
        logger.info(f"🤖 Training categories from dataset: {dataset_path}")
        
        try:
            # Load dataset
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)
            
            logger.info(f"📊 Loaded {len(dataset)} posts from dataset")
            
            # Process each post
            trained_count = 0
            
            for post in dataset:
                post_id = post.get('_id') or post.get('id')
                title = post.get('title', '')
                body = post.get('body', '')
                declared_category = post.get('category', '')
                
                # Combine text for analysis
                full_text = f"{title} {body}"
                
                # Method 1: Keyword-based scoring (fast)
                keyword_scores = self._calculate_keyword_scores(full_text)
                
                # Method 2: LLaMA-based category detection (accurate)
                llama_category = self._llama_detect_category(full_text)
                
                # Method 3: Semantic similarity (embedding-based)
                semantic_scores = self._calculate_semantic_scores(full_text)
                
                # Combine scores (weighted average)
                final_scores = {}
                for category in self.category_keywords.keys():
                    keyword_score = keyword_scores.get(category, 0.0)
                    semantic_score = semantic_scores.get(category, 0.0)
                    llama_boost = 0.3 if llama_category == category else 0.0
                    
                    # Weighted combination
                    final_scores[category] = (
                        0.3 * keyword_score +
                        0.4 * semantic_score +
                        0.3 * llama_boost
                    )
                
                # Store scores in category_scores collection
                for category, score in final_scores.items():
                    if score > 0.1:  # Only store meaningful scores
                        self.category_scores_collection.update_one(
                            {
                                'post_id': post_id,
                                'category': category
                            },
                            {
                                '$set': {
                                    'relevance_score': score,
                                    'trained_at': datetime.now(),
                                    'declared_category': declared_category,
                                    'llama_detected': llama_category
                                }
                            },
                            upsert=True
                        )
                
                trained_count += 1
                
                if trained_count % 10 == 0:
                    logger.info(f"   Trained {trained_count}/{len(dataset)} posts...")
            
            logger.info(f"✅ Training complete! Processed {trained_count} posts")
            
            # Update category statistics
            self._update_category_stats()
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise
    
    def _calculate_keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate category scores based on keyword matching"""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = min(matches / len(keywords), 1.0)
        
        return scores
    
    def _calculate_semantic_scores(self, text: str) -> Dict[str, float]:
        """Calculate category scores using semantic similarity"""
        # Generate embedding for text
        text_embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        
        scores = {}
        
        # Generate embeddings for each category (using keywords)
        for category, keywords in self.category_keywords.items():
            category_text = ' '.join(keywords)
            category_embedding = self.embedding_model.encode(
                category_text, 
                normalize_embeddings=True
            )
            
            # Cosine similarity
            similarity = float(text_embedding @ category_embedding.T)
            scores[category] = max(0.0, similarity)
        
        return scores
    
    def _llama_detect_category(self, text: str) -> str:
        """Use LLaMA to detect the most relevant category"""
        try:
            categories_list = ', '.join(self.category_keywords.keys())
            
            prompt = f"""Analyze this content and choose the MOST relevant category.

Content: "{text[:500]}"

Categories: {categories_list}

Reply with ONLY the category name, nothing else."""

            response = requests.post(
                f"{self.llama_api_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 10
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                detected = response.json()['response'].strip().lower()
                # Validate category
                if detected in self.category_keywords:
                    return detected
            
        except Exception as e:
            logger.warning(f"⚠️ LLaMA detection failed: {e}")
        
        return 'general'
    
    def _detect_category(self, text):
        """
        Detect category based on keywords.  
        You can expand or modify the keyword mapping anytime.
        """
        keyword_map = {
            "technology": ["tech", "mobile", "laptop", "ai", "software"],
            "finance": ["money", "loan", "bank", "investment"],
            "agriculture": ["farm", "crop", "soil", "tractor", "agriculture"],
            "health": ["doctor", "medicine", "health", "hospital"],
            "education": ["study", "school", "college", "exam"],
        }

        t = text.lower()
        for category, keywords in keyword_map.items():
            if any(k in t for k in keywords):
                return category

        return "other"

    def detect_query_category(self, query: str):
        """
        Detect category using keyword-based method.
        Always returns a dict:
        { "category": "...", "confidence": float }
        """
        detected = self._detect_category(query)

        # If nothing detected → general
        category = detected if detected else "general"

        # Ensure category exists in DB
        self.ensure_category_exists(category)

        return {
            "category": category,
            "confidence": 1.0
        }


    def ensure_category_exists(self, category: str):
        if not self.db.categories.find_one({"name": category}):
            self.db.categories.insert_one({
                "name": category,
                "created_at": datetime.utcnow(),
                "auto_created": True
            })
            print(f"[AUTO] Created new category: {category}")

    def get_category_top_posts(
        self,
        category: str,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Dict]:
        """
        Get top posts for a category based on trained scores
        """
        # Find high-scoring posts for this category
        top_scores = self.category_scores_collection.find(
            {
                'category': category,
                'relevance_score': {'$gte': min_score}
            }
        ).sort('relevance_score', -1).limit(limit * 2)
        
        posts = []
        seen_ids = set()
        
        for score_doc in top_scores:
            post_id = score_doc['post_id']
            
            if post_id in seen_ids:
                continue
            
            post = self.posts_collection.find_one({'_id': post_id})
            if post:
                posts.append({
                    'id': str(post['_id']),
                    'title': post.get('title', ''),
                    'category': post.get('category', ''),
                    'body': post.get('body', '')[:200],
                    'relevance_score': score_doc['relevance_score'],
                    'source': 'category_trained'
                })
                seen_ids.add(post_id)
                
                if len(posts) >= limit:
                    break
        
        return posts
    
    def _update_category_stats(self):
        """Update statistics for each category"""
        for category in self.category_keywords.keys():
            post_count = self.category_scores_collection.count_documents({
                'category': category,
                'relevance_score': {'$gte': 0.3}
            })
            
            self.categories_collection.update_one(
                {'name': category},
                {
                    '$set': {
                        'post_count': post_count,
                        'last_updated': datetime.now()
                    }
                },
                upsert=True
            )
    
    def get_all_categories(self) -> List[Dict]:
        """Get all available categories"""
        categories = list(self.categories_collection.find())
        return [
            {
                'name': cat['name'],
                'post_count': cat.get('post_count', 0),
                'last_updated': cat.get('last_updated')
            }
            for cat in categories
        ]
    
    def close(self):
        """Close connections"""
        if self.mongo_client:
            self.mongo_client.close()


# Example usage
if __name__ == '__main__':
    manager = CategoryManager(
        mongo_uri='mongodb://localhost:27017/',
        mongo_db='recommendation_db'
    )
    
    # Train from dataset (one-time operation)
    # manager.train_categories_from_dataset('data/llama_dataset.json')
    
    # Test category detection
    test_queries = [
        "best movies to watch this weekend",
        "how to cook pasta at home",
        "latest cricket match highlights"
    ]
    
    for query in test_queries:
        detected = manager.detect_query_category(query)
        print(f"\nQuery: {query}")
        print(f"Detected: {detected}")
        
        if detected:
            top_category = detected[0]['category']
            posts = manager.get_category_top_posts(top_category, limit=5)
            print(f"Top posts in '{top_category}':")
            for post in posts:
                print(f"  - {post['title']} (score: {post['relevance_score']:.2f})")
    
    manager.close()