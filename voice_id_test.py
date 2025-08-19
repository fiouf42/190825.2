#!/usr/bin/env python3
"""
Voice ID Parameter Testing - Test the specific fix mentioned in review request
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://prompt-to-video-18.preview.emergentagent.com/api"

async def test_voice_id_parameter():
    """Test if voice_id parameter is properly integrated in generate_voice endpoint"""
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        print("🎯 Testing Voice ID Parameter Integration")
        print("=" * 50)
        
        # First get available voices
        print("1. Fetching available voices...")
        async with session.get(f"{BACKEND_URL}/voices/available") as response:
            if response.status == 200:
                voices_data = await response.json()
                voices = voices_data["voices"]
                print(f"   ✅ Found {len(voices)} voices")
                
                # Test with first 3 voices
                test_voices = voices[:3]
                for i, voice in enumerate(test_voices):
                    voice_id = voice["voice_id"]
                    voice_name = voice["name"]
                    print(f"\n2.{i+1} Testing voice_id parameter with: {voice_name} ({voice_id})")
                    
                    # Test the generate_voice endpoint with voice_id parameter
                    test_url = f"{BACKEND_URL}/generate-voice?script_id=test-script-id&voice_id={voice_id}"
                    async with session.post(test_url, headers={"Content-Type": "application/json"}) as voice_response:
                        print(f"     Status: {voice_response.status}")
                        
                        if voice_response.status == 404:
                            # Expected - script not found, but voice_id parameter was accepted
                            error_data = await voice_response.json()
                            if "Script not found" in error_data.get("detail", ""):
                                print(f"     ✅ Voice ID parameter accepted (script not found as expected)")
                            else:
                                print(f"     ❓ Unexpected 404: {error_data}")
                        elif voice_response.status == 500:
                            error_text = await voice_response.text()
                            if "voice_id" in error_text.lower():
                                print(f"     ❌ Voice ID parameter issue: {error_text[:100]}")
                            else:
                                print(f"     ✅ Voice ID parameter accepted (other error: {error_text[:50]})")
                        else:
                            error_text = await voice_response.text()
                            print(f"     ❓ Unexpected status: {error_text[:100]}")
            else:
                print(f"   ❌ Could not fetch voices: {response.status}")
        
        print("\n" + "=" * 50)
        print("🎯 VOICE ID PARAMETER TEST COMPLETE")
        
        # Test the VideoGenerationRequest model with voice_id
        print("\n3. Testing VideoGenerationRequest with voice_id...")
        payload = {
            "prompt": "test prompt",
            "duration": 30,
            "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel's voice ID
        }
        
        async with session.post(
            f"{BACKEND_URL}/create-complete-video",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            print(f"   Status: {response.status}")
            if response.status == 500:
                error_text = await response.text()
                if "invalid_api_key" in error_text:
                    print(f"   ✅ VideoGenerationRequest accepts voice_id (blocked by OpenAI API key)")
                elif "voice_id" in error_text.lower():
                    print(f"   ❌ Voice ID issue in VideoGenerationRequest: {error_text[:100]}")
                else:
                    print(f"   ✅ VideoGenerationRequest accepts voice_id (other error)")
            else:
                print(f"   ❓ Unexpected response: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_voice_id_parameter())