# test_api.py - API Testing Script

import requests
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:5000'


def print_header(text):
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")


def print_results(results):
    """Pretty print recommendation results"""
    print(f"\n{'#':<4} {'Title':<45} {'Category':<12} {'Match %':<10}")
    print("-" * 80)
    
    for i, r in enumerate(results, 1):
        match_score = r.get('match_score', 0)
        print(f"{i:<4} {r['title'][:42]:<45} {r['category']:<12} {match_score:<10.1f}%")


def test_health():
    """Test health endpoint"""
    print_header("🏥 Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_categories():
    """Test categories endpoint"""
    print_header("📁 Testing Get Categories")
    
    response = requests.get(f"{BASE_URL}/api/categories")
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Total categories: {len(data.get('categories', []))}")
    
    for cat in data.get('categories', []):
        print(f"  - {cat['name']}: {cat.get('post_count', 0)} posts")
    
    return response.status_code == 200


def test_user_onboarding():
    """Test user onboarding"""
    print_header("👤 Testing User Onboarding")
    
    user_data = {
        "user_id": "test_user_movies",
        "interests": ["movies", "sports", "technology"]
    }
    
    print(f"Creating user: {user_data['user_id']}")
    print(f"Interests: {user_data['interests']}")
    
    response = requests.post(
        f"{BASE_URL}/api/user/onboard",
        json=user_data
    )
    
    data = response.json()
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ User created successfully!")
        print(f"Initial recommendations: {len(data.get('initial_recommendations', []))}")
        
        print_results(data.get('initial_recommendations', [])[:5])
        
        return True
    else:
        print(f"❌ Error: {data.get('error')}")
        return False


def test_recommendations(user_id, query=None):
    """Test recommendations endpoint"""
    print_header(f"🎯 Testing Recommendations")
    
    params = {
        'user_id': user_id,
        'limit': 10
    }
    
    if query:
        params['query'] = query
        print(f"Query: '{query}'")
    else:
        print("Query: None (Feed)")
    
    print(f"User: {user_id}")
    
    response = requests.get(
        f"{BASE_URL}/api/recommend",
        params=params
    )
    
    data = response.json()
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        recommendations = data.get('recommendations', [])
        metadata = data.get('metadata', {})
        
        print(f"Total results: {len(recommendations)}")
        print(f"Is new user: {metadata.get('is_new_user')}")
        print(f"Detected categories: {metadata.get('query_categories', [])}")
        print(f"Search time: {metadata.get('search_time_ms')}ms")
        
        print_results(recommendations)
        
        # Check relevance
        if query:
            query_cats = metadata.get('query_categories', [])
            if query_cats:
                relevant_count = sum(
                    1 for r in recommendations[:5]
                    if r['category'].lower() in [c.lower() for c in query_cats]
                )
                print(f"\n📊 Relevance: {relevant_count}/5 results match category '{query_cats[0]}'")
                
                if relevant_count >= 3:
                    print("✅ PASS: Good relevance!")
                    return True
                else:
                    print("⚠️ FAIL: Low relevance!")
                    return False
        
        return True
    else:
        print(f"❌ Error: {data.get('error')}")
        return False


def test_interaction_tracking(user_id, post_id):
    """Test interaction tracking"""
    print_header("📊 Testing Interaction Tracking")
    
    interaction_data = {
        "user_id": user_id,
        "post_id": post_id,
        "action": "like"
    }
    
    print(f"User: {user_id}")
    print(f"Post: {post_id}")
    print(f"Action: like")
    
    response = requests.post(
        f"{BASE_URL}/api/track",
        json=interaction_data
    )
    
    data = response.json()
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {data.get('message', data.get('error'))}")
    
    return response.status_code == 200


def test_user_interests(user_id):
    """Test get user interests"""
    print_header("📈 Testing Get User Interests")
    
    response = requests.get(f"{BASE_URL}/api/user/{user_id}/interests")
    data = response.json()
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        interests = data.get('interests', [])
        print(f"Total interests: {len(interests)}\n")
        
        for interest in interests:
            print(f"  - {interest['category']}: {interest['score']:.2f} (interactions: {interest['interaction_count']})")
        
        return True
    else:
        print(f"❌ Error: {data.get('error')}")
        return False


def test_search(query, user_id=None):
    """Test search endpoint"""
    print_header(f"🔍 Testing Search")
    
    params = {
        'q': query,
        'limit': 10
    }
    
    if user_id:
        params['user_id'] = user_id
    
    print(f"Query: '{query}'")
    print(f"User: {user_id or 'Anonymous'}")
    
    response = requests.get(
        f"{BASE_URL}/api/search",
        params=params
    )
    
    data = response.json()
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        detected = data.get('detected_categories', [])
        results = data.get('results', [])
        
        print(f"Detected categories: {[d['category'] for d in detected]}")
        print(f"Total results: {len(results)}")
        
        print_results(results[:5])
        
        return True
    else:
        print(f"❌ Error: {data.get('error')}")
        return False


def run_complete_test_suite():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("🧪 STARTING COMPLETE API TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Health check
    results['health'] = test_health()
    time.sleep(1)
    
    # Test 2: Get categories
    results['categories'] = test_categories()
    time.sleep(1)
    
    # Test 3: User onboarding
    results['onboarding'] = test_user_onboarding()
    time.sleep(1)
    
    # Test 4: Get user interests
    results['interests'] = test_user_interests('test_user_movies')
    time.sleep(1)
    
    # Test 5: Recommendations (Feed)
    results['feed'] = test_recommendations('test_user_movies')
    time.sleep(1)
    
    # Test 6: Recommendations with query (Movies - should be relevant)
    results['query_movies'] = test_recommendations(
        'test_user_movies',
        'best action movies to watch'
    )
    time.sleep(1)
    
    # Test 7: Recommendations with query (Technology)
    results['query_tech'] = test_recommendations(
        'test_user_movies',
        'best smartphones under 20000'
    )
    time.sleep(1)
    
    # Test 8: Track interaction
    results['tracking'] = test_interaction_tracking(
        'test_user_movies',
        'post_001'
    )
    time.sleep(1)
    
    # Test 9: Check updated interests
    results['interests_after'] = test_user_interests('test_user_movies')
    time.sleep(1)
    
    # Test 10: Search (Anonymous)
    results['search'] = test_search('cricket world cup')
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - Check logs above")


if __name__ == '__main__':
    print("\n🚀 Starting API Tests...")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Server is running!\n")
        
        # Run test suite
        run_complete_test_suite()
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server!")
        print(f"Make sure Flask is running on {BASE_URL}")
        print("\nStart server with: python app.py\n")
    except Exception as e:
        print(f"❌ ERROR: {e}\n")