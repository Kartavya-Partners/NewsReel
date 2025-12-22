"""Test video generation from existing scene plan."""

import json
from pathlib import Path
from agents.base_agent import AgentState
from agents.animation_generator_agent import AnimationGeneratorAgent
from agents.voiceover_agent import VoiceoverAgent
from agents.video_composer_agent import VideoComposerAgent
import yaml
from loguru import logger


def test_video_from_existing_plan():
    """Test video generation using existing result.json."""
    
    # Load configuration
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Load existing scene plan
    result_path = Path('output/result.json')
    
    if not result_path.exists():
        logger.error("No result.json found. Run main.py first to generate scene plan.")
        return False
    
    with open(result_path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    scene_plan = result.get('scene_plan', [])
    
    if not scene_plan:
        logger.error("No scene plan found in result.json")
        return False
    
    logger.info(f"Loaded scene plan with {len(scene_plan)} scenes")
    
    # Create agent state
    state = AgentState(
        topic=result.get('topic', 'Test Topic'),
        scene_plan=scene_plan
    )
    
    try:
        # Test animation generation
        logger.info("Testing AnimationGeneratorAgent...")
        animation_agent = AnimationGeneratorAgent(config)
        state = animation_agent.execute(state)
        logger.success(f"Generated {len(state.scene_clips)} scene clips")
        
        # Test voiceover generation
        logger.info("Testing VoiceoverAgent...")
        voiceover_agent = VoiceoverAgent(config)
        state = voiceover_agent.execute(state)
        logger.success(f"Generated {len(state.audio_files)} audio files")
        
        # Test video composition
        logger.info("Testing VideoComposerAgent...")
        composer_agent = VideoComposerAgent(config)
        state = composer_agent.execute(state)
        logger.success(f"Video saved to: {state.video_path}")
        
        # Verify video exists
        video_path = Path(state.video_path)
        if video_path.exists():
            size_mb = video_path.stat().st_size / (1024 * 1024)
            logger.success(f"✅ Video file created: {video_path.name} ({size_mb:.2f} MB)")
            return True
        else:
            logger.error("Video file was not created")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    logger.info("=" * 60)
    logger.info("Testing Video Generation from Existing Scene Plan")
    logger.info("=" * 60)
    
    success = test_video_from_existing_plan()
    
    if success:
        logger.success("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed")
        sys.exit(1)
