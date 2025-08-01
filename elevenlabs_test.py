#!/usr/bin/env python3
"""
ElevenLabs Voice Integration Test
Tests only the voice-related endpoints that don't depend on OpenAI
"""

import requests
import json
import sys
import base64
from typing import Dict, Any

# Configuration
BACKEND_URL = "https://eec84c22-7013-42be-90c3-11e7daa1d495.preview.emergentagent.com/api"

class ElevenLabsVoiceTester:
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
        """Test ElevenLabs voice fetching - find Nicolas voice or French male voice"""
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
                male_voices = []
                
                print(f"   Available voices ({len(voices)} total):")
                for voice in voices:
                    voice_name = voice.get("name", "").lower()
                    voice_id = voice.get("voice_id", "")
                    category = voice.get("category", "")
                    
                    print(f"     - {voice.get('name')} (ID: {voice_id[:8]}..., Category: {category})")
                    
                    if "nicolas" in voice_name:
                        nicolas_voice = voice
                    elif "french" in voice_name or "français" in voice_name:
                        french_voices.append(voice)
                    elif "male" in voice_name.lower() or "man" in voice_name.lower():
                        male_voices.append(voice)
                
                if nicolas_voice:
                    self.log_test("Available Voices - Nicolas Found", True, f"Found Nicolas voice: {nicolas_voice['voice_id']}")
                    print(f"   ✅ Nicolas voice found: {nicolas_voice['name']} ({nicolas_voice['voice_id']})")
                elif french_voices:
                    self.log_test("Available Voices - French Voices", True, f"Found {len(french_voices)} French voices")
                    print(f"   ✅ French voices found: {[v['name'] for v in french_voices]}")
                elif male_voices:
                    self.log_test("Available Voices - Male Voices", True, f"Found {len(male_voices)} male voices")
                    print(f"   ✅ Male voices found: {[v['name'] for v in male_voices[:3]]}")
                else:
                    self.log_test("Available Voices - Suitable Voices", False, "No Nicolas, French, or male voices found")
                
                self.log_test("Available Voices", True, f"Retrieved {len(voices)} voices from ElevenLabs")
                
                return data
            else:
                self.log_test("Available Voices", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Available Voices", False, f"Error: {str(e)}")
            return {}
    
    def create_mock_script(self) -> str:
        """Create a mock script in the database for testing voice generation"""
        try:
            # We'll directly insert a mock script into the database
            import pymongo
            from datetime import datetime
            import uuid
            
            # Connect to MongoDB
            client = pymongo.MongoClient("mongodb://localhost:27017")
            db = client["test_database"]
            
            # Create mock script
            mock_script = {
                "id": str(uuid.uuid4()),
                "prompt": "test voice generation",
                "duration": 30,
                "script_text": "Bonjour et bienvenue dans cette vidéo sur la productivité étudiante. Aujourd'hui, nous allons découvrir des conseils pratiques pour améliorer votre organisation et réussir vos études. Ces techniques simples peuvent transformer votre façon de travailler.",
                "scenes": [
                    "Introduction à la productivité étudiante",
                    "Conseils d'organisation pratiques", 
                    "Techniques de travail efficaces"
                ],
                "created_at": datetime.utcnow()
            }
            
            # Insert into database
            db.scripts.insert_one(mock_script)
            print(f"   Created mock script with ID: {mock_script['id']}")
            
            return mock_script["id"]
            
        except Exception as e:
            print(f"   Error creating mock script: {str(e)}")
            return None
    
    def test_generate_voice_with_mock_script(self) -> Dict[str, Any]:
        """Test voice generation using a mock script"""
        try:
            # Create mock script
            script_id = self.create_mock_script()
            if not script_id:
                self.log_test("Voice Generation - Mock Script", False, "Could not create mock script")
                return {}
            
            print(f"Testing voice generation with mock script ID: {script_id}")
            response = self.session.post(
                f"{self.base_url}/generate-voice",
                params={"script_id": script_id},
                timeout=60
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
                    audio_bytes = base64.b64decode(audio_base64)
                    self.log_test("Voice Generation - Base64 Valid", True, f"Audio base64 is valid ({len(audio_bytes)} bytes)")
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
                print(f"   Audio size: {len(audio_bytes)} bytes")
                
                return data
            else:
                self.log_test("Voice Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("Voice Generation", False, f"Error: {str(e)}")
            return {}
    
    def run_elevenlabs_tests(self):
        """Run ElevenLabs-specific tests"""
        print("=" * 70)
        print("ElevenLabs Voice Integration Tests")
        print("=" * 70)
        print(f"Testing API at: {self.base_url}")
        print("Note: Testing only voice features due to OpenAI API key issues")
        print()
        
        # Test 1: Available Voices
        voices_data = self.test_available_voices()
        if not voices_data:
            print("❌ ElevenLabs voice fetching failed.")
            return False
        
        print()
        
        # Test 2: Voice Generation with Mock Script
        voice_data = self.test_generate_voice_with_mock_script()
        if not voice_data:
            print("❌ Voice generation failed.")
        
        print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("=" * 70)
        print("ELEVENLABS VOICE TEST SUMMARY")
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
            print("\n🎉 All ElevenLabs voice tests passed!")
            return True
        else:
            print("\n⚠️  Some voice tests failed. Check details above.")
            return False

def main():
    """Main test execution"""
    tester = ElevenLabsVoiceTester()
    success = tester.run_elevenlabs_tests()
    
    if success:
        print("\n✅ ElevenLabs voice integration is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ ElevenLabs voice integration has issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()