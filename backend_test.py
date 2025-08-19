#!/usr/bin/env python3
"""
Comprehensive Backend Testing for TikTok Video Generator
Tests all API endpoints with real API keys provided by user
"""

import asyncio
import aiohttp
import json
import base64
import time
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://prompt-to-video-18.preview.emergentagent.com/api"

class TikTokBackendTester:
    def __init__(self):
        self.session = None
        self.test_results = {}
        self.script_id = None
        self.project_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout for video generation
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
    
    async def test_health_check(self):
        """Test GET /api/ - Health check"""
        test_name = "Health Check (GET /api/)"
        start_time = time.time()
        
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if "message" in data:
                        self.log_test(test_name, True, f"Status: {response.status}, Message: {data['message']}", duration)
                        return True
                    else:
                        self.log_test(test_name, False, f"Status: {response.status}, Missing message field", duration)
                        return False
                else:
                    self.log_test(test_name, False, f"Status: {response.status}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_available_voices(self):
        """Test GET /api/voices/available - ElevenLabs voices"""
        test_name = "Available Voices (GET /api/voices/available)"
        start_time = time.time()
        
        try:
            async with self.session.get(f"{BACKEND_URL}/voices/available") as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if "voices" in data and isinstance(data["voices"], list):
                        voice_count = len(data["voices"])
                        sample_voices = [v["name"] for v in data["voices"][:3]]
                        self.log_test(test_name, True, f"Retrieved {voice_count} voices. Sample: {sample_voices}", duration)
                        return True
                    else:
                        self.log_test(test_name, False, f"Status: {response.status}, Invalid response format", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_generate_script(self):
        """Test POST /api/generate-script - OpenAI GPT script generation"""
        test_name = "Script Generation (POST /api/generate-script)"
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
                    required_fields = ["id", "prompt", "duration", "script_text", "scenes", "created_at"]
                    
                    if all(field in data for field in required_fields):
                        self.script_id = data["id"]  # Store for later tests
                        script_length = len(data["script_text"])
                        scene_count = len(data["scenes"])
                        self.log_test(test_name, True, f"Script generated: {script_length} chars, {scene_count} scenes, ID: {self.script_id}", duration)
                        return True
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test(test_name, False, f"Status: {response.status}, Missing fields: {missing_fields}", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_generate_images(self):
        """Test POST /api/generate-images?script_id={id} - OpenAI DALL-E image generation"""
        test_name = "Image Generation (POST /api/generate-images)"
        start_time = time.time()
        
        if not self.script_id:
            self.log_test(test_name, False, "No script_id available from previous test", 0)
            return False
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-images?script_id={self.script_id}",
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    if "images" in data and "total_generated" in data:
                        image_count = data["total_generated"]
                        if image_count > 0 and len(data["images"]) > 0:
                            # Check first image for valid base64 data
                            first_image = data["images"][0]
                            if "image_base64" in first_image and len(first_image["image_base64"]) > 1000:
                                base64_length = len(first_image["image_base64"])
                                self.log_test(test_name, True, f"Generated {image_count} images, first image: {base64_length} chars base64", duration)
                                return True
                            else:
                                self.log_test(test_name, False, f"Generated {image_count} images but invalid base64 data", duration)
                                return False
                        else:
                            self.log_test(test_name, False, f"No images generated (total: {image_count})", duration)
                            return False
                    else:
                        self.log_test(test_name, False, f"Status: {response.status}, Invalid response format", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_generate_voice(self):
        """Test POST /api/generate-voice - ElevenLabs voice generation with voice_id"""
        test_name = "Voice Generation (POST /api/generate-voice)"
        start_time = time.time()
        
        if not self.script_id:
            self.log_test(test_name, False, "No script_id available from previous test", 0)
            return False
        
        # Get first available voice ID
        first_voice_id = "pNInz6obpgDQGcFmaJgB"  # Default fallback
        try:
            async with self.session.get(f"{BACKEND_URL}/voices/available") as response:
                if response.status == 200:
                    voices_data = await response.json()
                    if "voices" in voices_data and len(voices_data["voices"]) > 0:
                        first_voice_id = voices_data["voices"][0]["voice_id"]
                        print(f"   Using first available voice: {voices_data['voices'][0]['name']} ({first_voice_id})")
        except Exception as e:
            print(f"   Warning: Could not fetch voices, using default: {e}")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/generate-voice?script_id={self.script_id}&voice_id={first_voice_id}",
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["audio_id", "script_id", "voice_id", "duration", "audio_base64"]
                    
                    if all(field in data for field in required_fields):
                        audio_duration = data["duration"]
                        audio_base64_length = len(data["audio_base64"])
                        voice_id = data["voice_id"]
                        self.log_test(test_name, True, f"Voice generated: {audio_duration:.1f}s duration, {audio_base64_length} chars base64, voice: {voice_id}", duration)
                        return True
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test(test_name, False, f"Status: {response.status}, Missing fields: {missing_fields}", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_complete_video_pipeline(self):
        """Test POST /api/create-complete-video - Complete pipeline test with voice_id"""
        test_name = "Complete Video Pipeline (POST /api/create-complete-video)"
        start_time = time.time()
        
        # Get first available voice ID for the test
        first_voice_id = "pNInz6obpgDQGcFmaJgB"  # Default fallback
        try:
            async with self.session.get(f"{BACKEND_URL}/voices/available") as response:
                if response.status == 200:
                    voices_data = await response.json()
                    if "voices" in voices_data and len(voices_data["voices"]) > 0:
                        first_voice_id = voices_data["voices"][0]["voice_id"]
                        print(f"   Using first available voice for complete pipeline: {voices_data['voices'][0]['name']} ({first_voice_id})")
        except Exception as e:
            print(f"   Warning: Could not fetch voices for pipeline, using default: {e}")
        
        try:
            payload = {
                "prompt": "astuces productivité pour étudiants universitaires",
                "duration": 30,
                "voice_id": first_voice_id
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/create-complete-video",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    required_sections = ["project_id", "script", "images", "audio", "video", "status"]
                    
                    if all(section in data for section in required_sections):
                        project_id = data["project_id"]
                        script_length = len(data["script"]["script_text"])
                        image_count = len(data["images"])
                        audio_duration = data["audio"]["duration"]
                        audio_voice_id = data["audio"]["voice_id"]
                        video_base64_length = len(data["video"]["video_base64"])
                        video_resolution = data["video"]["resolution"]
                        
                        self.log_test(test_name, True, f"Complete pipeline success: Project {project_id}, Script {script_length} chars, {image_count} images, Audio {audio_duration:.1f}s (voice: {audio_voice_id}), Video {video_base64_length} chars ({video_resolution})", duration)
                        
                        # Store project_id for retrieval test
                        self.project_id = project_id
                        return True
                    else:
                        missing_sections = [s for s in required_sections if s not in data]
                        self.log_test(test_name, False, f"Status: {response.status}, Missing sections: {missing_sections}", duration)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(test_name, False, f"Status: {response.status}, Error: {error_text}", duration)
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("🚀 Starting TikTok Video Generator Backend Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Available Voices", self.test_available_voices),
            ("Script Generation", self.test_generate_script),
            ("Image Generation", self.test_generate_images),
            ("Voice Generation", self.test_generate_voice),
            ("Complete Pipeline", self.test_complete_video_pipeline)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                success = await test_func()
                if success:
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL: {test_name} - Unexpected error: {str(e)}")
        
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Backend is fully functional.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Minor issues detected.")
        else:
            print("❌ CRITICAL ISSUES DETECTED. Backend needs attention.")
        
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    async with TikTokBackendTester() as tester:
        passed, total, results = await tester.run_all_tests()
        
        # Save detailed results
        with open("/app/backend_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "passed": passed,
                    "total": total,
                    "success_rate": passed / total if total > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "detailed_results": results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
        return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)