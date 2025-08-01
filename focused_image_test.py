#!/usr/bin/env python3
"""
Focused Backend Tests for Image Generation Fix
Tests the specific OpenAI image generation and complete video pipeline after the base64 fix
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://eec84c22-7013-42be-90c3-11e7daa1d495.preview.emergentagent.com/api"
TIMEOUT = 120  # Extended timeout for image generation

class ImageGenerationTester:
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
    
    def test_generate_script_for_images(self, prompt: str = "techniques de mémorisation efficaces", duration: int = 45) -> Dict[str, Any]:
        """Generate a script to use for image testing"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Generating script for image testing: '{prompt}' ({duration}s)")
            response = self.session.post(
                f"{self.base_url}/generate-script",
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                script_id = data.get("id")
                scenes_count = len(data.get("scenes", []))
                
                self.log_test("Script Generation for Images", True, f"Script ID: {script_id}, Scenes: {scenes_count}")
                return data
            else:
                self.log_test("Script Generation for Images", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Script Generation for Images", False, f"Error: {str(e)}")
            return {}
    
    def test_image_generation_fix(self, script_id: str) -> Dict[str, Any]:
        """Test the fixed OpenAI image generation with base64 handling"""
        try:
            print(f"Testing FIXED image generation for script ID: {script_id}")
            print("   Focus: Base64 data processing fix for OpenAI API responses")
            
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
                    self.log_test("Image Generation Fix - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                images = data.get("images", [])
                total_generated = data.get("total_generated", 0)
                
                if total_generated == 0:
                    self.log_test("Image Generation Fix", False, "No images generated - base64 processing may still be broken")
                    return {}
                
                # Validate each image for the base64 fix
                valid_images = 0
                for i, img in enumerate(images):
                    # Check if base64 data exists and is not None/empty
                    base64_data = img.get("image_base64", "")
                    
                    if not base64_data or base64_data == "None" or len(base64_data) < 100:
                        self.log_test(f"Image {i+1} Base64 Fix", False, f"Base64 data invalid: {len(base64_data) if base64_data else 0} chars")
                        continue
                    
                    # Check for proper base64 format (should start with valid base64 chars)
                    if not base64_data.replace('+', '').replace('/', '').replace('=', '').isalnum():
                        self.log_test(f"Image {i+1} Base64 Format", False, "Base64 data contains invalid characters")
                        continue
                    
                    # Check charcoal style prompt
                    prompt = img.get("prompt", "")
                    charcoal_keywords = ["charbon", "noir", "gris", "blanc", "granuleux", "fusain", "dramatique"]
                    has_charcoal_style = any(keyword in prompt.lower() for keyword in charcoal_keywords)
                    
                    if not has_charcoal_style:
                        self.log_test(f"Image {i+1} Charcoal Style", False, "Missing charcoal style keywords in prompt")
                        continue
                    
                    valid_images += 1
                    self.log_test(f"Image {i+1} Generation Fix", True, f"Valid base64 data ({len(base64_data)} chars)")
                
                if valid_images > 0:
                    self.log_test("Image Generation Fix", True, f"Generated {valid_images}/{total_generated} valid images with proper base64 data")
                    return data
                else:
                    self.log_test("Image Generation Fix", False, "All images failed base64 validation")
                    return {}
            else:
                self.log_test("Image Generation Fix", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Image Generation Fix", False, f"Error: {str(e)}")
            return {}
    
    def test_complete_video_pipeline(self, prompt: str = "techniques de mémorisation efficaces", duration: int = 45) -> Dict[str, Any]:
        """Test the complete video pipeline that should now work with image fix"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Testing COMPLETE VIDEO PIPELINE: '{prompt}' ({duration}s)")
            print("   This should now work since image generation is fixed")
            
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT * 2  # Extended timeout for complete pipeline
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate complete pipeline response
                required_fields = ["project_id", "script", "images", "audio", "video", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Complete Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate each component
                script = data.get("script", {})
                images = data.get("images", [])
                audio = data.get("audio", {})
                video = data.get("video", {})
                status = data.get("status", "")
                
                # Check script component
                if not script or not script.get("script_text"):
                    self.log_test("Complete Pipeline - Script", False, "Script component missing or invalid")
                    return {}
                
                # Check images component (this is the key fix)
                if len(images) == 0:
                    self.log_test("Complete Pipeline - Images", False, "No images generated in pipeline")
                    return {}
                
                # Validate image base64 data in pipeline
                valid_pipeline_images = 0
                for i, img in enumerate(images):
                    base64_data = img.get("image_base64", "")
                    if base64_data and len(base64_data) > 100:
                        valid_pipeline_images += 1
                
                if valid_pipeline_images == 0:
                    self.log_test("Complete Pipeline - Image Data", False, "All images in pipeline have invalid base64 data")
                    return {}
                
                # Check audio component
                if not audio or not audio.get("audio_id"):
                    self.log_test("Complete Pipeline - Audio", False, "Audio component missing or invalid")
                    return {}
                
                # Check video component
                if not video or not video.get("video_base64"):
                    self.log_test("Complete Pipeline - Video", False, "Video component missing or invalid")
                    return {}
                
                # Check final status
                if status != "completed":
                    self.log_test("Complete Pipeline - Status", False, f"Pipeline status not completed: {status}")
                    return {}
                
                self.log_test("Complete Video Pipeline", True, f"Full pipeline completed: script + {len(images)} images + audio + video")
                print(f"   Project ID: {data.get('project_id')}")
                print(f"   Script length: {len(script.get('script_text', ''))} chars")
                print(f"   Images: {valid_pipeline_images} valid images")
                print(f"   Audio duration: {audio.get('duration', 0)}s")
                print(f"   Video size: {len(video.get('video_base64', ''))} chars")
                
                return data
            else:
                self.log_test("Complete Video Pipeline", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Complete Video Pipeline", False, f"Error: {str(e)}")
            return {}
    
    def run_focused_image_tests(self):
        """Run focused tests on image generation fix and complete pipeline"""
        print("=" * 70)
        print("FOCUSED TESTING: IMAGE GENERATION FIX & COMPLETE PIPELINE")
        print("=" * 70)
        print(f"Testing API at: {self.base_url}")
        print("Focus: OpenAI image base64 processing fix")
        print("Priority: Image generation → Complete video pipeline")
        print()
        
        # Test 1: Generate script for testing
        print("📝 Step 1: Generate script for image testing")
        script_data = self.test_generate_script_for_images("techniques de mémorisation efficaces", 45)
        if not script_data:
            print("❌ Cannot proceed without script. Stopping tests.")
            return False
        
        script_id = script_data.get("id")
        print(f"   ✅ Script generated: {script_id}")
        print()
        
        # Test 2: PRIORITY - Test image generation fix
        print("🎯 Step 2: PRIORITY - Test OpenAI image generation fix")
        print("   Testing base64 data processing from OpenAI API")
        image_data = self.test_image_generation_fix(script_id)
        if not image_data:
            print("❌ Image generation still broken. Complete pipeline will fail.")
            print("   The base64 processing fix may not be working correctly.")
            return False
        
        print(f"   ✅ Image generation fixed: {image_data.get('total_generated', 0)} images")
        print()
        
        # Test 3: PRIORITY - Test complete video pipeline
        print("🎯 Step 3: PRIORITY - Test complete video pipeline")
        print("   This should now work since image generation is fixed")
        pipeline_data = self.test_complete_video_pipeline("techniques de mémorisation efficaces", 45)
        if not pipeline_data:
            print("❌ Complete pipeline still failing despite image fix.")
            return False
        
        print("   ✅ Complete video pipeline working!")
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 70)
        print("FOCUSED TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Check critical tests
        image_fix_success = any(
            result["test"] == "Image Generation Fix" and result["success"] 
            for result in self.test_results
        )
        
        pipeline_success = any(
            result["test"] == "Complete Video Pipeline" and result["success"] 
            for result in self.test_results
        )
        
        if image_fix_success and pipeline_success:
            print("🎉 SUCCESS: Image generation fix working + Complete pipeline operational!")
            print("   ✅ OpenAI image base64 processing fixed")
            print("   ✅ Complete video pipeline end-to-end working")
            return True
        elif image_fix_success:
            print("⚠️  PARTIAL SUCCESS: Image generation fixed but pipeline still has issues")
            return False
        else:
            print("❌ FAILURE: Image generation fix not working - pipeline cannot succeed")
            return False

def main():
    """Main test execution focused on image generation fix"""
    print("Starting focused tests for image generation fix...")
    
    tester = ImageGenerationTester()
    success = tester.run_focused_image_tests()
    
    if success:
        print("\n✅ Image generation fix confirmed working! Complete pipeline operational!")
        sys.exit(0)
    else:
        print("\n❌ Image generation fix or complete pipeline still has issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()