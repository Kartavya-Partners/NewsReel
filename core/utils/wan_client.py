import os
import time
import requests
import json
from typing import Optional, Dict, Any
from loguru import logger

class WanClient:
    """
    Client for interacting with PiAPI (Wan 2.5 Video Generation).
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.piapi.ai/api/v1", model: str = "wan-2.5"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        
    def generate_video(self, prompt: str, aspect_ratio: str = "16:9") -> Optional[str]:
        """
        Generates a video from a prompt. Returns the URL of the generated video or None if failed.
        """
        url = f"{self.base_url}/task"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "task_type": "video_generation",
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio
            }
        }
        
        try:
            logger.info(f"WanClient: Sending generation request for model '{self.model}'...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"WanClient: API Error {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            if data.get("code") != 200:
                logger.error(f"WanClient: API Returned Error: {data.get('message')}")
                return None
                
            task_id = data['data']['task_id']
            logger.info(f"WanClient: Task started (ID: {task_id}). Polling for results...")
            
            return self._poll_task(task_id)
            
        except Exception as e:
            logger.error(f"WanClient: Request Exception: {e}")
            return None

    def _poll_task(self, task_id: str, max_retries: int = 60, interval: int = 5) -> Optional[str]:
        """
        Polls the task status until completion or timeout.
        """
        url = f"{self.base_url}/task/{task_id}"
        headers = {"x-api-key": self.api_key}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('data', {}).get('status')
                    
                    if status == 'completed':
                        output = data['data'].get('output', {})
                        video_url = output.get('video_url') or output.get('url')
                        if video_url:
                            logger.info("WanClient: Generation Successful!")
                            return video_url
                        else:
                            logger.error(f"WanClient: Completed but no URL found: {data}")
                            return None
                            
                    elif status == 'failed':
                        error = data['data'].get('error')
                        logger.error(f"WanClient: Task Failed: {error}")
                        return None
                        
                time.sleep(interval)
                
            except Exception as e:
                logger.warning(f"WanClient: Polling error (attempt {attempt}): {e}")
                time.sleep(interval)
                
        logger.error("WanClient: Polling Timed Out.")
        return None
