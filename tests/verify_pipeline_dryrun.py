import sys
import os
import shutil
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import core modules
sys.path.append(os.getcwd())

def safe_log(msg):
    with open("tests/dryrun_safe_log.txt", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg)

def run_dry_verification():
    safe_log("Starting End-to-End Dry Run Verification...")
    
    try:
        from core.agents.base_agent import AgentState
        from core.agents.visual_asset_agent import VisualAssetAgent
        from core.agents.video_composer_agent import VideoComposerAgent
        from core.agents.animation_generator_agent import AnimationGeneratorAgent
        
        # 1. Setup Environment & Config
        load_dotenv()
        if not os.getenv("PIAPI_API_KEY"):
            safe_log("Error: PIAPI_API_KEY not found. Cannot verify video generation.")
            return

        # Mock State
        safe_log("Injecting Mock State (Skipping LLM costs)...")
        
        mock_state = AgentState(
            topic="Dry Run Test",
            run_id="dry_run_verify"
        )
        
        # Clean prev run
        temp_dir = Path("temp/images/dry_run_verify")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        # Mock Script & Scenes
        mock_state.narration = "This is a dry run test of the video generation system."
        mock_state.scene_plan = [
            {
                "id": 1,
                "narration": "In the futuristic city, technology has evolved beyond imagination.",
                "visual": {
                    "scene_type": "CGI",
                    "image_query": "futuristic cyberpunk city with flying cars, neon lights, 4k, cinematic",
                    "camera_motion": "pan_left",
                    "lower_third_text": "Future City"
                },
                "duration": 5
            },
            {
                "id": 2,
                "narration": "Meanwhile, nature reclaims the old world.",
                "visual": {
                    "scene_type": "REAL_FOOTAGE",
                    "image_query": "abandoned overgrown ruins of a city, nature taking over, photorealistic, 4k",
                    "camera_motion": "zoom_in",
                    "lower_third_text": "Ancient Ruins"
                },
                "duration": 5
            }
        ]
        
        # Mock Audio
        safe_log("Creating Dummy Audio Files...")
        audio_dir = Path("temp/audio/dry_run_verify")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        mock_audio_files = []
        
        # We try to use EdgeTTS but wrap it safely
        try:
            from edge_tts import Communicate
            import asyncio
            
            async def generte_dummy_audio(text, out_path):
                comm = Communicate(text, "en-US-AriaNeural")
                await comm.save(out_path)
                
            for i, scene in enumerate(mock_state.scene_plan):
                p = audio_dir / f"scene_{i}.mp3"
                asyncio.run(generte_dummy_audio(scene['narration'], str(p)))
                mock_audio_files.append(str(p))
                
        except Exception as e:
            safe_log(f"Audio Gen Failed: {e}. Falling back to empty files.")
            for i in range(2):
                p = audio_dir / f"scene_{i}.mp3"
                with open(p, 'wb') as f: f.write(b'\0'*10) # invalid audio but exists
                mock_audio_files.append(str(p))
            
        mock_state.audio_files = mock_audio_files
        safe_log(f"Generated {len(mock_audio_files)} dummy audio files.")

        # 3. Execution: Visual Asset Agent (THE REAL TEST)
        safe_log("Running VisualAssetAgent (This calls PiAPI)...")
        
        import yaml
        with open("core/config/settings.yaml", "r") as f:
            config = yaml.safe_load(f)
            
        visual_agent = VisualAssetAgent(config)
        mock_state = visual_agent.execute(mock_state)

        # Check results
        safe_log("Verifying Assets:")
        for i, scene in enumerate(mock_state.scene_plan):
            asset = scene.get('visual_assets', {})
            path = asset.get('image_path')
            source = asset.get('source')
            safe_log(f"  Scene {i+1}: Source={source}, Path={path}")
            
            if not path or not os.path.exists(path):
                 safe_log(f"  Asset missing for Scene {i+1}")
            else:
                 safe_log(f"  Asset verified.")

        # 4. Execution: Animation & Composer
        safe_log("Running Animation & Composer...")
        
        anim_agent = AnimationGeneratorAgent(config)
        mock_state = anim_agent.execute(mock_state)
        
        composer_agent = VideoComposerAgent(config)
        mock_state = composer_agent.execute(mock_state)
        
        if mock_state.video_path and os.path.exists(mock_state.video_path):
            safe_log(f"DRY RUN SUCCESS! Final Video: {mock_state.video_path}")
        else:
            safe_log("Final Video Generation Failed.")

    except Exception as e:
        safe_log("CRITICAL FAILURE")
        safe_log(traceback.format_exc())

if __name__ == "__main__":
    if Path("tests/dryrun_safe_log.txt").exists():
        os.remove("tests/dryrun_safe_log.txt")
    run_dry_verification()
