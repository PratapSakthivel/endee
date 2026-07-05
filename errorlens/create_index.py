#!/usr/bin/env python3
"""Create Endee index for ErrorLens"""
import requests
import json

# Try different API endpoints
endpoints = [
    ("POST", "http://localhost:8080/api/v1/index/create", {
        "name": "error_logs",
        "dimension": 384,
        "space_type": "cosine"
    }),
    ("POST", "http://localhost:8080/api/v1/index", {
        "name": "error_logs",
        "dimension": 384,
        "metric": "cosine"
    }),
    ("PUT", "http://localhost:8080/api/v1/index/error_logs", {
        "dimension": 384,
        "space_type": "cosine"
    })
]

print("Attempting to create index 'error_logs'...")
print("=" * 60)

for method, url, payload in endpoints:
    print(f"\nTrying: {method} {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        if method == "POST":
            response = requests.post(url, json=payload, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=payload, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("\n✅ SUCCESS! Index created")
            break
    except Exception as e:
        print(f"Error: {e}")

# Verify
print("\n" + "=" * 60)
print("Verifying index list...")
try:
    response = requests.get("http://localhost:8080/api/v1/index/list")
    print(f"Indexes: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
