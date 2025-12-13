import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient,models
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)

class HybridRecommender:
    """
    CLASS 2: Hybrid Recommendation Engine
    
    Combines:
    1. Category-based filtering (from CategoryManager)
    2. Gorse collaborative filtering
    3. User interest tracking
    4. Qdrant semantic search
    
    Flow:
    - New users → Interest-based recommendations (high-score posts)
    - Existing users → Personalized (Gorse + Category + Semantic)
    """
    
    def __init__(
            self,
            mongo_uri: str,
            mongo_db: str,
            gorse_api_url: str,
            category_manager,  # Inject CategoryManager
            embedding_model: str = 'all-MiniLM-L6-v2'
        ):
            self.mongo_client = MongoClient(mongo_uri)
            self.db = self.mongo_client[mongo_db]  # ✅ Fixed: was 'client'
            
            # Collections
            self.posts_collection = self.db['posts']
            self.users_collection = self.db['users']
            self.user_interests_collection = self.db['user_interests']
            self.interactions_collection = self.db['interactions']
            self.category_scores_collection = self.db['category_scores']
            
            # Services
            self.gorse_api_url = gorse_api_url
            self.category_manager = category_manager
            self.embedding_model = SentenceTransformer(embedding_model)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            # self.embedding_dim = 384  # ← Remove duplicate, using get_sentence_embedding_dimension() above
            
            # Qdrant
            self.qdrant_client = QdrantClient(host='localhost', port=6333)
            self.collection_name = f"{mongo_db}_posts"
            
            self._init_qdrant()
            
            logger.info("✅ HybridRecommender initialized")
            # Fix for models/hybrid_recommender.py

    def _init_qdrant(self):
        """Initialize Qdrant collection with robust error handling"""
        try:
            # Check if collection exists using a simpler method
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                print(f"✅ Using existing collection: {self.collection_name}")
                return
            
            # Collection doesn't exist, create it
            print(f"📦 Creating new collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_dim,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✅ Collection created successfully")
            
        except qdrant_exceptions.UnexpectedResponse as e:
            # Handle 409 Conflict (collection already exists)
            if "409" in str(e) or "already exists" in str(e).lower():
                print(f"✅ Collection {self.collection_name} already exists")
                return
            raise
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for version mismatch
            if "ValidationError" in error_msg or "pydantic" in error_msg.lower():
                print(f"\n❌ QDRANT VERSION MISMATCH ERROR")
                print(f"   Your qdrant-client version is incompatible with the Qdrant server")
                print(f"\n   🔧 Fix: Run this command:")
                print(f"      pip install qdrant-client --upgrade")
                print(f"\n   Alternative: pip install qdrant-client==1.7.0\n")
                
            raise Exception(f"Qdrant initialization failed: {error_msg}")

    def create_user_profile(
        self,
        user_id: str,
        initial_interests: List[str]
    ) -> Dict:
        """
        Create user profile with 3 initial interests
        
        Args:
            user_id: Unique user identifier
            initial_interests: List of 3 category names
        """
        logger.info(f"👤 Creating profile for user: {user_id}")
        logger.info(f"   Initial interests: {initial_interests}")
        
        # Create user document
        user_doc = {
                'user_id': user_id,
                'interests':initial_interests,  # ← இது add பண்ணுங்க!
                'created_at': datetime.now(),
                'onboarding_completed': True,
                'updated_at': datetime.now()
            }
        
        self.users_collection.update_one(
            {'user_id': user_id},
            {'$set': user_doc},
            upsert=True
        )
        
        # Create interest entries (separate collection for scalability)
        for category in initial_interests[:3]:  # Ensure max 3
            self.user_interests_collection.update_one(
                {
                    'user_id': user_id,
                    'category': category.lower()
                },
                {
                    '$set': {
                        'score': 10.0,  # Initial high score
                        'last_updated': datetime.now(),
                        'interaction_count': 0
                    }
                },
                upsert=True
            )
        
        # Send initial interests to Gorse
        self._send_to_gorse_user(user_id, initial_interests)
        
        logger.info(f"✅ User profile created: {user_id}")
        
        return {
            'user_id': user_id,
            'interests': initial_interests,
            'status': 'created'
        }
    
    def get_user_interests(self, user_id: str) -> List[Dict]:
        """Get user's current interests with scores"""
        interests = list(
            self.user_interests_collection.find({'user_id': user_id})
            .sort('score', -1)
        )
        
        return [
            {
                'category': i['category'],
                'score': i['score'],
                'interaction_count': i.get('interaction_count', 0)
            }
            for i in interests
        ]
    
    def update_user_interests(
        self,
        user_id: str,
        category: str,
        action: str = 'view',
        decay_factor: float = 0.95
    ):
        """
        Update user interest scores based on interactions
        
        Actions:
        - view: +1.0
        - click: +2.0
        - like: +3.0
        - share: +4.0
        """
        action_weights = {
            'view': 1.0,
            'click': 2.0,
            'like': 3.0,
            'share': 4.0
        }
        
        weight = action_weights.get(action, 1.0)
        
        # Decay all interests (temporal dynamics)
        self.user_interests_collection.update_many(
            {'user_id': user_id},
            {
                '$mul': {'score': decay_factor},
                '$set': {'last_updated': datetime.now()}
            }
        )
        
        # Boost current category
        self.user_interests_collection.update_one(
            {
                'user_id': user_id,
                'category': category.lower()
            },
            {
                '$inc': {
                    'score': weight,
                    'interaction_count': 1
                },
                '$set': {'last_updated': datetime.now()}
            },
            upsert=True
        )
        
        logger.info(f"📊 Updated interest: {user_id} → {category} (+{weight})")
 

    def is_safe_query(query: str) -> bool:
            """Check if query is safe"""
            query_lower = query.lower()
            for term in BLOCKED_TERMS:
                if term in query_lower:
                    return False
            return True
       
    def recommend(
        self,
        user_id: str,
        query: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[List[Dict], Dict]:
        """
        Main recommendation method
        
        Strategy:
        1. Check if user is new (no interactions)
        2. New user → Interest-based recommendations (high-score posts)
        3. Existing user → Hybrid personalized recommendations
        """
        start_time = datetime.now()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 RECOMMENDATION REQUEST")
        logger.info(f"   User: {user_id}")
        logger.info(f"   Query: {query or 'Feed'}")
        logger.info(f"{'='*70}")
        
        # Get user profile
        user = self.users_collection.find_one({'user_id': user_id})
        user_interests = self.get_user_interests(user_id)
        
        # Check if new user (no interactions)
        interaction_count = self.interactions_collection.count_documents({
            'user_id': user_id
        })
        
        is_new_user = interaction_count == 0
        
        if is_new_user and not user_interests:
            logger.warning(f"⚠️ User {user_id} has no profile! Creating default...")
            self.create_user_profile(user_id, ['technology', 'movies', 'sports'])
            user_interests = self.get_user_interests(user_id)
        
        logger.info(f"   New user: {is_new_user}")
        logger.info(f"   Interests: {[(i['category'], i['score']) for i in user_interests]}")
        
        # Detect query categories (if query provided)
        query_categories = []
        if query:
            detected = self.category_manager.detect_query_category(query)
            query_categories = [d['category'] for d in detected]
            logger.info(f"   Detected categories: {query_categories}")
        
        results = []
        seen_ids = set()
        
        # ==================================================
        # NEW USER PATH: Interest-based recommendations
        # ==================================================
        if is_new_user:
            logger.info("👶 NEW USER → Interest-based recommendations")
            
            # Get user's interest categories
            interest_categories = [i['category'] for i in user_interests]
            
            # If query provided, prioritize query categories
            if query_categories:
                search_categories = query_categories + interest_categories
            else:
                search_categories = interest_categories
            
            # Get high-score posts from each category
            for category in search_categories[:5]:  # Top 5 categories
                category_posts = self.category_manager.get_category_top_posts(
                    category=category,
                    limit=limit,
                    min_score=0.5
                )
                
                for post in category_posts:
                    post_id = post['id']
                    if post_id not in seen_ids:
                        results.append({
                            **post,
                            'match_score': post['relevance_score'] * 100,
                            'source': f'interest_{category}',
                            'rank': len(results) + 1
                        })
                        seen_ids.add(post_id)
                        
                        if len(results) >= limit:
                            break
                
                if len(results) >= limit:
                    break
        
        # ==================================================
        # EXISTING USER PATH: Hybrid personalized
        # ==================================================
        else:
            logger.info("👤 EXISTING USER → Hybrid personalized recommendations")
            
            # Method 1: Gorse collaborative filtering (40% weight)
            gorse_results = self._get_gorse_recommendations(user_id, limit * 2)
            
            # Method 2: Category-based (30% weight)
            category_results = []
            if query_categories:
                for category in query_categories:
                    cat_posts = self.category_manager.get_category_top_posts(
                        category=category,
                        limit=limit
                    )
                    category_results.extend(cat_posts)
            else:
                # Use user's top interests
                for interest in user_interests[:3]:
                    cat_posts = self.category_manager.get_category_top_posts(
                        category=interest['category'],
                        limit=limit // 2
                    )
                    category_results.extend(cat_posts)
            
            # Method 3: Semantic search (30% weight)
            semantic_results = []
            if query:
                semantic_results = self._semantic_search(
                    query=query,
                    limit=limit * 2
                )
            
            # Combine and score
            combined = self._merge_results(
                gorse_results,
                category_results,
                semantic_results,
                query_categories
            )
            
            # Filter and rank
            for item in combined:
                item_id = item['id']
                if item_id not in seen_ids:
                    results.append({
                        **item,
                        'rank': len(results) + 1
                    })
                    seen_ids.add(item_id)
                    
                    if len(results) >= limit:
                        break
        
        # Track this recommendation event
        self._log_recommendation(user_id, query, results, query_categories)
        
        # Metadata
        elapsed = (datetime.now() - start_time).total_seconds()
        metadata = {
            'user_id': user_id,
            'query': query,
            'is_new_user': is_new_user,
            'user_interests': {i['category']: i['score'] for i in user_interests},
            'query_categories': query_categories,
            'total_results': len(results),
            'search_time_ms': round(elapsed * 1000, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Returned {len(results)} results in {elapsed*1000:.2f}ms")
        logger.info(f"{'='*70}\n")
        
        return results, metadata
    
    # hybrid_recommender.py

    def _get_gorse_recommendations(self, user_id: str, limit: int = 10) -> List[str]:
        """Get recommendations from Gorse (with proper error handling)"""
        try:
            url = f"{self.gorse_api_url}/api/recommend/{user_id}"
            params = {"n": limit}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Gorse returned HTTP {response.status_code}")
                return []
            
            data = response.json()
            
            # ✅ Handle list format (Gorse returns direct list)
            if isinstance(data, list):
                return data
            
            # ✅ Handle dict format (just in case)
            elif isinstance(data, dict):
                items = data.get('items', data.get('Items', []))
                if isinstance(items, list):
                    return items
            
            logger.warning(f"⚠️ Unexpected Gorse response format: {type(data)}")
            return []
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Gorse unavailable: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Gorse error: {e}")
            return []
    
    def check_gorse_format():
        """Debug script to see actual Gorse response""" 
        try:
            response = requests.get("http://localhost:8087/api/recommend/user_123?n=5")
            print(f"Status: {response.status_code}")
            print(f"Response type: {type(response.json())}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
    
            
    def _semantic_search(self, query: str, limit: int) -> List[Dict]:
        """Semantic search using Qdrant"""
        try:
            query_embedding = self.embedding_model.encode(
                query,
                normalize_embeddings=True
            )
            
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit
            )
            
            items = []
            for hit in results:
                post = self.posts_collection.find_one({'_id': hit.id})
                if post:
                    items.append({
                        'id': str(post['_id']),
                        'title': post.get('title', ''),
                        'category': post.get('category', ''),
                        'body': post.get('body', '')[:200],
                        'score': float(hit.score),
                        'source': 'semantic'
                    })
            
            logger.info(f"✅ Semantic: {len(items)} items")
            return items
        
        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return []
    
    def _merge_results(
        self,
        gorse_results: List[Dict],
        category_results: List[Dict],
        semantic_results: List[Dict],
        query_categories: List[str]
    ) -> List[Dict]:
        """
        Merge and rank results from multiple sources
        
        Scoring:
        - Gorse: 40% weight
        - Category match: 30% weight
        - Semantic: 30% weight
        - Boost: +20% if matches query category
        """
        merged = {}
        
        # Add Gorse results
        for item in gorse_results:
            item_id = item['id']
            merged[item_id] = {
                **item,
                'match_score': item['score'] * 40
            }
        
        # Add category results
        for item in category_results:
            item_id = item['id']
            if item_id in merged:
                merged[item_id]['match_score'] += item.get('relevance_score', 0.5) * 30
                merged[item_id]['source'] += '+category'
            else:
                merged[item_id] = {
                    **item,
                    'match_score': item.get('relevance_score', 0.5) * 30,
                    'source': 'category'
                }
        
        # Add semantic results
        for item in semantic_results:
            item_id = item['id']
            if item_id in merged:
                merged[item_id]['match_score'] += item['score'] * 30
                merged[item_id]['source'] += '+semantic'
            else:
                merged[item_id] = {
                    **item,
                    'match_score': item['score'] * 30,
                    'source': 'semantic'
                }
        
        # Apply category boost
        if query_categories:
            for item_id, item in merged.items():
                item_category = item.get('category', '').lower()
                if item_category in [c.lower() for c in query_categories]:
                    merged[item_id]['match_score'] *= 1.2  # 20% boost
                    merged[item_id]['category_match'] = True
        
        # Sort by score
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x['match_score'],
            reverse=True
        )
        
        return sorted_results
    
    def track_interaction(
        self,
        user_id: str,
        post_id: str,
        action: str = 'view'
    ):
        """Track user interaction"""
        # Get post category
        post = self.posts_collection.find_one({'_id': post_id})
        if not post:
            return
        
        category = post.get('category', 'general')
        
        # Update user interests
        self.update_user_interests(user_id, category, action)
        
        # Log interaction
        self.interactions_collection.insert_one({
            'user_id': user_id,
            'post_id': post_id,
            'category': category,
            'action': action,
            'timestamp': datetime.now()
        })
        
        # Send to Gorse
        self._send_to_gorse_feedback(user_id, post_id, action)
        
        logger.info(f"📊 Tracked: {user_id} {action} {post_id} ({category})")
    
    def _send_to_gorse_user(self, user_id: str, labels: List[str]):
        """Send user data to Gorse"""
        try:
            url = f"{self.gorse_api_url}/api/user"
            data = {
                "UserId": user_id,
                "Labels": labels
            }
            requests.post(url, json=data, timeout=2)
        except:
            pass
    
    def _send_to_gorse_feedback(self, user_id: str, item_id: str, action: str):
        """Send feedback to Gorse"""
        try:
            url = f"{self.gorse_api_url}/api/feedback"
            feedback = {
                "FeedbackType": action,
                "UserId": user_id,
                "ItemId": item_id,
                "Timestamp": datetime.now().isoformat()
            }
            requests.post(url, json=[feedback], timeout=2)
        except:
            pass
    
    def _log_recommendation(
        self,
        user_id: str,
        query: Optional[str],
        results: List[Dict],
        categories: List[str]
    ):
        """Log recommendation event for analytics"""
        self.db['recommendation_log'].insert_one({
            'user_id': user_id,
            'query': query,
            'categories': categories,
            'results_count': len(results),
            'result_ids': [r['id'] for r in results],
            'timestamp': datetime.now()
        })
    
    def close(self):
        """Close connections"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.qdrant_client:
            self.qdrant_client.close()