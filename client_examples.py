import requests
import json
from typing import Dict, Any


class RecommendationClient:
    """Client for interacting with the Recommendation API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip("/")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, **kwargs)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict:
        """Check API health status"""
        return self._make_request("GET", "/health")
    
    def extract_tags(self, text: str) -> Dict:
        """
        Extract tags from text
        
        Args:
            text: Input text for tag extraction
        """
        return self._make_request(
            "POST",
            "/api/category/extract-tags",
            json={"text": text}
        )
    
    def get_category_recommendations(self, text: str, top_k: int = 10) -> Dict:
        """
        Get category-based recommendations
        
        Args:
            text: User interest or query
            top_k: Number of recommendations
        """
        return self._make_request(
            "POST",
            "/api/category/recommend",
            json={"text": text, "top_k": top_k}
        )
    
    def get_gorse_recommendations(self, user_id: str, n: int = 10, 
                                 categories: str = None) -> Dict:
        """
        Get Gorse-based recommendations
        
        Args:
            user_id: User identifier
            n: Number of recommendations
            categories: Comma-separated categories
        """
        params = {"n": n}
        if categories:
            params["categories"] = categories
        
        return self._make_request(
            "GET",
            f"/api/gorse/recommend/{user_id}",
            params=params
        )
    
    def add_user(self, user_id: str, labels: list = None, comment: str = "") -> Dict:
        """
        Add or update a user
        
        Args:
            user_id: Unique user identifier
            labels: User labels/tags
            comment: Additional information
        """
        return self._make_request(
            "POST",
            "/api/gorse/user",
            json={
                "user_id": user_id,
                "labels": labels or [],
                "comment": comment
            }
        )
    
    def add_item(self, item_id: str, labels: list = None, 
                categories: list = None, comment: str = "", 
                is_hidden: bool = False) -> Dict:
        """
        Add or update an item
        
        Args:
            item_id: Unique item identifier
            labels: Item labels/tags
            categories: Item categories
            comment: Item description
            is_hidden: Whether item is hidden
        """
        return self._make_request(
            "POST",
            "/api/gorse/item",
            json={
                "item_id": item_id,
                "labels": labels or [],
                "categories": categories or [],
                "comment": comment,
                "is_hidden": is_hidden
            }
        )
    
    def add_feedback(self, user_id: str, item_id: str, 
                    feedback_type: str = "read", timestamp: str = None) -> Dict:
        """
        Submit user feedback
        
        Args:
            user_id: User identifier
            item_id: Item identifier
            feedback_type: Type of feedback (read, like, dislike)
            timestamp: Optional timestamp
        """
        payload = {
            "user_id": user_id,
            "item_id": item_id,
            "feedback_type": feedback_type
        }
        
        if timestamp:
            payload["timestamp"] = timestamp
        
        return self._make_request("POST", "/api/gorse/feedback", json=payload)
    
    def get_popular_items(self, n: int = 10, offset: int = 0) -> Dict:
        """Get popular items"""
        return self._make_request(
            "GET",
            "/api/gorse/popular",
            params={"n": n, "offset": offset}
        )
    
    def get_latest_items(self, n: int = 10, offset: int = 0) -> Dict:
        """Get latest items"""
        return self._make_request(
            "GET",
            "/api/gorse/latest",
            params={"n": n, "offset": offset}
        )
    
    def get_similar_items(self, item_id: str, n: int = 10, offset: int = 0) -> Dict:
        """Get similar items"""
        return self._make_request(
            "GET",
            f"/api/gorse/similar/{item_id}",
            params={"n": n, "offset": offset}
        )
    
    def moderate_content(self, text: str = None, image: str = None) -> Dict:
        """
        Moderate content for safety
        
        Args:
            text: Text to analyze
            image: Base64 encoded image
        """
        payload = {}
        if text:
            payload["text"] = text
        if image:
            payload["image"] = image
        
        return self._make_request("POST", "/api/moderate/content", json=payload)
    
    def get_hybrid_recommendations(self, user_id: str, query: str = "", 
                                  n: int = 10, weight_category: float = 0.5,
                                  weight_gorse: float = 0.5) -> Dict:
        """
        Get hybrid recommendations
        
        Args:
            user_id: User identifier
            query: Search query for category-based
            n: Number of recommendations
            weight_category: Weight for category-based
            weight_gorse: Weight for Gorse-based
        """
        return self._make_request(
            "POST",
            "/api/hybrid/recommend",
            json={
                "user_id": user_id,
                "query": query,
                "n": n,
                "weight_category": weight_category,
                "weight_gorse": weight_gorse
            }
        )


def print_result(title: str, result: Dict):
    """Pretty print results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    """Example usage of the recommendation client"""
    
    # Initialize client
    client = RecommendationClient("http://localhost:5000")
    
    # 1. Health check
    print_result("Health Check", client.health_check())
    
    # 2. Category-based recommendation - Extract tags
    print("\n" + "="*60)
    print("CATEGORY-BASED RECOMMENDATIONS")
    print("="*60)
    
    # Example 1: Actor name
    print_result(
        "Extract Tags: ajith",
        client.extract_tags("ajith")
    )
    
    # Example 2: Movie name
    print_result(
        "Extract Tags: thunivu",
        client.extract_tags("thunivu")
    )
    
    # Example 3: Game name
    print_result(
        "Extract Tags: hangman",
        client.extract_tags("hangman")
    )
    
    # Get category recommendations
    print_result(
        "Category Recommendations for 'action movies'",
        client.get_category_recommendations("action movies", top_k=5)
    )
    
    # 3. Gorse-based recommendations
    print("\n" + "="*60)
    print("GORSE-BASED RECOMMENDATIONS")
    print("="*60)
    
    # Add a user
    print_result(
        "Add User",
        client.add_user(
            user_id="user_123",
            labels=["action", "thriller"],
            comment="Action movie enthusiast"
        )
    )
    
    # Add items
    print_result(
        "Add Item: Thunivu",
        client.add_item(
            item_id="movie_thunivu",
            labels=["action", "ajith", "thriller"],
            categories=["movies", "tamil"],
            comment="Ajith Kumar starrer action thriller"
        )
    )
    
    print_result(
        "Add Item: Valimai",
        client.add_item(
            item_id="movie_valimai",
            labels=["action", "ajith", "police"],
            categories=["movies", "tamil"],
            comment="Ajith Kumar police action movie"
        )
    )
    
    # Add feedback (user interactions)
    print_result(
        "Add Feedback: User likes Thunivu",
        client.add_feedback("user_123", "movie_thunivu", "like")
    )
    
    print_result(
        "Add Feedback: User watched Valimai",
        client.add_feedback("user_123", "movie_valimai", "read")
    )
    
    # Get recommendations
    print_result(
        "Get Recommendations for user_123",
        client.get_gorse_recommendations("user_123", n=5)
    )
    
    # Get popular items
    print_result(
        "Get Popular Items",
        client.get_popular_items(n=5)
    )
    
    # Get similar items
    print_result(
        "Get Similar to Thunivu",
        client.get_similar_items("movie_thunivu", n=5)
    )
    
    # 4. Content moderation
    print("\n" + "="*60)
    print("CONTENT MODERATION")
    print("="*60)
    
    print_result(
        "Moderate Safe Content",
        client.moderate_content(text="this is Thalavai Manikandan from ChainScript")
    )
    
    # 5. Hybrid recommendations
    print("\n" + "="*60)
    print("HYBRID RECOMMENDATIONS")
    print("="*60)
    
    print_result(
        "Hybrid Recommendations",
        client.get_hybrid_recommendations(
            user_id="user_123",
            query="action thriller",
            n=5,
            weight_category=0.6,
            weight_gorse=0.4
        )
    )


if __name__ == "__main__":
    main()