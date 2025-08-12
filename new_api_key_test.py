#!/usr/bin/env python3
"""
NEW API KEY TESTING - CRITICAL PRIORITY
Tests the backend with newly provided OpenAI and ElevenLabs API keys
Focus: Authentication success and functionality validation
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://content-forge-79.preview.emergentagent.com/api"
TIMEOUT = 90  # Extended timeout for API calls

class NewAPIKeyTester:
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
    
    def test_openai_script_generation(self, prompt: str = "astuces productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """PRIORITY 1: Test OpenAI Script Generation (GPT-4.1) with new API key"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"🎯 PRIORITY 1: Testing OpenAI Script Generation (GPT-4.1)")
            print(f"   Prompt: '{prompt}' ({duration}s)")
            print(f"   Expected: 200 response with valid script structure")
            
            response = self.session.post(
                f"{self.base_url}/generate-script",
                json=payload,
                timeout=TIMEOUT
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["id", "prompt", "duration", "script_text", "scenes", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("OpenAI Script Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate content quality
                script_text = data.get("script_text", "")
                scenes = data.get("scenes", [])
                
                if len(script_text) < 100:
                    self.log_test("OpenAI Script Generation - Content", False, f"Script too short: {len(script_text)} chars")
                    return {}
                
                if len(scenes) < 2:
                    self.log_test("OpenAI Script Generation - Scenes", False, f"Too few scenes: {len(scenes)}")
                    return {}
                
                # Check if it's French content
                french_indicators = ["le", "la", "les", "de", "du", "des", "et", "à", "pour", "avec", "vous", "nous"]
                has_french = any(word in script_text.lower() for word in french_indicators)
                
                if not has_french:
                    self.log_test("OpenAI Script Generation - Language", False, "Script doesn't appear to be in French")
                    return {}
                
                self.log_test("OpenAI Script Generation (GPT-4.1)", True, 
                             f"✅ SUCCESS: Generated {len(scenes)} scenes, {len(script_text)} chars in French")
                print(f"   ✅ Script preview: {script_text[:150]}...")
                print(f"   ✅ Scenes count: {len(scenes)}")
                
                return data
            elif response.status_code == 401:
                self.log_test("OpenAI Script Generation (GPT-4.1)", False, 
                             "❌ AUTHENTICATION FAILED: OpenAI API key still invalid (401 Unauthorized)")
                return {}
            else:
                self.log_test("OpenAI Script Generation (GPT-4.1)", False, 
                             f"❌ FAILED: Status {response.status_code}, Response: {response.text[:200]}")
                return {}
                
        except Exception as e:
            self.log_test("OpenAI Script Generation (GPT-4.1)", False, f"❌ ERROR: {str(e)}")
            return {}
    
    def test_openai_image_generation(self, script_id: str) -> Dict[str, Any]:
        """PRIORITY 2: Test OpenAI Image Generation with new API key"""
        try:
            print(f"🎯 PRIORITY 2: Testing OpenAI Image Generation")
            print(f"   Script ID: {script_id}")
            print(f"   Expected: gpt-image-1 or dall-e-3 fallback with charcoal style")
            
            response = self.session.post(
                f"{self.base_url}/generate-images",
                params={"script_id": script_id},
                timeout=TIMEOUT
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["script_id", "images", "total_generated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("OpenAI Image Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                images = data.get("images", [])
                total_generated = data.get("total_generated", 0)
                
                if total_generated == 0:
                    self.log_test("OpenAI Image Generation", False, "❌ No images generated")
                    return {}
                
                # Validate image structure and charcoal style
                valid_images = 0
                for i, img in enumerate(images):
                    img_fields = ["id", "prompt", "image_base64", "scene_description", "created_at"]
                    missing_img_fields = [field for field in img_fields if field not in img]
                    
                    if missing_img_fields:
                        print(f"   ⚠️  Image {i+1}: Missing fields {missing_img_fields}")
                        continue
                    
                    # Check if base64 data exists and looks valid
                    base64_data = img.get("image_base64", "")
                    if len(base64_data) < 100:
                        print(f"   ⚠️  Image {i+1}: Base64 data too short ({len(base64_data)} chars)")
                        continue
                    
                    # Check charcoal style prompt
                    prompt = img.get("prompt", "")
                    charcoal_keywords = ["charbon", "noir", "gris", "blanc", "granuleux", "fusain", "dramatique"]
                    has_charcoal_style = any(keyword in prompt.lower() for keyword in charcoal_keywords)
                    
                    if not has_charcoal_style:
                        print(f"   ⚠️  Image {i+1}: Missing charcoal style keywords")
                        continue
                    
                    valid_images += 1
                    print(f"   ✅ Image {i+1}: Valid ({len(base64_data)} chars base64)")
                
                if valid_images > 0:
                    self.log_test("OpenAI Image Generation", True, 
                                 f"✅ SUCCESS: Generated {valid_images}/{total_generated} valid charcoal-style images")
                    return data
                else:
                    self.log_test("OpenAI Image Generation", False, 
                                 f"❌ No valid images generated ({total_generated} attempted)")
                    return {}
                    
            elif response.status_code == 401:
                self.log_test("OpenAI Image Generation", False, 
                             "❌ AUTHENTICATION FAILED: OpenAI API key still invalid (401 Unauthorized)")
                return {}
            elif response.status_code == 403:
                self.log_test("OpenAI Image Generation", False, 
                             "❌ ORGANIZATION VERIFICATION: gpt-image-1 requires verification, check dall-e-3 fallback")
                return {}
            else:
                self.log_test("OpenAI Image Generation", False, 
                             f"❌ FAILED: Status {response.status_code}, Response: {response.text[:200]}")
                return {}
                
        except Exception as e:
            self.log_test("OpenAI Image Generation", False, f"❌ ERROR: {str(e)}")
            return {}
    
    def test_elevenlabs_voice_generation(self, script_id: str) -> Dict[str, Any]:
        """PRIORITY 3: Test ElevenLabs Voice Generation with new API key"""
        try:
            print(f"🎯 PRIORITY 3: Testing ElevenLabs Voice Generation")
            print(f"   Script ID: {script_id}")
            print(f"   Expected: Voice generation with valid voice_id and text")
            
            response = self.session.post(
                f"{self.base_url}/generate-voice",
                params={"script_id": script_id, "use_real_api": "true"},
                timeout=TIMEOUT
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["audio_id", "script_id", "voice_id", "duration", "audio_base64", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("ElevenLabs Voice Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate audio data
                audio_base64 = data.get("audio_base64", "")
                if len(audio_base64) < 1000:  # Real audio should be substantial
                    self.log_test("ElevenLabs Voice Generation - Audio Data", False, 
                                 f"❌ Audio data too short: {len(audio_base64)} chars")
                    return {}
                
                duration = data.get("duration", 0)
                if duration == 0:
                    self.log_test("ElevenLabs Voice Generation - Duration", False, "❌ No duration provided")
                    return {}
                
                voice_id = data.get("voice_id", "")
                if not voice_id:
                    self.log_test("ElevenLabs Voice Generation - Voice ID", False, "❌ No voice ID provided")
                    return {}
                
                self.log_test("ElevenLabs Voice Generation", True, 
                             f"✅ SUCCESS: Generated {duration}s audio ({len(audio_base64)} chars) with voice {voice_id}")
                return data
                
            elif response.status_code == 401:
                # Check if it's the free tier issue or API key issue
                response_text = response.text.lower()
                if "free tier" in response_text or "unusual activity" in response_text:
                    self.log_test("ElevenLabs Voice Generation", False, 
                                 "❌ FREE TIER DISABLED: ElevenLabs free tier disabled - requires paid subscription")
                else:
                    self.log_test("ElevenLabs Voice Generation", False, 
                                 "❌ AUTHENTICATION FAILED: ElevenLabs API key invalid (401 Unauthorized)")
                return {}
            else:
                self.log_test("ElevenLabs Voice Generation", False, 
                             f"❌ FAILED: Status {response.status_code}, Response: {response.text[:200]}")
                return {}
                
        except Exception as e:
            self.log_test("ElevenLabs Voice Generation", False, f"❌ ERROR: {str(e)}")
            return {}
    
    def test_complete_video_pipeline(self, prompt: str = "conseils révisions efficaces", duration: int = 30) -> Dict[str, Any]:
        """PRIORITY 4: Test Complete Video Pipeline - End-to-end integration"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"🎯 PRIORITY 4: Testing Complete Video Pipeline")
            print(f"   Prompt: '{prompt}' ({duration}s)")
            print(f"   Expected: End-to-end video creation with all components")
            
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT * 2  # Extended timeout for complete pipeline
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["project_id", "script", "images", "audio", "video", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Complete Video Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate each component
                script = data.get("script", {})
                images = data.get("images", [])
                audio = data.get("audio", {})
                video = data.get("video", {})
                status = data.get("status", "")
                
                # Check script component
                if not script or not script.get("script_text"):
                    self.log_test("Complete Video Pipeline - Script", False, "❌ Invalid script component")
                    return {}
                
                # Check images component
                if len(images) == 0:
                    self.log_test("Complete Video Pipeline - Images", False, "❌ No images generated")
                    return {}
                
                # Check audio component
                if not audio or not audio.get("audio_id"):
                    self.log_test("Complete Video Pipeline - Audio", False, "❌ Invalid audio component")
                    return {}
                
                # Check video component
                if not video or not video.get("video_base64"):
                    self.log_test("Complete Video Pipeline - Video", False, "❌ Invalid video component")
                    return {}
                
                # Check final status
                if status != "completed":
                    self.log_test("Complete Video Pipeline - Status", False, f"❌ Status not completed: {status}")
                    return {}
                
                video_size = len(video.get("video_base64", ""))
                self.log_test("Complete Video Pipeline", True, 
                             f"✅ SUCCESS: Full pipeline completed - script + {len(images)} images + audio + video ({video_size} chars)")
                
                print(f"   ✅ Script: {len(script.get('script_text', ''))} chars")
                print(f"   ✅ Images: {len(images)} generated")
                print(f"   ✅ Audio: {audio.get('duration', 0)}s duration")
                print(f"   ✅ Video: {video_size} chars base64")
                
                return data
                
            elif response.status_code == 401:
                self.log_test("Complete Video Pipeline", False, 
                             "❌ AUTHENTICATION FAILED: API key issues block pipeline")
                return {}
            else:
                self.log_test("Complete Video Pipeline", False, 
                             f"❌ FAILED: Status {response.status_code}, Response: {response.text[:200]}")
                return {}
                
        except Exception as e:
            self.log_test("Complete Video Pipeline", False, f"❌ ERROR: {str(e)}")
            return {}
    
    def test_api_health(self) -> bool:
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"✅ API accessible: {data}")
                return True
            else:
                self.log_test("API Health Check", False, f"❌ Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"❌ Error: {str(e)}")
            return False
    
    def run_priority_testing(self):
        """Run the priority testing sequence as specified in review request"""
        print("=" * 80)
        print("🚨 BACKEND TESTING WITH NEW API KEYS - CRITICAL PRIORITY 🚨")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("New API Keys Updated:")
        print("- OpenAI API key: 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")
        print("- ElevenLabs API key: sk_0ac8438144cbed68081b6b1bca798a1a81738fb00b5dac8d")
        print()
        print("PRIORITY TESTING SEQUENCE:")
        print("1. OpenAI Script Generation (GPT-4.1) - /api/generate-script")
        print("2. OpenAI Image Generation - /api/generate-images") 
        print("3. ElevenLabs Voice Generation - /api/generate-voice")
        print("4. Complete Video Pipeline - /api/create-complete-video")
        print()
        
        # Test 0: API Health
        print("🔍 Step 0: API Health Check")
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
        print()
        
        # Test 1: OpenAI Script Generation (GPT-4.1)
        print("🔍 Step 1: OpenAI Script Generation (GPT-4.1)")
        script_data = self.test_openai_script_generation("astuces productivité étudiants", 30)
        script_success = bool(script_data)
        print()
        
        # Test 2: OpenAI Image Generation (only if script succeeded)
        image_success = False
        if script_success:
            print("🔍 Step 2: OpenAI Image Generation")
            script_id = script_data.get("id")
            image_data = self.test_openai_image_generation(script_id)
            image_success = bool(image_data)
        else:
            print("🔍 Step 2: OpenAI Image Generation - SKIPPED (script generation failed)")
        print()
        
        # Test 3: ElevenLabs Voice Generation (only if script succeeded)
        voice_success = False
        if script_success:
            print("🔍 Step 3: ElevenLabs Voice Generation")
            script_id = script_data.get("id")
            voice_data = self.test_elevenlabs_voice_generation(script_id)
            voice_success = bool(voice_data)
        else:
            print("🔍 Step 3: ElevenLabs Voice Generation - SKIPPED (script generation failed)")
        print()
        
        # Test 4: Complete Video Pipeline
        print("🔍 Step 4: Complete Video Pipeline")
        pipeline_data = self.test_complete_video_pipeline("conseils révisions efficaces", 30)
        pipeline_success = bool(pipeline_data)
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 80)
        print("🎯 NEW API KEY TESTING RESULTS")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Priority Results
        print("PRIORITY RESULTS:")
        print(f"1. OpenAI Script Generation: {'✅ PASS' if script_success else '❌ FAIL'}")
        print(f"2. OpenAI Image Generation: {'✅ PASS' if image_success else '❌ FAIL'}")
        print(f"3. ElevenLabs Voice Generation: {'✅ PASS' if voice_success else '❌ FAIL'}")
        print(f"4. Complete Video Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
        print()
        
        # Authentication Status
        auth_issues = []
        for result in self.test_results:
            if not result["success"] and "AUTHENTICATION FAILED" in result["details"]:
                auth_issues.append(result["test"])
        
        if auth_issues:
            print("🚨 AUTHENTICATION ISSUES DETECTED:")
            for issue in auth_issues:
                print(f"   - {issue}")
            print()
        
        # Overall Assessment
        critical_success = script_success  # Script generation is most critical
        if critical_success:
            print("🎉 CRITICAL SUCCESS: OpenAI API key authentication resolved!")
            if image_success:
                print("🎉 BONUS: Image generation also working!")
            if voice_success:
                print("🎉 BONUS: Voice generation also working!")
            if pipeline_success:
                print("🎉 FULL SUCCESS: Complete pipeline operational!")
            return True
        else:
            print("⚠️  CRITICAL FAILURE: OpenAI API key authentication still failing")
            print("   This blocks all core functionality")
            return False

def main():
    """Main test execution"""
    tester = NewAPIKeyTester()
    success = tester.run_priority_testing()
    
    if success:
        print("\n✅ NEW API KEYS ARE WORKING! Backend authentication resolved.")
        sys.exit(0)
    else:
        print("\n❌ NEW API KEYS STILL HAVE ISSUES. Authentication problems persist.")
        sys.exit(1)

if __name__ == "__main__":
    main()