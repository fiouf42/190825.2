#!/usr/bin/env python3
"""
Backend API Tests for TikTok Video Generator
Tests the FastAPI backend endpoints with realistic French prompts
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://0280dc01-f7fd-4b8a-9b53-8b0d086b38ea.preview.emergentagent.com/api"
TIMEOUT = 60  # seconds for API calls

class TikTokAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_api_health(self) -> bool:
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"Response: {data}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_generate_script(self, prompt: str = "astuces productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """Test script generation with GPT-4.1"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Testing script generation with prompt: '{prompt}' ({duration}s)")
            response = self.session.post(
                f"{self.base_url}/generate-script",
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["id", "prompt", "duration", "script_text", "scenes", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Script Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate content quality
                script_text = data.get("script_text", "")
                scenes = data.get("scenes", [])
                
                if len(script_text) < 50:
                    self.log_test("Script Generation - Content Length", False, f"Script too short: {len(script_text)} chars")
                    return {}
                
                if len(scenes) < 2:
                    self.log_test("Script Generation - Scenes", False, f"Too few scenes: {len(scenes)}")
                    return {}
                
                self.log_test("Script Generation", True, f"Generated {len(scenes)} scenes, {len(script_text)} chars")
                print(f"   Script preview: {script_text[:100]}...")
                print(f"   Scenes: {len(scenes)} scenes generated")
                
                return data
            else:
                self.log_test("Script Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Script Generation", False, f"Error: {str(e)}")
            return {}
    
    def test_generate_images(self, script_id: str) -> Dict[str, Any]:
        """Test image generation with OpenAI gpt-image-1"""
        try:
            print(f"Testing image generation for script ID: {script_id}")
            response = self.session.post(
                f"{self.base_url}/generate-images",
                params={"script_id": script_id},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["script_id", "images", "total_generated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Image Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                images = data.get("images", [])
                total_generated = data.get("total_generated", 0)
                
                if total_generated == 0:
                    self.log_test("Image Generation", False, "No images generated")
                    return {}
                
                # Validate image structure
                for i, img in enumerate(images):
                    img_fields = ["id", "prompt", "image_base64", "scene_description", "created_at"]
                    missing_img_fields = [field for field in img_fields if field not in img]
                    
                    if missing_img_fields:
                        self.log_test(f"Image {i+1} Structure", False, f"Missing fields: {missing_img_fields}")
                        continue
                    
                    # Check if base64 data exists and looks valid
                    base64_data = img.get("image_base64", "")
                    if len(base64_data) < 100:
                        self.log_test(f"Image {i+1} Base64", False, f"Base64 data too short: {len(base64_data)}")
                        continue
                    
                    # Check charcoal style prompt
                    prompt = img.get("prompt", "")
                    charcoal_keywords = ["charbon", "noir", "gris", "blanc", "granuleux", "fusain"]
                    has_charcoal_style = any(keyword in prompt.lower() for keyword in charcoal_keywords)
                    
                    if not has_charcoal_style:
                        self.log_test(f"Image {i+1} Charcoal Style", False, f"Missing charcoal style keywords in prompt")
                        continue
                    
                    self.log_test(f"Image {i+1} Generation", True, f"Valid base64 data ({len(base64_data)} chars)")
                
                self.log_test("Image Generation", True, f"Generated {total_generated} images")
                return data
            else:
                self.log_test("Image Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Image Generation", False, f"Error: {str(e)}")
            return {}
    
    def test_create_video_project(self, prompt: str = "conseils organisation travail étudiant", duration: int = 45) -> Dict[str, Any]:
        """Test complete video project creation"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Testing complete video project creation with prompt: '{prompt}' ({duration}s)")
            response = self.session.post(
                f"{self.base_url}/create-video-project",
                json=payload,
                timeout=TIMEOUT * 2  # Double timeout for complete project
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate project structure
                required_fields = ["id", "original_prompt", "duration", "script_id", "image_ids", "status", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Video Project Creation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate project data
                if data.get("status") != "completed":
                    self.log_test("Video Project Creation - Status", False, f"Status: {data.get('status')}")
                    return {}
                
                if not data.get("script_id"):
                    self.log_test("Video Project Creation - Script ID", False, "No script ID")
                    return {}
                
                image_ids = data.get("image_ids", [])
                if len(image_ids) == 0:
                    self.log_test("Video Project Creation - Images", False, "No image IDs")
                    return {}
                
                self.log_test("Video Project Creation", True, f"Project created with {len(image_ids)} images")
                return data
            else:
                self.log_test("Video Project Creation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Video Project Creation", False, f"Error: {str(e)}")
            return {}
    
    def test_get_project(self, project_id: str) -> Dict[str, Any]:
        """Test project retrieval"""
        try:
            print(f"Testing project retrieval for ID: {project_id}")
            response = self.session.get(
                f"{self.base_url}/project/{project_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["project", "script", "images"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Project Retrieval - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                project = data.get("project", {})
                script = data.get("script", {})
                images = data.get("images", [])
                
                if not project:
                    self.log_test("Project Retrieval - Project Data", False, "No project data")
                    return {}
                
                if not script:
                    self.log_test("Project Retrieval - Script Data", False, "No script data")
                    return {}
                
                if len(images) == 0:
                    self.log_test("Project Retrieval - Images Data", False, "No images data")
                    return {}
                
                self.log_test("Project Retrieval", True, f"Retrieved project with {len(images)} images")
                return data
            else:
                self.log_test("Project Retrieval", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Project Retrieval", False, f"Error: {str(e)}")
            return {}
    
    def test_mock_pipeline(self, prompt: str = "astuces productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """Test complete mock pipeline system"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Testing MOCK PIPELINE with prompt: '{prompt}' ({duration}s)")
            response = self.session.post(
                f"{self.base_url}/test-mock-pipeline",
                json=payload,
                timeout=TIMEOUT * 3  # Extended timeout for complete pipeline
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure (video_size OR video_error depending on success)
                required_fields = ["status", "project_id", "script", "images_count", "audio_duration", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Mock Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Check status
                status = data.get("status")
                if status not in ["mock_test_success", "mock_test_partial"]:
                    self.log_test("Mock Pipeline - Status", False, f"Unexpected status: {status}")
                    return {}
                
                # Validate script component
                script = data.get("script", {})
                if not script or not script.get("script_text") or not script.get("scenes"):
                    self.log_test("Mock Pipeline - Script Component", False, "Invalid script data")
                    return {}
                
                # Validate images component
                images_count = data.get("images_count", 0)
                if images_count == 0:
                    self.log_test("Mock Pipeline - Images Component", False, "No images generated")
                    return {}
                
                # Validate audio component
                audio_duration = data.get("audio_duration", 0)
                if audio_duration == 0:
                    self.log_test("Mock Pipeline - Audio Component", False, "No audio duration")
                    return {}
                
                # Validate video component (if status is success)
                if status == "mock_test_success":
                    video_size = data.get("video_size", 0)
                    if video_size == 0:
                        self.log_test("Mock Pipeline - Video Component", False, "No video generated")
                        return {}
                    
                    self.log_test("Mock Pipeline - Complete Success", True, f"Full pipeline: script + {images_count} images + audio + video ({video_size} chars)")
                else:
                    # Partial success - script and images work but video assembly failed
                    video_error = data.get("video_error", "Unknown error")
                    self.log_test("Mock Pipeline - Partial Success", True, f"Script + {images_count} images work, video error: {video_error}")
                
                self.log_test("Mock Pipeline Test", True, f"Status: {status}, Components: script + {images_count} images + audio")
                return data
            else:
                self.log_test("Mock Pipeline Test", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Mock Pipeline Test", False, f"Error: {str(e)}")
            return {}
    
    def test_voices_available(self) -> Dict[str, Any]:
        """Test ElevenLabs voices endpoint with new API key"""
        try:
            print("Testing ElevenLabs voices endpoint...")
            response = self.session.get(
                f"{self.base_url}/voices/available",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "voices" not in data:
                    self.log_test("Voices Available - Structure", False, "Missing 'voices' field")
                    return {}
                
                voices = data.get("voices", [])
                if len(voices) == 0:
                    self.log_test("Voices Available", False, "No voices returned")
                    return {}
                
                # Validate voice structure
                for i, voice in enumerate(voices[:3]):  # Check first 3 voices
                    voice_fields = ["voice_id", "name", "category"]
                    missing_voice_fields = [field for field in voice_fields if field not in voice]
                    
                    if missing_voice_fields:
                        self.log_test(f"Voice {i+1} Structure", False, f"Missing fields: {missing_voice_fields}")
                        continue
                
                self.log_test("Voices Available", True, f"Retrieved {len(voices)} voices from ElevenLabs")
                print(f"   Sample voices: {[v.get('name', 'Unknown') for v in voices[:3]]}")
                return data
            else:
                self.log_test("Voices Available", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Voices Available", False, f"Error: {str(e)}")
            return {}
    
    def test_real_voice_generation(self, script_id: str) -> Dict[str, Any]:
        """Test real ElevenLabs voice generation (only if mock pipeline works)"""
        try:
            print(f"Testing REAL ElevenLabs voice generation for script: {script_id}")
            response = self.session.post(
                f"{self.base_url}/generate-voice",
                params={"script_id": script_id, "use_real_api": "true"},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["audio_id", "script_id", "voice_id", "duration", "audio_base64", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Real Voice Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate audio data
                audio_base64 = data.get("audio_base64", "")
                if len(audio_base64) < 1000:  # Real audio should be substantial
                    self.log_test("Real Voice Generation - Audio Data", False, f"Audio data too short: {len(audio_base64)} chars")
                    return {}
                
                duration = data.get("duration", 0)
                if duration == 0:
                    self.log_test("Real Voice Generation - Duration", False, "No duration provided")
                    return {}
                
                self.log_test("Real Voice Generation", True, f"Generated {duration}s audio ({len(audio_base64)} chars)")
                return data
            else:
                # Check if it's a known ElevenLabs limitation
                if response.status_code == 401 and "free tier" in response.text.lower():
                    self.log_test("Real Voice Generation", False, "ElevenLabs free tier disabled - requires paid subscription")
                else:
                    self.log_test("Real Voice Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Real Voice Generation", False, f"Error: {str(e)}")
            return {}

    def test_complete_video_pipeline(self, prompt: str = "astuces productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """Test the COMPLETE video pipeline endpoint with NEW OpenAI API key"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"🎯 TESTING COMPLETE VIDEO PIPELINE with NEW OpenAI API key")
            print(f"   Prompt: '{prompt}' ({duration}s)")
            print(f"   Expected: Script (GPT-4.1) → Images (OpenAI charcoal style) → Voice (ElevenLabs Nicolas) → Video (FFmpeg TikTok format)")
            
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT * 4  # Extended timeout for complete pipeline
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["project_id", "script", "images", "audio", "video", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Complete Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate status
                if data.get("status") != "completed":
                    self.log_test("Complete Pipeline - Status", False, f"Status: {data.get('status')}")
                    return {}
                
                # Validate script component (GPT-4.1)
                script = data.get("script", {})
                if not script or not script.get("script_text") or not script.get("scenes"):
                    self.log_test("Complete Pipeline - Script (GPT-4.1)", False, "Invalid script data")
                    return {}
                
                script_text = script.get("script_text", "")
                scenes = script.get("scenes", [])
                if len(script_text) < 500:  # Expect substantial French script
                    self.log_test("Complete Pipeline - Script Quality", False, f"Script too short: {len(script_text)} chars")
                    return {}
                
                self.log_test("Complete Pipeline - Script (GPT-4.1)", True, f"Generated {len(scenes)} scenes, {len(script_text)} chars")
                
                # Validate images component (OpenAI charcoal style)
                images = data.get("images", [])
                if len(images) == 0:
                    self.log_test("Complete Pipeline - Images (OpenAI)", False, "No images generated")
                    return {}
                
                # Check image quality and charcoal style
                valid_images = 0
                for i, img in enumerate(images):
                    if not img.get("image_base64") or len(img.get("image_base64", "")) < 1000:
                        self.log_test(f"Complete Pipeline - Image {i+1} Quality", False, f"Invalid base64 data")
                        continue
                    
                    # Check charcoal style in prompt
                    prompt_text = img.get("prompt", "").lower()
                    charcoal_keywords = ["charbon", "noir", "gris", "blanc", "granuleux", "fusain"]
                    if not any(keyword in prompt_text for keyword in charcoal_keywords):
                        self.log_test(f"Complete Pipeline - Image {i+1} Style", False, "Missing charcoal style")
                        continue
                    
                    valid_images += 1
                
                if valid_images == 0:
                    self.log_test("Complete Pipeline - Images (OpenAI)", False, "No valid images with charcoal style")
                    return {}
                
                self.log_test("Complete Pipeline - Images (OpenAI)", True, f"Generated {valid_images} valid charcoal-style images")
                
                # Validate audio component (ElevenLabs)
                audio = data.get("audio", {})
                if not audio or not audio.get("audio_id") or not audio.get("duration"):
                    self.log_test("Complete Pipeline - Audio (ElevenLabs)", False, "Invalid audio data")
                    return {}
                
                audio_duration = audio.get("duration", 0)
                if audio_duration < 10:  # Expect reasonable duration
                    self.log_test("Complete Pipeline - Audio Duration", False, f"Audio too short: {audio_duration}s")
                    return {}
                
                self.log_test("Complete Pipeline - Audio (ElevenLabs)", True, f"Generated {audio_duration}s audio with voice {audio.get('voice_id', 'unknown')}")
                
                # Validate video component (FFmpeg TikTok format)
                video = data.get("video", {})
                if not video or not video.get("video_base64") or not video.get("resolution"):
                    self.log_test("Complete Pipeline - Video (FFmpeg)", False, "Invalid video data")
                    return {}
                
                video_base64 = video.get("video_base64", "")
                if len(video_base64) < 10000:  # Expect substantial video data
                    self.log_test("Complete Pipeline - Video Size", False, f"Video too small: {len(video_base64)} chars")
                    return {}
                
                resolution = video.get("resolution", "")
                if resolution != "1080x1920":
                    self.log_test("Complete Pipeline - Video Format", False, f"Wrong resolution: {resolution}, expected 1080x1920")
                    return {}
                
                video_duration = video.get("duration", 0)
                if abs(video_duration - audio_duration) > 5:  # Allow 5s tolerance
                    self.log_test("Complete Pipeline - Video/Audio Sync", False, f"Duration mismatch: video {video_duration}s vs audio {audio_duration}s")
                    return {}
                
                self.log_test("Complete Pipeline - Video (FFmpeg)", True, f"Generated {video_duration}s TikTok video ({len(video_base64)} chars, {resolution})")
                
                # Overall success
                self.log_test("🎉 COMPLETE VIDEO PIPELINE", True, f"Full end-to-end pipeline successful: Script → {len(images)} Images → {audio_duration}s Audio → {resolution} Video")
                
                return data
            else:
                error_text = response.text
                if "401" in error_text and "unauthorized" in error_text.lower():
                    self.log_test("Complete Pipeline - OpenAI API Key", False, "OpenAI API key is INVALID (401 Unauthorized)")
                elif "403" in error_text:
                    self.log_test("Complete Pipeline - API Access", False, "API access forbidden (403)")
                else:
                    self.log_test("Complete Pipeline", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Complete Pipeline", False, f"Error: {str(e)}")
            return {}

    def run_comprehensive_test(self):
        """Run focused tests on COMPLETE VIDEO PIPELINE with NEW OpenAI API key"""
        print("=" * 80)
        print("🎬 TikTok Video Generator - COMPLETE PIPELINE TESTING WITH NEW OPENAI API KEY")
        print("=" * 80)
        print(f"Testing API at: {self.base_url}")
        print("🔑 NEW OpenAI API Key: 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")
        print("🎯 Focus: Complete video pipeline validation")
        print("📋 Expected: Script (GPT-4.1 French) → Images (OpenAI charcoal style) → Voice (ElevenLabs Nicolas) → Video (FFmpeg TikTok)")
        print()
        
        # Test 1: API Health
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        print()
        
        # Test 2: ElevenLabs Voices (should work - 19 voices expected)
        print("🔊 Testing ElevenLabs Voice Availability")
        voices_data = self.test_voices_available()
        if not voices_data:
            print("❌ Voice fetching failed - this will block voice generation.")
        else:
            print(f"✅ ElevenLabs API working - {len(voices_data.get('voices', []))} voices available")
        
        print()
        
        # Test 3: PRIORITY - Complete Video Pipeline Test
        print("🎯 PRIORITY TEST: Complete Video Pipeline with NEW OpenAI API Key")
        print("   Testing: /api/create-complete-video")
        print("   Prompt: 'astuces productivité étudiants' (30s)")
        complete_pipeline_data = self.test_complete_video_pipeline("astuces productivité étudiants", 30)
        
        if not complete_pipeline_data:
            print("❌ Complete pipeline failed. This is the main focus.")
            print("   Checking individual components...")
            
            # Fallback: Test individual components to identify the issue
            print("\n🔍 DIAGNOSTIC: Testing individual components...")
            
            # Test script generation
            script_data = self.test_generate_script("astuces productivité étudiants", 30)
            if script_data:
                print("✅ Script generation working")
                
                # Test image generation
                images_data = self.test_generate_images(script_data.get("id"))
                if images_data:
                    print("✅ Image generation working")
                else:
                    print("❌ Image generation failed - likely OpenAI API key issue")
            else:
                print("❌ Script generation failed - likely OpenAI API key issue")
        
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 80)
        print("🎬 COMPLETE PIPELINE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Focus on complete pipeline result
        complete_pipeline_success = any(
            result["test"] == "🎉 COMPLETE VIDEO PIPELINE" and result["success"] 
            for result in self.test_results
        )
        
        if complete_pipeline_success:
            print("🎉 COMPLETE VIDEO PIPELINE TEST PASSED!")
            print("✅ NEW OpenAI API key is working correctly")
            print("✅ Script generation (GPT-4.1) working")
            print("✅ Image generation (OpenAI charcoal style) working") 
            print("✅ Voice generation (ElevenLabs) working")
            print("✅ Video assembly (FFmpeg TikTok format) working")
            print("✅ Pipeline ready for frontend integration!")
            return True
        else:
            print("⚠️  COMPLETE VIDEO PIPELINE TEST FAILED")
            
            # Check if it's specifically an OpenAI API key issue
            openai_key_issue = any(
                "OpenAI API key is INVALID" in result["details"] 
                for result in self.test_results if not result["success"]
            )
            
            if openai_key_issue:
                print("❌ CRITICAL: OpenAI API key provided by user is INVALID")
                print("   The key returns 401 Unauthorized errors")
                print("   User needs to provide a valid OpenAI API key")
            else:
                print("❌ Pipeline has other issues that need attention")
            
            return False

def main():
    """Main test execution"""
    tester = TikTokAPITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n✅ Backend API is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Backend API has issues that need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()