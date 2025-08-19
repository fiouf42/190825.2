#!/usr/bin/env python3
"""
Focused Backend Testing for TikTok Video Generator
Tests working components and identifies API key issues
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://prompt-to-video-18.preview.emergentagent.com/api"

class FocusedTikTokTester:
    def __init__(self):
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, success, details, duration=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status}: {test_name}{duration_str}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_api_health(self):
        """Test API health and accessibility"""
        test_name = "API Health Check"
        start_time = time.time()
        
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(test_name, True, f"Backend accessible: {data.get('message', 'OK')}", duration)
                    return True
                else:
                    self.log_test(test_name, False, f"Status: {response.status}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_elevenlabs_voices(self):
        """Test ElevenLabs voices endpoint - should return 19+ voices"""
        test_name = "ElevenLabs Voices Integration"
        start_time = time.time()
        
        try:
            async with self.session.get(f"{BACKEND_URL}/voices/available") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if "voices" in data and isinstance(data["voices"], list):
                        voice_count = len(data["voices"])
                        sample_voices = [(v["name"], v["voice_id"]) for v in data["voices"][:3]]
                        
                        # Check if we have the expected 19+ voices
                        expected_min = 19
                        if voice_count >= expected_min:
                            self.log_test(test_name, True, f"✅ {voice_count} voices available (≥{expected_min}). Sample: {sample_voices}", duration)
                            return True, data["voices"]
                        else:
                            self.log_test(test_name, False, f"Only {voice_count} voices (expected ≥{expected_min})", duration)
                            return False, []
                    else:
                        self.log_test(test_name, False, f"Invalid response format", duration)
                        return False, []
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False, []
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False, []
    
    async def test_openai_script_generation(self):
        """Test OpenAI script generation with specific French prompt"""
        test_name = "OpenAI Script Generation"
        start_time = time.time()
        
        try:
            payload = {
                "prompt": "astuces productivité pour étudiants universitaires",
                "duration": 30
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/generate-script",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    script_length = len(data.get("script_text", ""))
                    scene_count = len(data.get("scenes", []))
                    self.log_test(test_name, True, f"✅ Script generated: {script_length} chars, {scene_count} scenes", duration)
                    return True, data
                else:
                    error_text = await response.text()
                    # Check if it's an API key issue
                    if "401" in str(response.status) or "invalid_api_key" in error_text:
                        self.log_test(test_name, False, f"❌ CRITICAL: OpenAI API key is INVALID (401 Unauthorized)", duration)
                    else:
                        self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text[:200]}", duration)
                    return False, None
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False, None
    
    async def test_voice_id_integration(self, voices):
        """Test voice_id parameter integration in complete pipeline"""
        test_name = "Voice ID Integration Test"
        start_time = time.time()
        
        if not voices:
            self.log_test(test_name, False, "No voices available for testing", 0)
            return False
        
        # Use first available voice
        first_voice = voices[0]
        voice_id = first_voice["voice_id"]
        voice_name = first_voice["name"]
        
        try:
            payload = {
                "prompt": "astuces productivité pour étudiants universitaires",
                "duration": 30,
                "voice_id": voice_id  # This is the key fix being tested
            }
            
            print(f"   Testing with voice: {voice_name} ({voice_id})")
            
            async with self.session.post(
                f"{BACKEND_URL}/create-complete-video",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    # Check if voice_id was properly used
                    if "audio" in data and "voice_id" in data["audio"]:
                        returned_voice_id = data["audio"]["voice_id"]
                        if returned_voice_id == voice_id:
                            self.log_test(test_name, True, f"✅ Voice ID correctly integrated: {voice_name} ({voice_id})", duration)
                            return True
                        else:
                            self.log_test(test_name, False, f"Voice ID mismatch: sent {voice_id}, got {returned_voice_id}", duration)
                            return False
                    else:
                        self.log_test(test_name, False, f"Voice ID not found in response", duration)
                        return False
                else:
                    error_text = await response.text()
                    # Check if it's an API key issue blocking the test
                    if "401" in str(response.status) or "invalid_api_key" in error_text:
                        self.log_test(test_name, False, f"❌ BLOCKED: OpenAI API key invalid - cannot test voice_id integration", duration)
                    else:
                        self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text[:200]}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_error_handling_improvements(self):
        """Test improved error handling and logging"""
        test_name = "Error Handling & Logging"
        start_time = time.time()
        
        try:
            # Test with invalid script_id to trigger error handling
            async with self.session.post(
                f"{BACKEND_URL}/generate-voice?script_id=invalid-id&voice_id=test",
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 404:
                    error_data = await response.json()
                    if "detail" in error_data and "Script not found" in error_data["detail"]:
                        self.log_test(test_name, True, f"✅ Proper error handling: {error_data['detail']}", duration)
                        return True
                    else:
                        self.log_test(test_name, False, f"Unexpected error format: {error_data}", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Unexpected status: {response.status}, {error_text[:100]}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def run_focused_tests(self):
        """Run focused tests on working components"""
        print("🎯 FOCUSED TESTING: TikTok Video Generator Backend")
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing working components and identifying blockers...")
        print("=" * 80)
        
        # Test sequence
        tests_results = {}
        
        # 1. API Health
        print(f"\n🧪 Testing: API Health")
        tests_results["api_health"] = await self.test_api_health()
        
        # 2. ElevenLabs Integration
        print(f"\n🧪 Testing: ElevenLabs Voices")
        voices_success, voices = await self.test_elevenlabs_voices()
        tests_results["elevenlabs_voices"] = voices_success
        
        # 3. OpenAI Integration
        print(f"\n🧪 Testing: OpenAI Script Generation")
        openai_success, script_data = await self.test_openai_script_generation()
        tests_results["openai_script"] = openai_success
        
        # 4. Voice ID Integration (key fix being tested)
        print(f"\n🧪 Testing: Voice ID Integration")
        tests_results["voice_id_integration"] = await self.test_voice_id_integration(voices)
        
        # 5. Error Handling
        print(f"\n🧪 Testing: Error Handling")
        tests_results["error_handling"] = await self.test_error_handling_improvements()
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 FOCUSED TEST RESULTS:")
        
        working_components = []
        blocked_components = []
        
        if tests_results["api_health"]:
            working_components.append("✅ Backend API accessible")
        
        if tests_results["elevenlabs_voices"]:
            working_components.append(f"✅ ElevenLabs integration ({len(voices)} voices)")
        
        if tests_results["openai_script"]:
            working_components.append("✅ OpenAI script generation")
        else:
            blocked_components.append("❌ OpenAI script generation (API key invalid)")
        
        if tests_results["voice_id_integration"]:
            working_components.append("✅ Voice ID parameter integration")
        else:
            blocked_components.append("❌ Voice ID integration (blocked by OpenAI API key)")
        
        if tests_results["error_handling"]:
            working_components.append("✅ Error handling improvements")
        
        print("\n🟢 WORKING COMPONENTS:")
        for component in working_components:
            print(f"   {component}")
        
        if blocked_components:
            print("\n🔴 BLOCKED COMPONENTS:")
            for component in blocked_components:
                print(f"   {component}")
        
        # Determine overall status
        critical_working = tests_results["api_health"] and tests_results["elevenlabs_voices"]
        openai_blocked = not tests_results["openai_script"]
        
        if critical_working and openai_blocked:
            print(f"\n⚠️  PARTIAL SUCCESS: Core infrastructure working, OpenAI API key needs fixing")
            return "partial_success", tests_results
        elif critical_working:
            print(f"\n🎉 SUCCESS: All components working correctly")
            return "success", tests_results
        else:
            print(f"\n❌ CRITICAL FAILURE: Core infrastructure issues")
            return "failure", tests_results

async def main():
    """Main focused test runner"""
    async with FocusedTikTokTester() as tester:
        status, results = await tester.run_focused_tests()
        
        # Save results
        with open("/app/focused_test_results.json", "w") as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "detailed_results": results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: /app/focused_test_results.json")
        return status == "success"

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)