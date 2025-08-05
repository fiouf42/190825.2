#!/usr/bin/env python3
"""
Test complete video pipeline after image generation fix
"""

import requests
import json
import time

BACKEND_URL = "https://00eb60f7-eab0-46f7-8790-e33187771154.preview.emergentagent.com/api"

def test_complete_video_pipeline():
    """Test the complete video pipeline"""
    
    print("Testing complete video pipeline...")
    print("Prompt: 'techniques de mémorisation efficaces'")
    print("Duration: 45 seconds")
    
    payload = {
        "prompt": "techniques de mémorisation efficaces",
        "duration": 45
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/create-complete-video",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code != 200:
            print(f"❌ Complete pipeline failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["project_id", "script", "images", "audio", "video", "status"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Response missing fields: {missing_fields}")
            return False
        
        # Check each component
        script = data.get("script", {})
        images = data.get("images", [])
        audio = data.get("audio", {})
        video = data.get("video", {})
        status = data.get("status", "")
        
        print(f"✅ Pipeline completed with status: {status}")
        print(f"   Project ID: {data.get('project_id')}")
        
        # Validate script
        if script and script.get("script_text"):
            print(f"   ✅ Script: {len(script.get('script_text', ''))} chars")
        else:
            print("   ❌ Script: Missing or invalid")
            return False
        
        # Validate images
        valid_images = 0
        for img in images:
            if img.get("image_base64") and len(img.get("image_base64", "")) > 100:
                valid_images += 1
        
        if valid_images > 0:
            print(f"   ✅ Images: {valid_images}/{len(images)} valid images")
        else:
            print("   ❌ Images: No valid images")
            return False
        
        # Validate audio
        if audio and audio.get("audio_id"):
            print(f"   ✅ Audio: {audio.get('duration', 0)}s duration")
        else:
            print("   ❌ Audio: Missing or invalid")
            return False
        
        # Validate video
        if video and video.get("video_base64"):
            print(f"   ✅ Video: {len(video.get('video_base64', ''))} chars")
        else:
            print("   ❌ Video: Missing or invalid")
            return False
        
        print("🎉 SUCCESS: Complete video pipeline working end-to-end!")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Pipeline timed out (this may be normal for complex videos)")
        return False
    except Exception as e:
        print(f"❌ Pipeline error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_complete_video_pipeline()
    if success:
        print("\n✅ Complete video pipeline confirmed working!")
    else:
        print("\n❌ Complete video pipeline still has issues.")