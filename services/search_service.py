"""
Hybrid Search Service
Combines your LLaMA category extraction with keyword-based search
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.categories import (
    CATEGORY_KEYWORDS, 
    normalize_category, 
    is_valid_category
)
from utils.scoring import calculate_combined_scores, rank_posts, paginate_posts


class CategoryDetector:
    """Fast keyword-based category detection for search queries"""
    
    def __init__(self):
        self.categories = CATEGORY_KEYWORDS
    
    def detect(self, query):
        """
        Detect category from query using keyword matching
        Fast for real-time search
        
        Args:
            query: Search query string
        
        Returns:
            tuple: (category, confidence)
        """
        if not query:
            return 'other', 0.0
        
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Check each category's keywords
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in query_lower:
                    word_count = len(keyword.split())
                    score += word_count
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'matched_keywords': matched_keywords
                }
        
        if not category_scores:
            return 'other', 0.3
        
        # Get category with highest score
        best_category = max(category_scores, key=lambda x: category_scores[x]['score'])
        best_score = category_scores[best_category]['score']
        
        # Calculate confidence
        max_possible_score = len(query_words)
        confidence = min(best_score / max_possible_score, 1.0)
        
        # Boost confidence if multiple keywords matched
        keyword_count = len(category_scores[best_category]['matched_keywords'])
        if keyword_count > 1:
            confidence = min(confidence * 1.2, 1.0)
        
        return best_category, round(confidence, 2)


class SearchService:
    """
    Hybrid Search Service
    - Uses keyword detection for fast search queries
    - Can integrate with your LLaMA service for post analysis
    """
    
    def __init__(self, db):
        """
        Initialize search service
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.posts_collection = db.posts
        self.users_collection = db.users
        self.detector = CategoryDetector()
    
    def search(self, query, user_id=None, page=1, per_page=10, use_llama_categories=False):
        """
        Search posts with smart category detection and ranking
        
        Args:
            query: Search query string
            user_id: User ID (optional)
            page: Page number
            per_page: Results per page
            use_llama_categories: If True, also search using LLaMA-extracted categories from posts
        
        Returns:
            dict: Search results with metadata
        """
        # Detect category from query (keyword-based, fast)
        category, confidence = self.detector.detect(query)
        
        # Fetch relevant posts
        posts = self._fetch_posts(category, query, use_llama_categories)
        
        if not posts:
            # Fallback to popular posts
            posts = self._fetch_popular_posts(per_page * 3)
        
        # Rank posts by combined score
        ranked_posts = rank_posts(posts, query=query, sort_by='combined_score')
        
        # Paginate results
        paginated = paginate_posts(ranked_posts, page, per_page)
        
        # Update user interests if user_id provided
        interest_added = False
        if user_id and confidence >= 0.5:
            interest_added = self._update_user_interests(user_id, category, confidence)
            self._log_search(user_id, query, category, confidence)
        
        # Format results
        formatted_results = []
        for post in paginated['posts']:
            formatted_results.append({
                '_id': str(post.get('_id', '')),
                'title': post.get('title', ''),
                'body': post.get('body', ''),
                'category': post.get('category', ''),
                'author_id': post.get('author_id', ''),
                'views': post.get('views', 0),
                'likes': post.get('likes', 0),
                'tags': post.get('tags', []),
                'core_categories': post.get('core_categories', []),  # From your LLaMA analysis
                'final_tags': post.get('final_tags', []),  # From your LLaMA analysis
                'created_at': self._format_date(post.get('created_at', '')),
                'relevance_score': round(post.get('relevance_score', 0), 3),
                'popularity_score': round(post.get('popularity_score', 0), 1),
                'combined_score': round(post.get('combined_score', 0), 3),
                'match_reason': f"Relevant to {category}"
            })
        
        return {
            'status': 'success',
            'query': query,
            'detected_categories': [{
                'category': category,
                'confidence': confidence
            }],
            'results': formatted_results,
            'metadata': {
                'query_category': category,
                'category_confidence': confidence,
                'interest_added': interest_added,
                'page': paginated['page'],
                'per_page': paginated['per_page'],
                'total_results': paginated['total'],
                'total_pages': paginated['total_pages'],
                'has_next': paginated['has_next'],
                'has_prev': paginated['has_prev'],
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _fetch_posts(self, category, query=None, use_llama_categories=False):
        """
        Fetch posts from database
        Can search by main category or LLaMA-extracted categories
        """
        posts = []
        
        # Search by main category
        category_posts = list(self.posts_collection.find({'category': category}))
        posts.extend(category_posts)
        
        # Also search by LLaMA core_categories or final_tags
        if use_llama_categories:
            llama_posts = list(self.posts_collection.find({
                '$or': [
                    {'core_categories': category},
                    {'core_categories': {'$in': [category]}},
                    {'final_tags': category},
                    {'final_tags': {'$in': [category]}}
                ]
            }))
            posts.extend(llama_posts)
        
        # If few results, text search
        if len(posts) < 20 and query:
            query_words = query.lower().split()
            regex_pattern = '|'.join(query_words)
            
            text_posts = list(self.posts_collection.find({
                '$or': [
                    {'title': {'$regex': regex_pattern, '$options': 'i'}},
                    {'body': {'$regex': regex_pattern, '$options': 'i'}},
                    {'tags': {'$in': query_words}},
                    {'core_categories': {'$in': query_words}},
                    {'final_tags': {'$in': query_words}}
                ]
            }).limit(20))
            posts.extend(text_posts)
        
        # Remove duplicates
        seen_ids = set()
        unique_posts = []
        for post in posts:
            post_id = str(post.get('_id', ''))
            if post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        return unique_posts
    
    def _fetch_popular_posts(self, limit=30):
        """Fetch popular posts as fallback"""
        return list(self.posts_collection.find().sort([
            ('likes', -1),
            ('views', -1)
        ]).limit(limit))
    
    def _update_user_interests(self, user_id, category, confidence):
        """Add new interest to user profile"""
        if confidence < 0.5:
            return False
        
        # Normalize category before storing
        normalized_category = normalize_category(category)
        
        user = self.users_collection.find_one({'user_id': user_id})
        
        if not user:
            # Create new user
            self.users_collection.insert_one({
                'user_id': user_id,
                'interests': [normalized_category],
                'search_history': [],
                'created_at': datetime.utcnow()
            })
            return True
        
        interests = user.get('interests', [])
        
        if normalized_category not in interests:
            self.users_collection.update_one(
                {'user_id': user_id},
                {
                    '$push': {'interests': normalized_category},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            return True
        
        return False
    
    def _log_search(self, user_id, query, category, confidence):
        """Log user search for analytics"""
        self.users_collection.update_one(
            {'user_id': user_id},
            {
                '$push': {
                    'search_history': {
                        '$each': [{
                            'query': query,
                            'category': normalize_category(category),
                            'confidence': confidence,
                            'timestamp': datetime.utcnow()
                        }],
                        '$slice': -50
                    }
                }
            },
            upsert=True
        )
    
    def get_recommendations(self, user_id, page=1, per_page=10):
        """Get personalized recommendations for user"""
        user = self.users_collection.find_one({'user_id': user_id})
        
        if not user or not user.get('interests'):
            posts = self._fetch_popular_posts(per_page * 3)
        else:
            interests = user['interests']
            
            # Search by category and LLaMA tags
            posts = list(self.posts_collection.find({
                '$or': [
                    {'category': {'$in': interests}},
                    {'core_categories': {'$in': interests}},
                    {'final_tags': {'$in': interests}}
                ]
            }))
        
        # Rank by popularity
        ranked_posts = rank_posts(posts, sort_by='popularity_score')
        
        # Paginate
        paginated = paginate_posts(ranked_posts, page, per_page)
        
        # Format results
        formatted_results = []
        for post in paginated['posts']:
            formatted_results.append({
                '_id': str(post.get('_id', '')),
                'title': post.get('title', ''),
                'body': post.get('body', ''),
                'category': post.get('category', ''),
                'views': post.get('views', 0),
                'likes': post.get('likes', 0),
                'tags': post.get('tags', []),
                'core_categories': post.get('core_categories', []),
                'created_at': self._format_date(post.get('created_at', ''))
            })
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommendations': formatted_results,
            'page': paginated['page'],
            'per_page': paginated['per_page'],
            'total': paginated['total'],
            'total_pages': paginated['total_pages'],
            'has_next': paginated['has_next'],
            'has_prev': paginated['has_prev']
        }
    
    def get_user_interests(self, user_id):
        """Get user's interests and search history"""
        user = self.users_collection.find_one({'user_id': user_id})
        
        if not user:
            return {
                'status': 'error',
                'message': 'User not found'
            }
        
        return {
            'status': 'success',
            'user_id': user_id,
            'interests': user.get('interests', []),
            'total_interests': len(user.get('interests', [])),
            'search_history': user.get('search_history', [])[-20:],
            'total_searches': len(user.get('search_history', []))
        }
    
    def detect_category(self, query):
        """Detect category from query with details"""
        category, confidence = self.detector.detect(query)
        
        query_lower = query.lower()
        matched_keywords = []
        
        normalized_category = normalize_category(category)
        if normalized_category in CATEGORY_KEYWORDS:
            for keyword in CATEGORY_KEYWORDS[normalized_category]:
                if keyword in query_lower:
                    matched_keywords.append(keyword)
        
        return {
            'status': 'success',
            'query': query,
            'primary_category': normalized_category,
            'confidence': confidence,
            'matched_keywords': matched_keywords[:10]
        }
    
    def _format_date(self, date_obj):
        """Format date object to ISO string"""
        if hasattr(date_obj, 'isoformat'):
            return date_obj.isoformat()
        return str(date_obj)