#!/usr/bin/env python3
"""
Test script for GitHub Repository Summarizer API
Run this after starting the server to verify it works correctly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_valid_repo():
    """Test with a valid, small repository"""
    print_header("Testing Valid Repository (psf/requests)")
    try:
        data = {"github_url": "https://github.com/psf/requests"}
        response = requests.post(
            f"{BASE_URL}/summarize",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Summary:")
            print(f"  {result['summary']}\n")
            print(f"✅ Technologies: {', '.join(result['technologies'])}\n")
            print(f"✅ Structure:")
            print(f"  {result['structure']}\n")
            return True
        else:
            print(f"❌ Error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_url():
    """Test with an invalid GitHub URL"""
    print_header("Testing Invalid URL")
    try:
        data = {"github_url": "https://notgithub.com/user/repo"}
        response = requests.post(
            f"{BASE_URL}/summarize",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code >= 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nonexistent_repo():
    """Test with a non-existent repository"""
    print_header("Testing Non-existent Repository")
    try:
        data = {"github_url": "https://github.com/thisuserdoesnotexist12345/nonexistentrepo99999"}
        response = requests.post(
            f"{BASE_URL}/summarize",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code >= 400
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  GitHub Repository Summarizer - Test Suite")
    print("="*60)
    print("\nMake sure the server is running on http://localhost:8000")
    input("Press Enter to continue...")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Valid Repository", test_valid_repo()))
    results.append(("Invalid URL", test_invalid_url()))
    results.append(("Non-existent Repository", test_nonexistent_repo()))
    
    # Print summary
    print_header("Test Results Summary")
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
