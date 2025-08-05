#!/usr/bin/env python3
"""
Quick test to verify image generation fix is working
"""

import requests
import json
import time

BACKEND_URL = "https://0280dc01-f7fd-4b8a-9b53-8b0d086b38ea.preview.emergentagent.com/api"

def test_single_image_generation():
    """Test image generation with a simple script"""
    
    # Step 1: Generate a simple script
    print("1. Generating simple script...")
    script_payload = {
        "prompt": "test simple",
        "duration": 15
    }
    
    response = requests.post(f"{BACKEND_URL}/generate-script", json=script_payload, timeout=30)
    if response.status_code != 200:
        print(f"❌ Script generation failed: {response.status_code}")
        return False
    
    script_data = response.json()
    script_id = script_data.get("id")
    scenes_count = len(script_data.get("scenes", []))
    print(f"✅ Script generated: {script_id} with {scenes_count} scenes")
    
    # Step 2: Test image generation
    print("2. Testing image generation...")
    response = requests.post(f"{BACKEND_URL}/generate-images", params={"script_id": script_id}, timeout=180)
    
    if response.status_code != 200:
        print(f"❌ Image generation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    image_data = response.json()
    images = image_data.get("images", [])
    total_generated = image_data.get("total_generated", 0)
    
    print(f"✅ Image generation response received")
    print(f"   Total generated: {total_generated}")
    print(f"   Images in response: {len(images)}")
    
    # Check if we got valid images
    valid_images = 0
    for i, img in enumerate(images):
        base64_data = img.get("image_base64", "")
        if base64_data and len(base64_data) > 100:
            valid_images += 1
            print(f"   ✅ Image {i+1}: Valid base64 data ({len(base64_data)} chars)")
        else:
            print(f"   ❌ Image {i+1}: Invalid base64 data ({len(base64_data) if base64_data else 0} chars)")
    
    if valid_images > 0:
        print(f"🎉 SUCCESS: {valid_images}/{len(images)} images have valid base64 data!")
        print("   Image generation fix is working!")
        return True
    else:
        print("❌ FAILURE: No valid images generated")
        return False

if __name__ == "__main__":
    print("Testing image generation fix...")
    success = test_single_image_generation()
    if success:
        print("\n✅ Image generation fix confirmed working!")
    else:
        print("\n❌ Image generation fix still has issues.")