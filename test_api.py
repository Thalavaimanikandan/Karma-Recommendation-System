import requests
import json

BASE_URL = "http://localhost:5000"

def test_category():
    print("\n=== Testing Category Extraction ===")
    
    # Test 1: ajith
    response = requests.post(
        f"{BASE_URL}/api/category/extract-tags",
        json={"text": "ajith"}
    )
    print(f"ajith: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: thunivu
    response = requests.post(
        f"{BASE_URL}/api/category/extract-tags",
        json={"text": "thunivu"}
    )
    print(f"\nthunivu: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: hangman
    response = requests.post(
        f"{BASE_URL}/api/category/extract-tags",
        json={"text": "hangman"}
    )
    print(f"\nhangman: {json.dumps(response.json(), indent=2)}")

def test_gorse():
    print("\n=== Testing Gorse Recommendations ===")
    
    # Add user
    requests.post(f"{BASE_URL}/api/gorse/user", json={
        "user_id": "user_123",
        "labels": ["action"]
    })
    print("✅ User added")
    
    # Add items
    requests.post(f"{BASE_URL}/api/gorse/item", json={
        "item_id": "movie_1",
        "labels": ["action", "thriller"]
    })
    print("✅ Item added")
    
    # Add feedback
    requests.post(f"{BASE_URL}/api/gorse/feedback", json={
        "user_id": "user_123",
        "item_id": "movie_1",
        "feedback_type": "like"
    })
    print("✅ Feedback added")
    
    # Get recommendations
    response = requests.get(f"{BASE_URL}/api/gorse/recommend/user_123?n=5")
    print(f"Recommendations: {json.dumps(response.json(), indent=2)}")

def test_moderation():
    print("\n=== Testing Content Moderation ===")
    
    response = requests.post(
        f"{BASE_URL}/api/moderate/content",
        json={"text": "this is Thalavai Manikandan from ChainScript"}
    )
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_category()
    test_gorse()
    test_moderation()