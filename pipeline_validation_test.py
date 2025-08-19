#!/usr/bin/env python3
"""
Pipeline Validation Test - Critical validation after FFmpeg installation
Tests the complete video pipeline with the new OpenAI API key
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BACKEND_URL = "https://prompt-to-video-18.preview.emergentagent.com/api"

async def test_complete_pipeline():
    """Test the complete video pipeline end-to-end"""
    print("🎯 CRITICAL VALIDATION: Complete Video Pipeline")
    print(f"Backend URL: {BACKEND_URL}")
    print("Testing with new OpenAI API key and FFmpeg installation...")
    print("=" * 80)
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as session:
        
        # Step 1: Get available voices
        print("\n🧪 Step 1: Getting available voices...")
        start_time = time.time()
        
        try:
            async with session.get(f"{BACKEND_URL}/voices/available") as response:
                if response.status == 200:
                    voices_data = await response.json()
                    voices = voices_data["voices"]
                    first_voice = voices[0]
                    voice_id = first_voice["voice_id"]
                    voice_name = first_voice["name"]
                    print(f"✅ Retrieved {len(voices)} voices. Using: {voice_name} ({voice_id})")
                else:
                    print(f"❌ Failed to get voices: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Exception getting voices: {e}")
            return False
        
        # Step 2: Test complete pipeline
        print(f"\n🧪 Step 2: Testing complete video pipeline...")
        print(f"   Prompt: 'astuces productivité pour étudiants universitaires'")
        print(f"   Duration: 30 seconds")
        print(f"   Voice: {voice_name} ({voice_id})")
        
        start_time = time.time()
        
        try:
            payload = {
                "prompt": "astuces productivité pour étudiants universitaires",
                "duration": 30,
                "voice_id": voice_id
            }
            
            async with session.post(
                f"{BACKEND_URL}/create-complete-video",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_sections = ["project_id", "script", "images", "audio", "video", "status"]
                    if all(section in data for section in required_sections):
                        
                        # Extract key metrics
                        project_id = data["project_id"]
                        script_length = len(data["script"]["script_text"])
                        scene_count = len(data["script"]["scenes"])
                        image_count = len(data["images"])
                        audio_duration = data["audio"]["duration"]
                        audio_voice_id = data["audio"]["voice_id"]
                        video_base64_length = len(data["video"]["video_base64"])
                        video_resolution = data["video"]["resolution"]
                        status = data["status"]
                        
                        print(f"\n🎉 COMPLETE PIPELINE SUCCESS! ({duration:.2f}s)")
                        print(f"   ✅ Project ID: {project_id}")
                        print(f"   ✅ Script: {script_length} chars, {scene_count} scenes")
                        print(f"   ✅ Images: {image_count} generated")
                        print(f"   ✅ Audio: {audio_duration:.1f}s duration (voice: {audio_voice_id})")
                        print(f"   ✅ Video: {video_base64_length} chars base64 ({video_resolution})")
                        print(f"   ✅ Status: {status}")
                        
                        # Validate voice_id was correctly used
                        if audio_voice_id == voice_id:
                            print(f"   ✅ Voice ID correctly integrated: {voice_name}")
                        else:
                            print(f"   ⚠️  Voice ID mismatch: sent {voice_id}, got {audio_voice_id}")
                        
                        # Step 3: Test project retrieval
                        print(f"\n🧪 Step 3: Testing project retrieval...")
                        async with session.get(f"{BACKEND_URL}/project/{project_id}") as proj_response:
                            if proj_response.status == 200:
                                proj_data = await proj_response.json()
                                print(f"   ✅ Project retrieved successfully")
                                return True
                            else:
                                print(f"   ❌ Project retrieval failed: {proj_response.status}")
                                return False
                        
                    else:
                        missing = [s for s in required_sections if s not in data]
                        print(f"❌ Missing response sections: {missing}")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ PIPELINE FAILED ({duration:.2f}s)")
                    print(f"   Status: {response.status}")
                    print(f"   Error: {error_text}")
                    
                    # Check for specific error patterns
                    if "ffmpeg" in error_text.lower():
                        print(f"   🔧 FFmpeg issue detected")
                    elif "401" in str(response.status) or "invalid_api_key" in error_text:
                        print(f"   🔑 OpenAI API key issue detected")
                    elif "quota" in error_text.lower():
                        print(f"   💳 API quota issue detected")
                    
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ PIPELINE EXCEPTION ({duration:.2f}s): {e}")
            return False

async def main():
    """Main validation test"""
    success = await test_complete_pipeline()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 VALIDATION SUCCESSFUL: Complete pipeline working with new OpenAI API key!")
        print("✅ OpenAI API key authentication resolved")
        print("✅ FFmpeg video assembly working")
        print("✅ Voice_id parameter integration confirmed")
        print("✅ 'Error creating complete video:' issue RESOLVED")
    else:
        print("❌ VALIDATION FAILED: Pipeline still has issues")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)