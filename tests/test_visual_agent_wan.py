import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import shutil

# Mock config
mock_config = {
    "video": {
        "generation": {
            "enable": True,
            "provider": "piapi",
            "model": "wan-2.5",
            "api_key": "test_key"
        }
    },
    "logging": {"level": "DEBUG"},
    "paths": {"temp_dir": "temp_test"}
}

# Import Agent
import sys
import os
sys.path.append(os.getcwd())

from core.agents.visual_asset_agent import VisualAssetAgent
from core.agents.base_agent import AgentState

class TestVisualAssetAgentWan(unittest.TestCase):
    def setUp(self):
        if Path("temp_test").exists():
            shutil.rmtree("temp_test")
        
    def test_initialization(self):
        agent = VisualAssetAgent(mock_config)
        self.assertIsNotNone(agent.wan_client)
        self.assertEqual(agent.wan_client.api_key, "test_key")
        print("Initialization Test Passed")
        
    @patch("core.agents.visual_asset_agent.WanClient") 
    def test_execution_calls_wan(self, MockWanClient):
        # Setup Mock
        mock_client_instance = MockWanClient.return_value
        mock_client_instance.generate_video.return_value = "http://fake.url/video.mp4"
        
        # Inject mock instance into agent (bypassing init creation for control)
        agent = VisualAssetAgent(mock_config)
        agent.wan_client = mock_client_instance 
        agent._fetch_wan_video = MagicMock(return_value=Path("temp_test/images/wan_gen_test.mp4"))
        
        # State
        state = AgentState()
        state.scene_plan = [
            {"visual": {"image_query": "A cat"}, "duration": 5}
        ]
        
        # Execute
        agent.execute(state)
        
        # Assert
        agent._fetch_wan_video.assert_called()
        self.assertIn("wan_gen", str(state.scene_plan[0]["visual_assets"]["image_path"]))
        self.assertEqual(state.scene_plan[0]["visual_assets"]["source"], "generated_wan_video")
        print("Execution & Integration Logic Test Passed")

if __name__ == "__main__":
    unittest.main()
