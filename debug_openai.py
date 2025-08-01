#!/usr/bin/env python3
"""
Debug script to test OpenAI image generation directly
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def test_direct_openai_call():
    """Test direct OpenAI API call to see what's returned"""
    
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": "dall-e-3",
        "prompt": "Style charbon artistique dramatique: techniques de mémorisation. Palette noir, gris, blanc exclusivement.",
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json"
    }
    
    print("Testing direct OpenAI DALL-E 3 API call...")
    print(f"API Key: {OPENAI_API_KEY[:20]}...")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response structure:")
            print(f"  - data: {type(data.get('data', []))}")
            if data.get('data'):
                first_image = data['data'][0]
                print(f"  - first image keys: {list(first_image.keys())}")
                if 'b64_json' in first_image:
                    b64_data = first_image['b64_json']
                    print(f"  - b64_json length: {len(b64_data) if b64_data else 0}")
                    print(f"  - b64_json type: {type(b64_data)}")
                    print(f"  - b64_json preview: {b64_data[:50] if b64_data else 'None'}...")
                    return True
                else:
                    print("  - No b64_json field found")
                    return False
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_direct_openai_call()