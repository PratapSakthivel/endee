#!/usr/bin/env python3
"""Fix Endee index"""
from endee import Endee
import requests

print("Initializing Endee client...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

print("\n1. Checking current indexes...")
try:
    response = requests.get("http://localhost:8080/api/v1/index/list")
    print(f"Current indexes: {response.json()}")
except Exception as e:
    print(f"Error listing indexes: {e}")

print("\n2. Attempting to create index 'error_logs'...")
try:
    result = client.create_index(
        name="error_logs",
        dimension=384,
        space_type="cosine"
    )
    print(f"✅ Index created: {result}")
except Exception as e:
    error_msg = str(e)
    print(f"Error: {error_msg}")
    
    if "already exists" in error_msg.lower():
        print("Index claims to exist, but might be in bad state")
        print("\n3. Attempting to delete existing index...")
        try:
            client.delete_index("error_logs")
            print("✅ Deleted existing index")
            
            print("\n4. Creating index again...")
            result = client.create_index(
                name="error_logs",
                dimension=384,
                space_type="cosine"
            )
            print(f"✅ Index recreated: {result}")
        except Exception as e2:
            print(f"Failed to delete/recreate: {e2}")

print("\n5. Final verification...")
try:
    response = requests.get("http://localhost:8080/api/v1/index/list")
    indexes = response.json().get("indexes", [])
    print(f"Final indexes: {indexes}")
    
    if "error_logs" in indexes or any("error_logs" in str(idx) for idx in indexes):
        print("✅ SUCCESS - error_logs index is ready!")
    else:
        print("❌ Index still not visible")
except Exception as e:
    print(f"Error: {e}")
