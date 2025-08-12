#!/usr/bin/env python3
"""
Simple test script for the TikTok Video Generator API
Tests the complete pipeline with real APIs
"""

import asyncio
import httpx
import json
import sys

# API Base URL
API_BASE = "http://localhost:8001/api"

async def test_api_health():
    """Test if API is running"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/")
            if response.status_code == 200:
                print("✅ API Health Check: PASSED")
                return True
            else:
                print(f"❌ API Health Check: FAILED - Status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ API Health Check: FAILED - {str(e)}")
        return False

async def test_voices_endpoint():
    """Test ElevenLabs voices endpoint"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{API_BASE}/voices/available")
            if response.status_code == 200:
                data = response.json()
                voices = data.get("voices", [])
                print(f"✅ Voices Endpoint: PASSED - {len(voices)} voices available")
                if voices:
                    print(f"   Sample voices: {[v['name'] for v in voices[:3]]}")
                return True
            else:
                print(f"❌ Voices Endpoint: FAILED - Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Voices Endpoint: FAILED - {str(e)}")
        return False

async def test_script_generation():
    """Test OpenAI script generation"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "prompt": "astuces productivité étudiants",
                "duration": 30
            }
            response = await client.post(f"{API_BASE}/generate-script", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                script_text = data.get("script_text", "")
                scenes = data.get("scenes", [])
                print(f"✅ Script Generation: PASSED")
                print(f"   Script length: {len(script_text)} chars")
                print(f"   Scenes: {len(scenes)}")
                return data["id"]
            else:
                print(f"❌ Script Generation: FAILED - Status {response.status_code}")
                print(f"   Response: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Script Generation: FAILED - {str(e)}")
        return None

async def test_image_generation(script_id):
    """Test OpenAI image generation"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{API_BASE}/generate-images?script_id={script_id}")
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])
                print(f"✅ Image Generation: PASSED - {len(images)} images generated")
                for i, img in enumerate(images):
                    base64_len = len(img.get("image_base64", ""))
                    print(f"   Image {i+1}: {base64_len} chars base64")
                return True
            else:
                print(f"❌ Image Generation: FAILED - Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Image Generation: FAILED - {str(e)}")
        return False

async def test_complete_pipeline():
    """Test the complete video generation pipeline"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes timeout
            payload = {
                "prompt": "conseils pour améliorer sa productivité au travail",
                "duration": 30
            }
            response = await client.post(f"{API_BASE}/create-complete-video", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                video_base64 = data.get("video", {}).get("video_base64", "")
                print(f"✅ Complete Pipeline: PASSED")
                print(f"   Video size: {len(video_base64)} chars base64")
                print(f"   Project ID: {data.get('project_id')}")
                print(f"   Script length: {len(data.get('script', {}).get('script_text', ''))}")
                print(f"   Images: {len(data.get('images', []))}")
                print(f"   Audio duration: {data.get('audio', {}).get('duration')}s")
                return True
            else:
                print(f"❌ Complete Pipeline: FAILED - Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Complete Pipeline: FAILED - {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting TikTok Video Generator API Tests")
    print("=" * 50)
    
    # Test 1: API Health
    if not await test_api_health():
        print("❌ API is not running. Exiting tests.")
        sys.exit(1)
    
    print()
    
    # Test 2: Voices endpoint
    await test_voices_endpoint()
    print()
    
    # Test 3: Script generation
    script_id = await test_script_generation()
    print()
    
    # Test 4: Image generation (if script generation succeeded)
    if script_id:
        await test_image_generation(script_id)
        print()
    
    # Test 5: Complete pipeline
    print("🎬 Testing Complete Video Pipeline...")
    await test_complete_pipeline()
    
    print()
    print("=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())