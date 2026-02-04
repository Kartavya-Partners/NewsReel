import os
import time
import requests
import json
from typing import Optional, Dict, Any
from loguru import logger

class WanClient:
    """
    Client for interacting with PiAPI (Wan Video Generation) or Local Wan 2.2 Models.
    """
    
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.piapi.ai/api/v1", model: str = "wan-2.2", mode: str = "api", local_paths: Dict[str, str] = None, gcp_config: Dict[str, str] = None):
        """
        Args:
            api_key: API Key for PiAPI
            base_url: Base URL for PiAPI
            model: Model name
            mode: 'api', 'local', or 'gcp'
            local_paths: Dictionary with 'repo' and 'checkpoint' paths for local mode
            gcp_config: Dictionary with 'project_id', 'zone', 'instance_name', 'bucket_name' for GCP mode
        """
        self.mode = mode
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.gcp_config = gcp_config or {}
        
        self.local_pipeline = None
        if self.mode == "local":
            self._setup_local_model(local_paths)

    def _setup_local_model(self, paths: Dict[str, str]):
        """Sets up the local Wan 2.2 model."""
        import sys
        
        if paths is None:
            paths = {}
        
        repo_path = paths.get('repo', "../Wan-Video")
        # Default to Wan 2.2 A14B INT8 Quantized as per architecture plan
        # "Sweet Spot" Configuration
        ckpt_path = paths.get('checkpoint', "./weights/Wan2.2-I2V-14B-720P-INT8")
        
        # Ensure defaults are stored back so they are available to _generate_via_local
        paths['repo'] = repo_path
        paths['checkpoint'] = ckpt_path
        
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
            
            # Based on Wan 2.2 Github (MoE architecture):
            # import wan
            # from wan.configs import WAN_CONFIGS
            
            logger.info("WanClient: Importing local Wan module...")
            import torch
            from wan.configs import WAN_CONFIGS
            from wan.utils.utils import cache_fake_news_token, str2bool
            
            # Determine config based on model name or default
            # User specified Wan 2.2 A14B INT8 Quantized as the "sweet spot"
            # Wan 2.2 is a distinct architecture (MoE)
            cfg_name = 'Wan2.2-I2V-14B-720P' 
            if 't2v' in self.model.lower():
                 cfg_name = 'Wan2.2-T2V-14B'
            
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
        elif self.mode == "gcp":
            return self._generate_via_gcp(prompt, aspect_ratio)
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
        # Default to i2v-14B as per Wan 2.2 sweet spot
        task_arg = "i2v-14B" 
        if "t2v" in self.model.lower():
            task_arg = "t2v-14B"
            
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

    def _generate_via_gcp(self, prompt: str, aspect_ratio: str) -> Optional[str]:
        """
        Orchestrates generation via GCP Compute Engine:
        1. Start VM
        2. Run generation script via SSH
        3. Upload output to GCS
        4. Stop VM
        5. Download output locally
        """
        import subprocess
        import uuid
        
        project = self.gcp_config.get('project_id')
        zone = self.gcp_config.get('zone')
        instance = self.gcp_config.get('instance_name')
        bucket = self.gcp_config.get('bucket_name')
        
        if not all([project, zone, instance, bucket]):
            logger.error("WanClient: Missing GCP configuration (project, zone, instance, or bucket).")
            return None

        logger.info(f"WanClient: Starting logic for GCP Instance '{instance}' in '{zone}'...")

        def run_gcloud(cmd_list, timeout=300):
            """Helper to run gcloud commands"""
            try:
                # Add non-interactive flags where possible
                full_cmd = ["gcloud"] + cmd_list
                logger.info(f"WanClient GCP: Running '{' '.join(full_cmd)}'")
                
                # Check for 'ssh' in command to allow larger timeout or specific handling if needed
                if "ssh" in cmd_list:
                    # SSH commands might take longer if they are running generation
                    pass
                
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True if os.name == 'nt' else False # Windows compatibility
                )
                if result.returncode != 0:
                     logger.error(f"WanClient GCP: {full_cmd} failed: {result.stderr}")
                     raise Exception(f"Command failed: {result.stderr}")
                return result.stdout.strip()
            except Exception as e:
                raise e

        try:
            # 1. Start VM
            logger.info("WanClient GCP: Starting VM...")
            run_gcloud(["compute", "instances", "start", instance, "--zone", zone, "--project", project])
            
            # Wait for SSH availability (simple retry loop)
            logger.info("WanClient GCP: Waiting for SSH connectivity...")
            time.sleep(15) # Give it a moment to boot
            
            # 2. Prepare Remote Command
            # Assuming VM has /wan-project setup as per architecture
            # generate.py args need to match what is on the VM. 
            # We assume a wrapper script or direct python call.
            
            remote_filename = f"wan_out_{uuid.uuid4().hex[:6]}.mp4"
            remote_output_path = f"/wan-project/outputs/{remote_filename}"
            
            # Note: We need to escape quotes for the shell
            safe_prompt = prompt.replace("'", "'\\''") 
            
            # Check prompt length / complexity?
            
            # Command to run on VM:
            # cd /wan-project && python generate.py --prompt "..." --output "..." && gsutil cp "..." gs://bucket/
            
            # We use ' && ' to chain commands so failure stops the chain (but we handle stop in finally)
            
            # Task arg alignment
            task_arg = "t2v-14B"
            res_arg = "1280*720"
            
            # Using specific paths assumed in "Steps 8: Folder Structure"
            # /wan-project/generate.py
            # models in /wan-project/models
            
            # Construct the remote python command string
            # We use 'source /opt/deeplearning/env/bin/activate' or similar if needed?
            # Deep Learning VM usually has conda or default python ready. 
            # We assume 'python3' is on path.
            
            python_cmd = (
                f"cd /wan-project && "
                f"python3 generate.py "
                f"--task {task_arg} "
                f"--size {res_arg} "
                f"--prompt '{safe_prompt}' "
                f"--save_file {remote_output_path}"
            )
            
            upload_cmd = f"gsutil cp {remote_output_path} gs://{bucket}/{remote_filename}"
            
            full_remote_cmd = f"{python_cmd} && {upload_cmd}"
            
            logger.info(f"WanClient GCP: executing remote generation: {full_remote_cmd}")
            
            # Execute via SSH
            # We use --command flag for non-interactive execution
            run_gcloud([
                "compute", "ssh", instance, 
                "--zone", zone, 
                "--project", project, 
                "--command", full_remote_cmd
            ], timeout=1200) # 20 mins timeout for generation
            
            # 3. Download from GCS to local
            logger.info(f"WanClient GCP: Downloading result from gs://{bucket}/{remote_filename}...")
            
            local_output_dir = os.path.abspath("output/videos")
            os.makedirs(local_output_dir, exist_ok=True)
            local_file_path = os.path.join(local_output_dir, remote_filename)
            
            # Use gcloud storage or gsutil locally
            run_gcloud(["storage", "cp", f"gs://{bucket}/{remote_filename}", local_file_path])
            
            if os.path.exists(local_file_path):
                logger.success(f"WanClient GCP: Video downloaded to {local_file_path}")
                return local_file_path
            else:
                logger.error("WanClient GCP: Download appeared to succeed but file not found.")
                return None

        except Exception as e:
            logger.error(f"WanClient GCP: Error during execution: {e}")
            return None
            
        finally:
            # 4. ALWAYS Stop VM
            logger.info("WanClient GCP: Stopping VM to save costs...")
            try:
                run_gcloud(["compute", "instances", "stop", instance, "--zone", zone, "--project", project])
                logger.info("WanClient GCP: VM stop request sent.")
            except Exception as e:
                logger.critical(f"WanClient GCP: FAILED TO STOP VM! PLEASE STOP MANUALLY: {e}")


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
