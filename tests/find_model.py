
import requests
import os
import sys

# Load API Key (Hardcoded for test reliability or safely load)
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("PIAPI_API_KEY")

if not API_KEY:
    print("ERROR: No API Key found.")
    sys.exit(1)

BASE_URL = "https://api.piapi.ai/api/v1"

def check_model(model_id):
    url = f"{BASE_URL}/task"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    # Minimal payload
    payload = {
        "model": model_id,
        "task_type": "video_generation",
        "input": {
            "prompt": "test",
            "aspect_ratio": "16:9"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[{model_id}] Status: {response.status_code}")
        if response.status_code == 400:
            print(f"   Msg: {response.json().get('message', '')}")
        elif response.status_code == 200:
            print(f"   SUCCESS! {response.json()}")
            return True
    except Exception as e:
        print(f"   Error: {e}")
    return False

candidates = [
    # Wan 2.1 (The new standard?)
    "wan-2.1-t2v-1.3b",
    "wan-2.1-t2v-14b",
    "wan-2.1-img2vid",
    
    # Official aliases?
    "wan-t2v",
    "wan-i2v",
    
    # Kling (as fallback)
    "kling-v1",
    "kling-v1-standard",
    "kling-v1-pro",
    
    # Older Wan
    "wan-2.0",
    
    # Misc
    "minimax-video-01",
    "hailuo-video-01"
]

print("--- PROBING PIAPI MODELS ---")

# 1. Try to list (Unlikely to work publicly but worth a shot)
# try:
#     resp = requests.get("https://api.piapi.ai/api/v1/models", headers={"x-api-key": API_KEY})
#     print(f"List Models Endpoint: {resp.status_code}")
#     if resp.status_code == 200:
#         print(resp.text)
# except:
#     pass

# 2. Brute force
for m in candidates:
    if check_model(m):
        print(f"\n!!! FOUND VALID MODEL: {m} !!!\n")
        break
