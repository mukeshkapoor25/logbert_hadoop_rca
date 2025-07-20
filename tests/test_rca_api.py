#!/usr/bin/env python3
import requests
import json

# Read the test log file
with open('/Users/mukeshkapoor/projects/logbert_hadoop_rca/test_logs/clean_test.log', 'r') as f:
    log_content = f.read()

# Create the request payload
payload = {
    "log_text": log_content,
    "threshold": 0.5,
    "model_name": "logbert_hadoop",
    "context_window": 10,
    "include_rca": True
}

# Make the API request
try:
    response = requests.post(
        "http://localhost:8000/api/analyze",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
    try:
        print(f"Response text: {response.text}")
    except:
        print("Could not get response text")
