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
BACKEND_URL = "https://949daeb1-ac6a-43ae-930f-dc59ba72c7b2.preview.emergentagent.com/api"
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
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("=" * 60)
        print("TikTok Video Generator Backend API Tests")
        print("=" * 60)
        print(f"Testing API at: {self.base_url}")
        print()
        
        # Test 1: API Health
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        print()
        
        # Test 2: Script Generation
        script_data = self.test_generate_script("astuces productivité étudiants", 30)
        if not script_data:
            print("❌ Script generation failed. Stopping tests.")
            return False
        
        print()
        
        # Test 3: Image Generation
        script_id = script_data.get("id")
        if script_id:
            images_data = self.test_generate_images(script_id)
            if not images_data:
                print("❌ Image generation failed.")
        
        print()
        
        # Test 4: Complete Video Project Creation
        project_data = self.test_create_video_project("conseils organisation travail étudiant", 45)
        if not project_data:
            print("❌ Video project creation failed.")
            return False
        
        print()
        
        # Test 5: Project Retrieval
        project_id = project_data.get("id")
        if project_id:
            retrieved_data = self.test_get_project(project_id)
            if not retrieved_data:
                print("❌ Project retrieval failed.")
        
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
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