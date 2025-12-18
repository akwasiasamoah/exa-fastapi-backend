"""
Test script for Exa FastAPI Backend
Run this after starting the server to verify all endpoints work correctly
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_result(title: str, response: requests.Response):
    """Pretty print test results"""
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print()


def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_result("Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def test_root():
    """Test root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print_result("Root Endpoint", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {str(e)}")
        return False


def test_search():
    """Test search endpoint"""
    try:
        payload = {
            "query": "FastAPI Python framework",
            "num_results": 5,
            "search_type": "auto"
        }
        response = requests.post(f"{BASE_URL}/api/v1/search", json=payload)
        print_result("Search Endpoint", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return False


def test_search_with_filters():
    """Test search with filters"""
    try:
        payload = {
            "query": "artificial intelligence news",
            "num_results": 3,
            "search_type": "neural",
            "include_domains": ["techcrunch.com", "wired.com"],
            "start_published_date": "2025-01-01"
        }
        response = requests.post(f"{BASE_URL}/api/v1/search", json=payload)
        print_result("Search with Filters", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Search with filters failed: {str(e)}")
        return False


def test_get_contents():
    """Test get contents endpoint"""
    try:
        payload = {
            "urls": ["https://fastapi.tiangolo.com/"],
            "text": True,
            "highlights": False,
            "summary": False
        }
        response = requests.post(f"{BASE_URL}/api/v1/contents", json=payload)
        print_result("Get Contents", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Get contents failed: {str(e)}")
        return False


def test_find_similar():
    """Test find similar endpoint"""
    try:
        payload = {
            "url": "https://fastapi.tiangolo.com/",
            "num_results": 5,
            "exclude_source_domain": True
        }
        response = requests.post(f"{BASE_URL}/api/v1/find-similar", json=payload)
        print_result("Find Similar", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Find similar failed: {str(e)}")
        return False


def test_batch_search():
    """Test batch search endpoint"""
    try:
        payload = {
            "queries": [
                "Python FastAPI",
                "Machine Learning",
                "Web Development"
            ],
            "num_results": 3
        }
        response = requests.post(f"{BASE_URL}/api/v1/batch-search", json=payload)
        print_result("Batch Search", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Batch search failed: {str(e)}")
        return False


def test_invalid_request():
    """Test error handling with invalid request"""
    try:
        payload = {
            "query": "",  # Empty query should fail validation
            "num_results": 5
        }
        response = requests.post(f"{BASE_URL}/api/v1/search", json=payload)
        print_result("Invalid Request (should fail)", response)
        return response.status_code == 422  # Validation error
    except Exception as e:
        print(f"❌ Invalid request test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXA FASTAPI BACKEND - TEST SUITE")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the server is running before running tests!")
    print()
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root),
        ("Basic Search", test_search),
        ("Search with Filters", test_search_with_filters),
        ("Get Contents", test_get_contents),
        ("Find Similar", test_find_similar),
        ("Batch Search", test_batch_search),
        ("Invalid Request", test_invalid_request),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {str(e)}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
