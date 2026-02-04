import os
from loguru import logger
from core.utils.wan_client import WanClient

def verify_gcp_wan():
    """
    Manual verification script for GCP WanClient.
    Usage:
    1. Update the GCP_CONFIG dictionary with your actual values.
    2. Run: python verify_gcp_wan.py
    """
    
    # ---------------------------------------------------------
    # CONFIGURATION - PLEASE UPDATE THESE
    # ---------------------------------------------------------
    GCP_CONFIG = {
        "project_id": "your-project-id",    # e.g., "my-news-project"
        "zone": "us-central1-a",            # e.g., "us-central1-a"
        "instance_name": "wan-vm",          # e.g., "wan-gpu-vm"
        "bucket_name": "your-bucket-name"   # e.g., "my-news-videos"
    }
    # ---------------------------------------------------------
    
    logger.info("Starting GCP WanClient Verification...")
    
    client = WanClient(
        mode="gcp",
        gcp_config=GCP_CONFIG,
        model="wan-2.2"
    )
    
    prompt = "A futuristic news anchor desk with a robot reading the news, cyberpunk style, high quality, 4k"
    
    logger.info(f"Test Prompt: {prompt}")
    
    try:
        if GCP_CONFIG["project_id"] == "your-project-id":
            logger.warning("PLEASE UPDATE THE CONFIGURATION IN THIS SCRIPT BEFORE RUNNING!")
            return

        result = client.generate_video(prompt)
        
        if result:
            logger.success(f"Verification Verified! Video saved at: {result}")
        else:
            logger.error("Verification Failed.")
            
    except Exception as e:
        logger.error(f"Verification Error: {e}")

if __name__ == "__main__":
    verify_gcp_wan()
