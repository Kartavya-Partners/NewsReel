import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load env to get key
env_path = Path('.') / '.env'
print(f"Current API Probe working dir: {os.getcwd()}")
print(f"Looking for .env at: {env_path.absolute()} (Exists: {env_path.exists()})")

loaded = load_dotenv(dotenv_path=env_path)
print(f"load_dotenv returned: {loaded}")

API_KEY = os.getenv("PIAPI_API_KEY")

if not API_KEY:
    print("Error: PIAPI_API_KEY not found in os.environ even after load_dotenv.")
    print("Attempting manual parse of .env...")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith("PIAPI_API_KEY"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        API_KEY = parts[1].strip().strip('"').strip("'")
                        print("Manually extracted PIAPI_API_KEY")
                        break
    
    if not API_KEY:
        print("Still failed to find PIAPI_API_KEY.")
        exit(1)

print(f"Found API Key: {API_KEY[:5]}...*****")

# Endpoint for PiAPI
BASE_URL = "https://api.piapi.ai/api/v1"

def create_task():
    url = f"{BASE_URL}/task"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    candidates = [
        "wanx",
        "wan-x",
        "wanx-2.1",
        "wan-2.1-t2v-turbo",
        "wan-2.1-t2v-plus",
        "wan-2.5", 
        "wan-2.5-t2v-turbo",
        "ali-wan-2.5",
        "kling-v1"
    ]
    
    for model_id in candidates:
        # print(f"\nTrying Model ID: {model_id}") # Reduce noise
        
        payload = {
            "model": model_id,
            "task_type": "video_generation", 
            "input": {
                "prompt": "A cinematic drone shot of a futuristic city",
                "aspect_ratio": "16:9"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Clean msg
            msg = "Unknown"
            try:
                data = response.json()
                msg = data.get("message", json.dumps(data))
            except:
                msg = response.text[:100]
                
            print(f"[{model_id}] Status: {response.status_code} | Msg: {msg}")
            
            if response.status_code == 200:
                 return response.json()['data']['task_id']
                 
        except Exception as e:
            print(f"[{model_id}] Failed: {e}")
            
    return None

def check_status(task_id):
    url = f"{BASE_URL}/task/{task_id}"
    headers = {"x-api-key": API_KEY}
    
    print(f"Polling task {task_id}...")
    for _ in range(10): # Wait up to 20s for probe
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data.get('data', {}).get('status')
        print(f"Status: {status}")
        
        if status == 'completed':
            print("Success! Video URL:", data['data']['output']['video_url'])
            return True
        elif status == 'failed':
            print("Task Failed:", data['data'].get('error'))
            return False
            
        time.sleep(2)
        
    print("Timed out waiting for probe.")
    return False

if __name__ == "__main__":
    task_id = create_task()
    if task_id:
        check_status(task_id)
