#!/usr/bin/env python3
"""
FFmpeg Pipeline Test - Focus on identifying exact FFmpeg errors
Tests the complete video pipeline to identify the specific FFmpeg stream specifier issues
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://content-forge-79.preview.emergentagent.com/api"
TIMEOUT = 120  # Extended timeout for video processing

class FFmpegPipelineTester:
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
        """Test the complete video pipeline to identify FFmpeg issues"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"🎬 Testing COMPLETE VIDEO PIPELINE")
            print(f"   Prompt: '{prompt}' ({duration}s)")
            print(f"   This will test: Script → Images → Voice → FFmpeg Assembly")
            print(f"   Expected: Pipeline should fail at FFmpeg stage with stream specifier errors")
            print()
            
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT * 2  # Extended timeout for complete pipeline
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["project_id", "script", "images", "audio", "video", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Complete Pipeline - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # If we get here, the pipeline actually succeeded!
                self.log_test("Complete Video Pipeline", True, "🎉 UNEXPECTED SUCCESS - Pipeline completed without FFmpeg errors!")
                
                # Validate each component
                script = data.get("script", {})
                images = data.get("images", [])
                audio = data.get("audio", {})
                video = data.get("video", {})
                
                print(f"   ✅ Script: {len(script.get('script_text', ''))} chars, {len(script.get('scenes', []))} scenes")
                print(f"   ✅ Images: {len(images)} images generated")
                print(f"   ✅ Audio: {audio.get('duration', 0)}s duration")
                print(f"   ✅ Video: {len(video.get('video_base64', ''))} chars base64")
                
                return data
            else:
                # This is where we expect to capture the FFmpeg error
                error_text = response.text
                print(f"📋 Full Error Response:")
                print(f"   {error_text}")
                print()
                
                # Try to parse JSON error for more details
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "No detail provided")
                    print(f"🔍 Parsed Error Detail:")
                    print(f"   {error_detail}")
                    
                    # Check if this is the expected FFmpeg error
                    if "ffmpeg" in error_detail.lower() or "stream" in error_detail.lower():
                        self.log_test("Complete Pipeline - FFmpeg Error Captured", True, f"FFmpeg error identified: {error_detail}")
                        return {"error_type": "ffmpeg", "error_detail": error_detail, "full_response": error_text}
                    else:
                        self.log_test("Complete Pipeline - Unexpected Error", False, f"Non-FFmpeg error: {error_detail}")
                        return {"error_type": "other", "error_detail": error_detail, "full_response": error_text}
                        
                except json.JSONDecodeError:
                    # Raw text error
                    if "ffmpeg" in error_text.lower() or "stream" in error_text.lower():
                        self.log_test("Complete Pipeline - FFmpeg Error Captured", True, f"FFmpeg error in raw response: {error_text[:200]}...")
                        return {"error_type": "ffmpeg", "error_detail": error_text, "full_response": error_text}
                    else:
                        self.log_test("Complete Pipeline - Raw Error", False, f"Raw error response: {error_text[:200]}...")
                        return {"error_type": "raw", "error_detail": error_text, "full_response": error_text}
                
        except Exception as e:
            self.log_test("Complete Video Pipeline", False, f"Exception: {str(e)}")
            return {"error_type": "exception", "error_detail": str(e)}
    
    def test_individual_components(self) -> Dict[str, Any]:
        """Test individual pipeline components to isolate the issue"""
        print(f"🔧 Testing INDIVIDUAL COMPONENTS")
        print(f"   This will test each step separately to confirm where the pipeline breaks")
        print()
        
        results = {}
        
        # Step 1: Script Generation
        print("1️⃣ Testing Script Generation...")
        try:
            script_payload = {"prompt": "astuces productivité étudiants", "duration": 30}
            response = self.session.post(f"{self.base_url}/generate-script", json=script_payload, timeout=60)
            
            if response.status_code == 200:
                script_data = response.json()
                script_id = script_data.get("id")
                self.log_test("Individual - Script Generation", True, f"Script ID: {script_id}")
                results["script"] = {"success": True, "data": script_data, "script_id": script_id}
                print(f"   ✅ Script generated: {len(script_data.get('script_text', ''))} chars")
            else:
                self.log_test("Individual - Script Generation", False, f"Status: {response.status_code}")
                results["script"] = {"success": False, "error": response.text}
                return results
        except Exception as e:
            self.log_test("Individual - Script Generation", False, f"Exception: {str(e)}")
            results["script"] = {"success": False, "error": str(e)}
            return results
        
        # Step 2: Image Generation
        print("\n2️⃣ Testing Image Generation...")
        try:
            script_id = results["script"]["script_id"]
            response = self.session.post(f"{self.base_url}/generate-images", params={"script_id": script_id}, timeout=60)
            
            if response.status_code == 200:
                images_data = response.json()
                images_count = images_data.get("total_generated", 0)
                self.log_test("Individual - Image Generation", True, f"Images: {images_count}")
                results["images"] = {"success": True, "data": images_data}
                print(f"   ✅ Images generated: {images_count} images")
            else:
                self.log_test("Individual - Image Generation", False, f"Status: {response.status_code}")
                results["images"] = {"success": False, "error": response.text}
                return results
        except Exception as e:
            self.log_test("Individual - Image Generation", False, f"Exception: {str(e)}")
            results["images"] = {"success": False, "error": str(e)}
            return results
        
        # Step 3: Voice Generation
        print("\n3️⃣ Testing Voice Generation...")
        try:
            script_id = results["script"]["script_id"]
            response = self.session.post(f"{self.base_url}/generate-voice", params={"script_id": script_id}, timeout=60)
            
            if response.status_code == 200:
                voice_data = response.json()
                duration = voice_data.get("duration", 0)
                self.log_test("Individual - Voice Generation", True, f"Duration: {duration}s")
                results["voice"] = {"success": True, "data": voice_data}
                print(f"   ✅ Voice generated: {duration}s duration")
            else:
                self.log_test("Individual - Voice Generation", False, f"Status: {response.status_code}")
                results["voice"] = {"success": False, "error": response.text}
                return results
        except Exception as e:
            self.log_test("Individual - Voice Generation", False, f"Exception: {str(e)}")
            results["voice"] = {"success": False, "error": str(e)}
            return results
        
        # Step 4: Create Project (to get project_id for video assembly)
        print("\n4️⃣ Creating Project for Video Assembly...")
        try:
            project_payload = {"prompt": "astuces productivité étudiants", "duration": 30}
            response = self.session.post(f"{self.base_url}/create-video-project", json=project_payload, timeout=120)
            
            if response.status_code == 200:
                project_data = response.json()
                project_id = project_data.get("id")
                self.log_test("Individual - Project Creation", True, f"Project ID: {project_id}")
                results["project"] = {"success": True, "data": project_data, "project_id": project_id}
                print(f"   ✅ Project created: {project_id}")
            else:
                self.log_test("Individual - Project Creation", False, f"Status: {response.status_code}")
                results["project"] = {"success": False, "error": response.text}
                return results
        except Exception as e:
            self.log_test("Individual - Project Creation", False, f"Exception: {str(e)}")
            results["project"] = {"success": False, "error": str(e)}
            return results
        
        # Step 5: Video Assembly (This is where we expect the FFmpeg error)
        print("\n5️⃣ Testing Video Assembly (FFmpeg) - EXPECTED TO FAIL...")
        try:
            project_id = results["project"]["project_id"]
            response = self.session.post(f"{self.base_url}/assemble-video", params={"project_id": project_id}, timeout=120)
            
            if response.status_code == 200:
                video_data = response.json()
                video_size = len(video_data.get("video_base64", ""))
                self.log_test("Individual - Video Assembly", True, f"🎉 UNEXPECTED SUCCESS - Video size: {video_size} chars")
                results["video_assembly"] = {"success": True, "data": video_data}
                print(f"   ✅ Video assembled successfully: {video_size} chars")
            else:
                # This is where we expect the FFmpeg error
                error_text = response.text
                print(f"   📋 FFmpeg Error Response:")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {error_text}")
                
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "No detail provided")
                    print(f"   🔍 Detailed Error: {error_detail}")
                    
                    if "ffmpeg" in error_detail.lower() or "stream" in error_detail.lower():
                        self.log_test("Individual - Video Assembly FFmpeg Error", True, f"FFmpeg error captured: {error_detail}")
                        results["video_assembly"] = {"success": False, "error_type": "ffmpeg", "error": error_detail}
                    else:
                        self.log_test("Individual - Video Assembly Other Error", False, f"Non-FFmpeg error: {error_detail}")
                        results["video_assembly"] = {"success": False, "error_type": "other", "error": error_detail}
                        
                except json.JSONDecodeError:
                    if "ffmpeg" in error_text.lower() or "stream" in error_text.lower():
                        self.log_test("Individual - Video Assembly FFmpeg Error", True, f"FFmpeg error in raw response")
                        results["video_assembly"] = {"success": False, "error_type": "ffmpeg", "error": error_text}
                    else:
                        self.log_test("Individual - Video Assembly Raw Error", False, f"Raw error response")
                        results["video_assembly"] = {"success": False, "error_type": "raw", "error": error_text}
                        
        except Exception as e:
            self.log_test("Individual - Video Assembly", False, f"Exception: {str(e)}")
            results["video_assembly"] = {"success": False, "error_type": "exception", "error": str(e)}
        
        return results
    
    def run_ffmpeg_focused_test(self):
        """Run focused tests to identify FFmpeg issues"""
        print("=" * 80)
        print("🎬 FFMPEG PIPELINE DIAGNOSTIC TEST")
        print("=" * 80)
        print(f"Testing API at: {self.base_url}")
        print(f"Focus: Identify exact FFmpeg stream specifier errors")
        print(f"Expected: Pipeline should work until FFmpeg video assembly")
        print()
        
        # Test 1: Complete Pipeline (expected to fail at FFmpeg)
        print("🎯 PRIMARY TEST: Complete Video Pipeline")
        print("   This should fail at FFmpeg stage with stream specifier errors")
        print()
        
        complete_result = self.test_complete_video_pipeline()
        
        print("\n" + "="*60)
        
        # Test 2: Individual Components (to isolate the exact failure point)
        print("🔍 DIAGNOSTIC TEST: Individual Components")
        print("   This will test each step to confirm where exactly it breaks")
        print()
        
        individual_results = self.test_individual_components()
        
        # Analysis
        print("\n" + "="*80)
        print("📊 FFMPEG DIAGNOSTIC ANALYSIS")
        print("="*80)
        
        if complete_result.get("error_type") == "ffmpeg":
            print("✅ FFMPEG ERROR SUCCESSFULLY IDENTIFIED:")
            print(f"   Error Type: FFmpeg stream specifier issue")
            print(f"   Error Detail: {complete_result.get('error_detail', 'No detail')}")
            print()
            print("🔧 RECOMMENDED ACTIONS:")
            print("   1. Check FFmpeg filter_complex syntax")
            print("   2. Verify stream specifier format ([0:v], [1:a], etc.)")
            print("   3. Review xfade transition parameters")
            print("   4. Check subtitle overlay syntax")
            
        elif individual_results.get("video_assembly", {}).get("error_type") == "ffmpeg":
            print("✅ FFMPEG ERROR IDENTIFIED IN INDIVIDUAL TEST:")
            error_detail = individual_results["video_assembly"].get("error", "No detail")
            print(f"   Error Detail: {error_detail}")
            print()
            print("🔧 PIPELINE STATUS:")
            print(f"   ✅ Script Generation: {individual_results.get('script', {}).get('success', False)}")
            print(f"   ✅ Image Generation: {individual_results.get('images', {}).get('success', False)}")
            print(f"   ✅ Voice Generation: {individual_results.get('voice', {}).get('success', False)}")
            print(f"   ✅ Project Creation: {individual_results.get('project', {}).get('success', False)}")
            print(f"   ❌ Video Assembly: FFmpeg Error")
            
        else:
            print("⚠️  UNEXPECTED RESULT:")
            if complete_result and not complete_result.get("error_type"):
                print("   Complete pipeline succeeded - FFmpeg issue may be resolved!")
            else:
                print("   Error is not FFmpeg-related or pipeline failed earlier")
                print(f"   Complete pipeline error: {complete_result.get('error_type', 'unknown')}")
                if individual_results:
                    for step, result in individual_results.items():
                        success = result.get("success", False)
                        status = "✅" if success else "❌"
                        print(f"   {status} {step.title()}: {success}")
        
        print("\n" + "="*80)
        
        # Return summary for test_result.md update
        return {
            "complete_pipeline": complete_result,
            "individual_components": individual_results,
            "ffmpeg_error_identified": (
                complete_result.get("error_type") == "ffmpeg" or 
                individual_results.get("video_assembly", {}).get("error_type") == "ffmpeg"
            )
        }

def main():
    """Main test execution"""
    tester = FFmpegPipelineTester()
    results = tester.run_ffmpeg_focused_test()
    
    if results.get("ffmpeg_error_identified"):
        print("\n✅ FFmpeg error successfully identified and captured!")
        print("   Main agent can now use this information to fix the video assembly.")
        sys.exit(0)
    else:
        print("\n⚠️  FFmpeg error not identified as expected.")
        print("   Either the issue is resolved or there's a different problem.")
        sys.exit(1)

if __name__ == "__main__":
    main()