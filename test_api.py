#!/usr/bin/env python3
"""
Test script for the Empathetic Code Reviewer API
"""

import requests
import json
import time

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
        return False

def test_review_endpoint():
    """Test the review endpoint"""
    url = "http://localhost:8000/review"
    
    test_data = {
        "code_snippet": """def get_active_users(users):
    results = []
    for u in users:
        if u.is_active == True and u.profile_complete == True:
            results.append(u)
    return results""",
        "review_comments": [
            "This is inefficient. Don't loop twice conceptually.",
            "Variable 'u' is a bad name.",
            "Boolean comparison '== True' is redundant."
        ]
    }
    
    try:
        print("🔄 Sending test review request...")
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Review endpoint working")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            print(f"Report length: {len(result.get('markdown_report', ''))} characters")
            
            # Save the report to a file for inspection
            with open("test_review_report.md", "w") as f:
                f.write(result.get('markdown_report', ''))
            print("📄 Report saved to test_review_report.md")
            
            return True
        else:
            print(f"❌ Review endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing review endpoint: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint"""
    url = "http://localhost:8000/analyze"
    
    test_data = {
        "code_snippet": """def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Test the function
print(calculate_fibonacci(10))""",
        "query": "How can I optimize this Fibonacci function for better performance?"
    }
    
    try:
        print("🔄 Sending test analyze request...")
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analyze endpoint working")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            print(f"Analysis length: {len(result.get('analysis', ''))} characters")
            
            # Save the analysis to a file for inspection
            with open("test_analysis_report.md", "w") as f:
                f.write(result.get('analysis', ''))
            print("📄 Analysis saved to test_analysis_report.md")
            
            return True
        else:
            print(f"❌ Analyze endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing analyze endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Empathetic Code Reviewer API")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("\n❌ Health check failed. Please make sure the server is running.")
        return
    
    print("\n" + "=" * 50)
    
    # Test review endpoint
    review_success = test_review_endpoint()
    
    print("\n" + "=" * 50)
    
    # Test analyze endpoint
    analyze_success = test_analyze_endpoint()
    
    print("\n" + "=" * 50)
    
    if review_success and analyze_success:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("❌ Some tests failed.")

if __name__ == "__main__":
    main()

