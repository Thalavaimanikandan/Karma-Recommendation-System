# services/gorse_service.py - FIXED VERSION

import logging
import requests
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class GorseService:
    """Gorse recommendation engine client - FIXED"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-API-Key': api_key} if api_key else {}
        logger.info(f"✅ Gorse service initialized: {api_url}")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test if Gorse is available"""
        try:
            response = requests.get(
                f"{self.api_url}/api/health",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ Gorse connection successful")
            else:
                logger.warning(f"⚠️ Gorse health check returned {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Gorse not available: {e}")
    
    def insert_user(self, user_id: str, labels: List[str] = None) -> bool:
        """Insert or update a user"""
        try:
            url = f"{self.api_url}/api/user"
            
            # FIX: Ensure user_id is string and clean
            clean_user_id = str(user_id).strip()
            
            data = {
                "UserId": clean_user_id,
                "Labels": labels or []
            }
            
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Gorse user inserted: {clean_user_id}")
                return True
            else:
                logger.warning(f"⚠️ Gorse insert user failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gorse insert user error: {e}")
            return False
    
    def insert_item(
        self,
        item_id: str,
        categories: List[str],
        labels: List[str] = None,
        timestamp: Optional[str] = None
    ) -> bool:
        """Insert or update an item - FIXED"""
        try:
            url = f"{self.api_url}/api/item"
            
            # FIX: Clean item_id - remove special characters
            clean_item_id = str(item_id).strip()
            # Remove any characters that might cause Redis issues
            clean_item_id = clean_item_id.replace(' ', '_')
            
            # FIX: Ensure categories and labels are clean strings
            clean_categories = [str(cat).strip() for cat in (categories or [])]
            clean_labels = [str(label).strip() for label in (labels or [])]
            
            data = {
                "ItemId": clean_item_id,
                "Categories": clean_categories,
                "Labels": clean_labels,
                "IsHidden": False,
                "Comment": "",
                "Timestamp": timestamp or ""
            }
            
            logger.debug(f"Sending to Gorse: {data}")
            
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Gorse item inserted: {clean_item_id}")
                return True
            else:
                logger.warning(
                    f"⚠️ Gorse insert item failed: {response.status_code}\n"
                    f"   Response: {response.text}\n"
                    f"   Data sent: {data}"
                )
                return False
                
        except Exception as e:
            logger.error(f"❌ Gorse insert item error: {e}")
            return False
    
    def insert_feedback(
        self,
        user_id: str,
        item_id: str,
        feedback_type: str = "click"
    ) -> bool:
        """Insert user feedback - FIXED"""
        try:
            url = f"{self.api_url}/api/feedback"
            
            # FIX: Clean IDs
            clean_user_id = str(user_id).strip()
            clean_item_id = str(item_id).strip().replace(' ', '_')
            
            data = [{
                "FeedbackType": feedback_type,
                "UserId": clean_user_id,
                "ItemId": clean_item_id
            }]
            
            response = requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Gorse feedback: {clean_user_id} → {clean_item_id} ({feedback_type})")
                return True
            else:
                logger.warning(f"⚠️ Gorse insert feedback failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gorse insert feedback error: {e}")
            return False
    
    def get_recommendations(self, user_id: str, n: int = 10) -> List[Dict]:
        """Get recommendations for a user"""
        try:
            # FIX: Clean user_id
            clean_user_id = str(user_id).strip()
            
            url = f"{self.api_url}/api/recommend/{clean_user_id}"
            params = {"n": n}
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                items = response.json()
                logger.info(f"✅ Gorse recommendations for {clean_user_id}: {len(items)} items")
                return items
            else:
                logger.warning(f"⚠️ Gorse recommendations failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Gorse get recommendations error: {e}")
            return []
    
    def get_popular(self, category: Optional[str] = None, n: int = 10) -> List[Dict]:
        """Get popular items"""
        try:
            url = f"{self.api_url}/api/popular"
            params = {"n": n}
            
            if category:
                # FIX: Clean category
                clean_category = str(category).strip()
                params['category'] = clean_category
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                items = response.json()
                logger.info(f"✅ Gorse popular items: {len(items)} items")
                return items
            else:
                logger.warning(f"⚠️ Gorse popular items failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Gorse get popular error: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Gorse is available"""
        try:
            response = requests.get(
                f"{self.api_url}/api/health",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False