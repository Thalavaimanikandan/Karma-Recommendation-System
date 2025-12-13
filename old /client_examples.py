import requests
import json
from typing import Dict, Any


class RecommendationClient:
    """Client for interacting with the Recommendation API"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    # -------------------- CORE ENDPOINTS (LIVE) --------------------

    def health(self) -> Dict:
        return self._make_request("GET", "/api/health")

    def extract_keywords(self, text: str) -> Dict:
        return self._make_request(
            "POST",
            "/api/extract-keywords",
            json={"text": text}
        )

    def detect_category(self, text: str) -> Dict:
        return self._make_request(
            "POST",
            "/api/detect-category",
            json={"text": text}
        )

    def search(self, query: str, top_k: int = 10) -> Dict:
        return self._make_request(
        "POST",
        "/api/search",
        json={"text": query, "top_k": top_k}
    )

    def smart_search(self, query: str, top_k: int = 10) -> Dict:
      return self._make_request(
        "POST",
        "/api/smart-search",
        json={"text": query, "top_k": top_k}
    )


    def get_categories(self) -> Dict:
        return self._make_request("GET", "/api/categories")

    def get_stats(self) -> Dict:
        return self._make_request("GET", "/api/stats")

    def refresh_index(self) -> Dict:
        return self._make_request("POST", "/api/refresh")


# -------------------- PRINT UTILITY --------------------

def print_result(title: str, result: Dict):
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


# -------------------- EXAMPLE USAGE --------------------

def main():
    client = RecommendationClient("http://localhost:5000")

    # 1. Health
    print_result("Health Check", client.health())

    print("\n" + "="*60)
    print("NLP FEATURES")
    print("="*60)

    print_result("Extract Keywords: ajith", client.extract_keywords("ajith"))
    print_result("Extract Keywords: thunivu", client.extract_keywords("thunivu"))
    print_result("Extract Keywords: hangman", client.extract_keywords("hangman"))

    # 2. Category Detection
    print_result("Detect Category: action movies",
                 client.detect_category("action movies"))

    # 3. Search
    print("\n" + "="*60)
    print("SEARCH")
    print("="*60)

    print_result("Search Results", client.search("action movies"))
    print_result("Smart Search Results",
                 client.smart_search("technology innovation"))

    # 4. Categories & Stats
    print("\n" + "="*60)
    print("SYSTEM INFO")
    print("="*60)

    print_result("Available Categories", client.get_categories())
    print_result("Database Stats", client.get_stats())

    # 5. Refresh
    print("\n" + "="*60)
    print("REFRESH INDEX")
    print("="*60)

    print_result("Refresh Response", client.refresh_index())


if __name__ == "__main__":
    main()
