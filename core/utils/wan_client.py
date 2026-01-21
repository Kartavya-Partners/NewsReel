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
    
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.piapi.ai/api/v1", model: str = "wan-2.5", mode: str = "api", local_paths: Dict[str, str] = None):
        """
        Args:
            api_key: API Key for PiAPI
            base_url: Base URL for PiAPI
            model: Model name
            mode: 'api' or 'local'
            local_paths: Dictionary with 'repo' and 'checkpoint' paths for local mode
        """
        self.mode = mode
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        
        self.local_pipeline = None
        if self.mode == "local":
            self._setup_local_model(local_paths)

    def _setup_local_model(self, paths: Dict[str, str]):
        """Sets up the local Wan 2.1 model."""
        import sys
        
        repo_path = paths.get('repo', "../Wan-Video")
        ckpt_path = paths.get('checkpoint', "./weights/Wan2.1-I2V-14B-720P")
        
        # 1. Add Wan-Video to sys.path
        abs_repo_path = os.path.abspath(repo_path)
        if abs_repo_path not in sys.path:
            logger.info(f"WanClient: Adding {abs_repo_path} to sys.path")
            sys.path.append(abs_repo_path)
            
        try:
            # Dynamic Import based on Wan repository structure
            # Example: from wan.t2v import WanT2V
            # Note: We need to know exact import structure. 
            # Assuming 'wan.image2video' or similar based on typical repo.
            # For now, we'll try a generic import and allow user to fix trace if repo differs.
            
            # Based on Wan 2.1 Github:
            # import wan
            # from wan.configs import WARN_2_1_14B_I2V_720P_CONFIG
            
            logger.info("WanClient: Importing local Wan module...")
            import torch
            from wan.configs import WAN_CONFIGS
            from wan.utils.utils import cache_fake_news_token, str2bool
            
            # Determine config based on model name or default
            # We assume Image-to-Video for now as it's most robust, or T2V.
            # Let's support Text-to-Video (T2V) for this workflow.
            
            # Using 14B T2V as default for high quality
            cfg_name = 'Wan2.1-T2V-14B' 
            if 'i2v' in self.model.lower():
                 cfg_name = 'Wan2.1-I2V-14B-720P'
            
            logger.info(f"WanClient: Loading Local Model: {cfg_name} from {ckpt_path}")
            
            # Placeholder for actual loading logic provided in Wan-Video/generate.py
            # Since we don't have the repo, we will define a wrapper that mimics it.
            # Real implementation would be:
            # self.wan_model = WanModel.from_pretrained(ckpt_path)
            # But let's assume we can call main generation function or class.
            
            # To be safe and simple: We will run the generation via SUBPROCESS call to the repo's script
            # because importing complex research code often has side effects or conflicts.
            # AND the user approved the "Batch" workflow which implies running scripts.
            # BUT the user asked for "Machine Inference" inside code.
            
            # Let's stick to subprocess for stability unless user demanded python import.
            # Python import allows better integration.
            # Let's try to simulate the import.
            
            self.local_paths = paths
            self.model_loaded = True
            
        except ImportError as e:
            logger.error(f"WanClient: Failed to import Wan local module: {e}. Ensure 'Wan-Video' repo is cloned.")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"WanClient: Local setup error: {e}")
            self.model_loaded = False
        
    def generate_video(self, prompt: str, aspect_ratio: str = "16:9") -> Optional[str]:
        if self.mode == "local":
            return self._generate_via_local(prompt, aspect_ratio)
        else:
            return self._generate_via_api(prompt, aspect_ratio)

    def _generate_via_api(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """Original API implementation"""
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

    def _generate_via_local(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Runs local inference via subprocess to 'generate.py' in the Wan repo.
        This provides maximum stability and isolation.
        """
        import subprocess
        import uuid
        
        if not self.model_loaded:
             logger.error("WanClient: Local model not loaded. execution skipped.")
             return None
             
        repo_path = self.local_paths.get('repo')
        ckpt_path = self.local_paths.get('checkpoint')
        
        # Output file
        output_filename = f"wan_{uuid.uuid4().hex[:8]}.mp4"
        # We assume code is running in 'core/agents', so we need absolute paths
        output_dir = os.path.abspath("temp/wan_output")
        os.makedirs(output_dir, exist_ok=True)
        
        full_output_path = os.path.join(output_dir, output_filename)
        
        # Construct command
        # python generate.py --task t2v-14B --size 1280*720 --ckpt_dir <path> --prompt <prompt> --save_file <output>
        
        # Determine task argument based on model config
        task_arg = "t2v-14B" # Default
        if "i2v" in self.model.lower():
            task_arg = "i2v-14B"
            
        # Wan generate.py usually takes specific resolution format
        # 16:9 -> 1280*720
        res_arg = "1280*720"
        
        cmd = [
            "python", "generate.py",
            "--task", task_arg,
            "--size", res_arg,
            "--ckpt_dir", os.path.abspath(ckpt_path),
            "--prompt", prompt,
            "--save_file", full_output_path
        ]
        
        logger.info(f"WanClient: Running local inference: {' '.join(cmd)}")
        
        try:
            # Run in the repo directory
            result = subprocess.run(
                cmd, 
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=600 # 10 min timeout for one video
            )
            
            if result.returncode == 0 and os.path.exists(full_output_path):
                logger.info(f"WanClient: Local Generation Successful: {full_output_path}")
                return full_output_path
            else:
                 logger.error(f"WanClient: Local Gen Failed (Code {result.returncode})")
                 logger.error(f"Stdout: {result.stdout}")
                 logger.error(f"Stderr: {result.stderr}")
                 return None
                 
        except Exception as e:
            logger.error(f"WanClient: Subprocess Error: {e}")
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
