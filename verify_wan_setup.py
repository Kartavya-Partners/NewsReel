
import os
import sys
import yaml
from pathlib import Path

# Add core to path
sys.path.append(os.getcwd())

from core.agents.visual_asset_agent import VisualAssetAgent
from core.utils.wan_client import WanClient
from loguru import logger

def test_initialization():
    logger.info("Testing VisualAssetAgent Initialization with Local Wan Config...")
    
    # Load config
    with open("core/config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    # Verify config loaded correctly
    gen_config = config.get("video", {}).get("generation", {})
    logger.info(f"Config Provider: {gen_config.get('provider')}")
    logger.info(f"Config Model: {gen_config.get('model')}")
    
    # Initialize Agent
    try:
        agent = VisualAssetAgent(config)
        logger.info("VisualAssetAgent initialized successfully.")
        
        if agent.wan_client:
            logger.info(f"WanClient initialized in mode: {agent.wan_client.mode}")
            logger.info(f"WanClient model_loaded: {getattr(agent.wan_client, 'model_loaded', 'N/A')}")
            
            if not agent.wan_client.model_loaded:
                logger.info("Expected Result: Model NOT loaded (Repo missing locally). Graceful degradation works.")
            else:
                logger.info("Model unexpectedly loaded? (Did you clone the repo?)")
        else:
            logger.error("WanClient not initialized!")
            
    except Exception as e:
        logger.error(f"Initialization Failed: {e}")
        raise e

if __name__ == "__main__":
    test_initialization()
