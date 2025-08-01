#!/usr/bin/env python3
"""
OpenAI API Key Validation Test
Tests the new OpenAI API key with the complete video pipeline
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://5df54ba3-897c-4805-b2d5-ffbd6fd6461c.preview.emergentagent.com/api"
TIMEOUT = 120  # Extended timeout for complete pipeline

class OpenAIKeyTester:
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
    
    def test_complete_video_pipeline(self, prompt: str = "astuces productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """Test the complete video pipeline with new OpenAI API key"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"🎯 TESTING COMPLETE VIDEO PIPELINE")
            print(f"   Prompt: '{prompt}'")
            print(f"   Duration: {duration}s")
            print(f"   Expected: No 401 Unauthorized errors")
            print()
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT
            )
            end_time = time.time()
            
            print(f"   Response time: {end_time - start_time:.1f}s")
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 401:
                self.log_test("Complete Video Pipeline - Authentication", False, "401 Unauthorized - OpenAI API key still invalid")
                return {}
            elif response.status_code != 200:
                self.log_test("Complete Video Pipeline - HTTP Status", False, f"Status: {response.status_code}, Response: {response.text[:500]}")
                return {}
            
            # Parse response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.log_test("Complete Video Pipeline - JSON Parse", False, f"Invalid JSON response: {str(e)}")
                return {}
            
            # Validate response structure
            required_fields = ["project_id", "script", "images", "audio", "video", "status"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Complete Video Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                return {}
            
            # Validate each component
            success_components = []
            
            # 1. Script validation
            script = data.get("script", {})
            if script and script.get("script_text") and script.get("scenes"):
                script_length = len(script.get("script_text", ""))
                scenes_count = len(script.get("scenes", []))
                success_components.append(f"Script ({script_length} chars, {scenes_count} scenes)")
                self.log_test("Complete Pipeline - Script Generation", True, f"GPT-4.1 generated {script_length} chars with {scenes_count} scenes")
            else:
                self.log_test("Complete Pipeline - Script Generation", False, "Invalid script data")
                return {}
            
            # 2. Images validation
            images = data.get("images", [])
            if images and len(images) > 0:
                valid_images = 0
                for img in images:
                    if img.get("image_base64") and len(img.get("image_base64", "")) > 1000:
                        valid_images += 1
                
                if valid_images > 0:
                    success_components.append(f"Images ({valid_images} valid)")
                    self.log_test("Complete Pipeline - Image Generation", True, f"OpenAI generated {valid_images} valid images")
                else:
                    self.log_test("Complete Pipeline - Image Generation", False, "No valid images generated")
                    return {}
            else:
                self.log_test("Complete Pipeline - Image Generation", False, "No images in response")
                return {}
            
            # 3. Audio validation
            audio = data.get("audio", {})
            if audio and audio.get("audio_id") and audio.get("duration"):
                audio_duration = audio.get("duration", 0)
                success_components.append(f"Audio ({audio_duration}s)")
                self.log_test("Complete Pipeline - Voice Generation", True, f"ElevenLabs generated {audio_duration}s audio")
            else:
                self.log_test("Complete Pipeline - Voice Generation", False, "Invalid audio data")
                return {}
            
            # 4. Video validation
            video = data.get("video", {})
            if video and video.get("video_base64") and video.get("duration"):
                video_size = len(video.get("video_base64", ""))
                video_duration = video.get("duration", 0)
                success_components.append(f"Video ({video_duration}s, {video_size} chars)")
                self.log_test("Complete Pipeline - Video Assembly", True, f"FFmpeg assembled {video_duration}s video ({video_size} chars)")
            else:
                self.log_test("Complete Pipeline - Video Assembly", False, "Invalid video data")
                return {}
            
            # 5. Overall status
            status = data.get("status", "")
            if status == "completed":
                self.log_test("Complete Pipeline - Status", True, "Pipeline completed successfully")
            else:
                self.log_test("Complete Pipeline - Status", False, f"Unexpected status: {status}")
                return {}
            
            # SUCCESS!
            components_str = " → ".join(success_components)
            self.log_test("Complete Video Pipeline", True, f"Full pipeline working: {components_str}")
            
            return data
            
        except requests.exceptions.Timeout:
            self.log_test("Complete Video Pipeline", False, f"Request timeout after {TIMEOUT}s")
            return {}
        except Exception as e:
            self.log_test("Complete Video Pipeline", False, f"Error: {str(e)}")
            return {}
    
    def test_individual_components(self):
        """Test individual components to isolate any issues"""
        print("🔍 TESTING INDIVIDUAL COMPONENTS")
        print()
        
        # Test script generation
        try:
            payload = {"prompt": "astuces productivité étudiants", "duration": 30}
            response = self.session.post(f"{self.base_url}/generate-script", json=payload, timeout=60)
            
            if response.status_code == 401:
                self.log_test("Individual - Script Generation", False, "401 Unauthorized - OpenAI API key invalid")
                return False
            elif response.status_code == 200:
                data = response.json()
                if data.get("script_text") and data.get("scenes"):
                    self.log_test("Individual - Script Generation", True, f"GPT-4.1 working: {len(data.get('script_text', ''))} chars")
                    script_id = data.get("id")
                    
                    # Test image generation
                    if script_id:
                        img_response = self.session.post(f"{self.base_url}/generate-images", params={"script_id": script_id}, timeout=60)
                        if img_response.status_code == 401:
                            self.log_test("Individual - Image Generation", False, "401 Unauthorized - OpenAI API key invalid")
                            return False
                        elif img_response.status_code == 200:
                            img_data = img_response.json()
                            images = img_data.get("images", [])
                            valid_images = sum(1 for img in images if img.get("image_base64") and len(img.get("image_base64", "")) > 1000)
                            if valid_images > 0:
                                self.log_test("Individual - Image Generation", True, f"OpenAI images working: {valid_images} valid images")
                            else:
                                self.log_test("Individual - Image Generation", False, "No valid images generated")
                        else:
                            self.log_test("Individual - Image Generation", False, f"Status: {img_response.status_code}")
                else:
                    self.log_test("Individual - Script Generation", False, "Invalid script response")
            else:
                self.log_test("Individual - Script Generation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Individual Components Test", False, f"Error: {str(e)}")
            return False
        
        return True
    
    def run_openai_key_validation(self):
        """Run OpenAI API key validation test"""
        print("=" * 70)
        print("🔑 OPENAI API KEY VALIDATION TEST")
        print("=" * 70)
        print(f"Testing API at: {self.base_url}")
        print("New OpenAI API Key: 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")
        print("Expected: Complete pipeline should work without 401 errors")
        print()
        
        # Test API health first
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code != 200:
                print("❌ API is not accessible. Stopping tests.")
                return False
            self.log_test("API Health Check", True, "API is accessible")
        except Exception as e:
            print(f"❌ API connection failed: {str(e)}")
            return False
        
        print()
        
        # Main test: Complete video pipeline
        pipeline_data = self.test_complete_video_pipeline("astuces productivité étudiants", 30)
        
        if not pipeline_data:
            print()
            print("🔍 Pipeline failed, testing individual components...")
            self.test_individual_components()
        
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 70)
        print("🎯 OPENAI API KEY TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        # Check for 401 errors specifically
        auth_failures = [result for result in self.test_results if "401" in result.get("details", "")]
        
        if auth_failures:
            print()
            print("❌ AUTHENTICATION FAILURES DETECTED:")
            for failure in auth_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
            print("🔑 CONCLUSION: OpenAI API key is still INVALID")
            return False
        
        # Check if complete pipeline worked
        pipeline_success = any(
            result["test"] == "Complete Video Pipeline" and result["success"] 
            for result in self.test_results
        )
        
        if pipeline_success:
            print()
            print("🎉 SUCCESS: OpenAI API key is WORKING!")
            print("✅ Complete video pipeline functional")
            print("✅ No 401 Unauthorized errors")
            print("✅ GPT-4.1 script generation working")
            print("✅ OpenAI image generation working")
            print("✅ ElevenLabs voice generation working")
            print("✅ FFmpeg video assembly working")
            return True
        else:
            print()
            print("⚠️  PARTIAL SUCCESS: No 401 errors but pipeline has other issues")
            return False

def main():
    """Main test execution"""
    tester = OpenAIKeyTester()
    success = tester.run_openai_key_validation()
    
    if success:
        print("\n🎉 OpenAI API key validation PASSED!")
        sys.exit(0)
    else:
        print("\n❌ OpenAI API key validation FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()