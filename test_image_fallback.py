#!/usr/bin/env python3
"""
Test script to check if DALL-E 3 works as fallback for image generation
"""

import requests
import json

BACKEND_URL = "https://949daeb1-ac6a-43ae-930f-dc59ba72c7b2.preview.emergentagent.com/api"

def test_dalle3_fallback():
    """Test if we can modify the backend to use DALL-E 3 instead"""
    
    # First, let's generate a script
    script_payload = {
        "prompt": "test simple",
        "duration": 15
    }
    
    print("Testing script generation...")
    response = requests.post(f"{BACKEND_URL}/generate-script", json=script_payload, timeout=30)
    
    if response.status_code == 200:
        script_data = response.json()
        script_id = script_data.get("id")
        print(f"✅ Script generated with ID: {script_id}")
        
        # Now test image generation (this will fail with gpt-image-1)
        print("Testing image generation with current setup...")
        img_response = requests.post(f"{BACKEND_URL}/generate-images", params={"script_id": script_id}, timeout=60)
        
        if img_response.status_code == 200:
            img_data = img_response.json()
            print(f"✅ Images generated: {img_data.get('total_generated', 0)}")
        else:
            print(f"❌ Image generation failed: {img_response.status_code}")
            print(f"Response: {img_response.text}")
    else:
        print(f"❌ Script generation failed: {response.status_code}")

if __name__ == "__main__":
    test_dalle3_fallback()