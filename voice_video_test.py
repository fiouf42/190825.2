#!/usr/bin/env python3
"""
Voice Generation and Video Assembly Tests for TikTok Video Generator
Tests the new ElevenLabs voice generation and FFmpeg video assembly endpoints
"""

import requests
import json
import time
import sys
import base64
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://0280dc01-f7fd-4b8a-9b53-8b0d086b38ea.preview.emergentagent.com/api"
TIMEOUT = 120  # Extended timeout for video processing

class VoiceVideoTester:
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
    
    def test_available_voices(self) -> Dict[str, Any]:
        """Test ElevenLabs voice fetching - find Nicolas or French male voice"""
        try:
            print("Testing ElevenLabs voice fetching...")
            response = self.session.get(f"{self.base_url}/voices/available", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                voices = data.get("voices", [])
                
                if not voices:
                    self.log_test("Available Voices - Data", False, "No voices returned")
                    return {}
                
                # Look for Nicolas voice or French male voices
                nicolas_voice = None
                french_voices = []
                
                for voice in voices:
                    voice_name = voice.get("name", "").lower()
                    if "nicolas" in voice_name:
                        nicolas_voice = voice
                    elif "french" in voice_name or "français" in voice_name:
                        french_voices.append(voice)
                
                if nicolas_voice:
                    self.log_test("Available Voices - Nicolas Found", True, f"Found Nicolas voice: {nicolas_voice['voice_id']}")
                elif french_voices:
                    self.log_test("Available Voices - French Voices", True, f"Found {len(french_voices)} French voices")
                else:
                    self.log_test("Available Voices - French/Nicolas", False, "No Nicolas or French voices found")
                
                self.log_test("Available Voices", True, f"Retrieved {len(voices)} voices from ElevenLabs")
                
                # Print some voice details for debugging
                print(f"   Total voices available: {len(voices)}")
                if nicolas_voice:
                    print(f"   Nicolas voice ID: {nicolas_voice['voice_id']}")
                if french_voices:
                    print(f"   French voices: {[v['name'] for v in french_voices[:3]]}")
                
                return data
            else:
                self.log_test("Available Voices", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Available Voices", False, f"Error: {str(e)}")
            return {}
    
    def test_generate_voice(self, script_id: str) -> Dict[str, Any]:
        """Test voice generation from existing script"""
        try:
            print(f"Testing voice generation for script ID: {script_id}")
            response = self.session.post(
                f"{self.base_url}/generate-voice",
                params={"script_id": script_id},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["audio_id", "script_id", "voice_id", "duration", "audio_base64"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Voice Generation - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate audio data
                audio_base64 = data.get("audio_base64", "")
                if len(audio_base64) < 1000:  # Audio should be substantial
                    self.log_test("Voice Generation - Audio Data", False, f"Audio data too short: {len(audio_base64)} chars")
                    return {}
                
                # Validate base64 format
                try:
                    base64.b64decode(audio_base64)
                    self.log_test("Voice Generation - Base64 Valid", True, "Audio base64 is valid")
                except Exception:
                    self.log_test("Voice Generation - Base64 Valid", False, "Invalid base64 audio data")
                    return {}
                
                duration = data.get("duration", 0)
                if duration <= 0:
                    self.log_test("Voice Generation - Duration", False, f"Invalid duration: {duration}")
                    return {}
                
                self.log_test("Voice Generation", True, f"Generated {duration:.1f}s audio ({len(audio_base64)} chars base64)")
                print(f"   Voice ID used: {data.get('voice_id')}")
                print(f"   Audio duration: {duration:.1f} seconds")
                
                return data
            else:
                self.log_test("Voice Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Voice Generation", False, f"Error: {str(e)}")
            return {}
    
    def test_assemble_video(self, project_id: str) -> Dict[str, Any]:
        """Test video assembly with images, voice, and subtitles"""
        try:
            print(f"Testing video assembly for project ID: {project_id}")
            response = self.session.post(
                f"{self.base_url}/assemble-video",
                params={"project_id": project_id},
                timeout=TIMEOUT * 2  # Video assembly takes longer
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["video_id", "project_id", "duration", "resolution", "video_base64"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Video Assembly - Structure", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Validate video data
                video_base64 = data.get("video_base64", "")
                if len(video_base64) < 10000:  # Video should be substantial
                    self.log_test("Video Assembly - Video Data", False, f"Video data too short: {len(video_base64)} chars")
                    return {}
                
                # Validate base64 format
                try:
                    base64.b64decode(video_base64)
                    self.log_test("Video Assembly - Base64 Valid", True, "Video base64 is valid")
                except Exception:
                    self.log_test("Video Assembly - Base64 Valid", False, "Invalid base64 video data")
                    return {}
                
                # Validate resolution (should be TikTok format)
                resolution = data.get("resolution", "")
                if resolution != "1080x1920":
                    self.log_test("Video Assembly - Resolution", False, f"Wrong resolution: {resolution}, expected 1080x1920")
                else:
                    self.log_test("Video Assembly - Resolution", True, "Correct TikTok resolution (1080x1920)")
                
                duration = data.get("duration", 0)
                if duration <= 0:
                    self.log_test("Video Assembly - Duration", False, f"Invalid duration: {duration}")
                    return {}
                
                self.log_test("Video Assembly", True, f"Generated {duration:.1f}s video ({len(video_base64)} chars base64)")
                print(f"   Video duration: {duration:.1f} seconds")
                print(f"   Video resolution: {resolution}")
                print(f"   Video size: {len(video_base64)} base64 characters")
                
                return data
            else:
                self.log_test("Video Assembly", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Video Assembly", False, f"Error: {str(e)}")
            return {}
    
    def test_complete_video_pipeline(self, prompt: str = "conseils productivité étudiants", duration: int = 30) -> Dict[str, Any]:
        """Test complete pipeline from prompt to final video"""
        try:
            payload = {
                "prompt": prompt,
                "duration": duration
            }
            
            print(f"Testing complete video pipeline with prompt: '{prompt}' ({duration}s)")
            print("This will test: script generation -> image generation -> voice generation -> video assembly")
            
            response = self.session.post(
                f"{self.base_url}/create-complete-video",
                json=payload,
                timeout=TIMEOUT * 3  # Complete pipeline takes longest
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
                
                # Validate script
                script = data.get("script", {})
                if not script.get("script_text") or len(script.get("scenes", [])) == 0:
                    self.log_test("Complete Pipeline - Script", False, "Invalid script data")
                    return {}
                
                # Validate images
                images = data.get("images", [])
                if len(images) == 0:
                    self.log_test("Complete Pipeline - Images", False, "No images generated")
                    return {}
                
                # Validate audio
                audio = data.get("audio", {})
                if not audio.get("audio_id") or audio.get("duration", 0) <= 0:
                    self.log_test("Complete Pipeline - Audio", False, "Invalid audio data")
                    return {}
                
                # Validate video
                video = data.get("video", {})
                if not video.get("video_base64") or video.get("duration", 0) <= 0:
                    self.log_test("Complete Pipeline - Video", False, "Invalid video data")
                    return {}
                
                # Validate video format
                if video.get("resolution") != "1080x1920":
                    self.log_test("Complete Pipeline - Video Format", False, f"Wrong resolution: {video.get('resolution')}")
                else:
                    self.log_test("Complete Pipeline - Video Format", True, "Correct TikTok format")
                
                self.log_test("Complete Pipeline", True, f"Generated complete video with {len(images)} images")
                print(f"   Project ID: {data.get('project_id')}")
                print(f"   Script scenes: {len(script.get('scenes', []))}")
                print(f"   Images generated: {len(images)}")
                print(f"   Audio duration: {audio.get('duration', 0):.1f}s")
                print(f"   Video duration: {video.get('duration', 0):.1f}s")
                print(f"   Video size: {len(video.get('video_base64', ''))} base64 characters")
                
                return data
            else:
                self.log_test("Complete Pipeline", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Complete Pipeline", False, f"Error: {str(e)}")
            return {}
    
    def run_voice_video_tests(self):
        """Run all voice and video tests"""
        print("=" * 70)
        print("TikTok Video Generator - Voice & Video Assembly Tests")
        print("=" * 70)
        print(f"Testing API at: {self.base_url}")
        print()
        
        # Test 1: Available Voices (ElevenLabs integration)
        voices_data = self.test_available_voices()
        if not voices_data:
            print("❌ ElevenLabs voice fetching failed. Continuing with other tests...")
        
        print()
        
        # Test 2: Complete Pipeline (this will create script and images we need)
        pipeline_data = self.test_complete_video_pipeline("conseils productivité étudiants", 30)
        if not pipeline_data:
            print("❌ Complete pipeline failed. Cannot test individual components.")
            return False
        
        print()
        
        # Extract IDs for individual component tests
        script_id = pipeline_data.get("script", {}).get("id")
        project_id = pipeline_data.get("project_id")
        
        # Test 3: Individual Voice Generation (if we have script_id)
        if script_id:
            print("Testing individual voice generation...")
            voice_data = self.test_generate_voice(script_id)
            if not voice_data:
                print("❌ Individual voice generation failed.")
        
        print()
        
        # Test 4: Individual Video Assembly (if we have project_id)
        if project_id:
            print("Testing individual video assembly...")
            # Create a new project for assembly test
            try:
                # First create a simple project
                simple_project_response = self.session.post(
                    f"{self.base_url}/create-video-project",
                    json={"prompt": "test vidéo courte", "duration": 20},
                    timeout=60
                )
                if simple_project_response.status_code == 200:
                    simple_project = simple_project_response.json()
                    assembly_data = self.test_assemble_video(simple_project.get("id"))
                    if not assembly_data:
                        print("❌ Individual video assembly failed.")
                else:
                    print("❌ Could not create test project for assembly test.")
            except Exception as e:
                print(f"❌ Error setting up assembly test: {str(e)}")
        
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 70)
        print("VOICE & VIDEO TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\nFailed Tests:")
            for test in failed_tests:
                print(f"  ❌ {test['test']}: {test['details']}")
        
        if passed_tests == total_tests:
            print("\n🎉 All voice and video tests passed!")
            return True
        else:
            print("\n⚠️  Some tests failed. Check details above.")
            return False

def main():
    """Main test execution"""
    tester = VoiceVideoTester()
    success = tester.run_voice_video_tests()
    
    if success:
        print("\n✅ Voice generation and video assembly are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Voice/video features have issues that need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()