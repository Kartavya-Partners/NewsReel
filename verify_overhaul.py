
import os
import shutil
import sys
from pathlib import Path
from agents.visual_planner_agent import VisualPlannerAgent
from agents.visual_asset_agent import VisualAssetAgent
from agents.animation_generator_agent import AnimationGeneratorAgent
from agents.base_agent import AgentState

def verify():
    sys.stdout = open("verify_log.txt", "w", encoding="utf-8")
    sys.stderr = sys.stdout
    
    print("=== Verifying Video Quality Overhaul ===")
    
    try:
        # 1. Setup Dummy State
        config = {
            "llm": {"model": "test"}, 
            "video": {"text_color": "#ffffff"},
            "animation": {"fps": 24, "resolution": "1080p"},
            "paths": {"temp_dir": "temp_verify", "output_dir": "output_verify"}
        }
        
        # Clean temp
        if Path("temp_verify").exists():
            shutil.rmtree("temp_verify")
        Path("temp_verify/images").mkdir(parents=True, exist_ok=True)

        state = AgentState(topic="Delhi Blast Test", raw_articles=[])
        
        # Create a mock scene that needs re-enactment
        mock_scene = {
            "scene_id": "test_001",
            "narration_text": "A massive explosion rocked the Red Fort area, sending shockwaves through the capital.",
            "duration": 5,
            "visual": {
                # This simulates what the new VisualPlanner would output
                "scene_type": "RE_ENACTMENT",
                "image_query": "Hyper-realistic 3D render of car explosion at Red Fort, isometric view, dramatic lighting, smoke, unreal engine 5",
                "visual_style": "3d_render",
                "camera_motion": "zoom_in",
                "lower_third_text": "BLAST AT RED FORT"
            }
        }
        state.scene_plan = [mock_scene]
        
        # 2. Test Visual Asset Agent (Pollinations Integration)
        print("\n--- Testing Visual Asset Agent (Pollinations) ---")
        asset_agent = VisualAssetAgent(config)
        state = asset_agent.execute(state)
        
        img_path = state.scene_plan[0].get("visual_assets", {}).get("image_path")
        print(f"Asset Path: {img_path}")
        
        if not img_path or not Path(img_path).exists():
            print("FAIL: Image not generated")
            # Create dummy image to proceed
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1280, 720), color='red')
            state.scene_plan[0]["visual_assets"] = {"image_path": "temp_verify/images/dummy.jpg"}
            img.save("temp_verify/images/dummy.jpg")
            
        # 3. Test Animation Generator Components
        print("\n--- Testing Animation Generator Components ---")
        anim_agent = AnimationGeneratorAgent(config)
        
        # Test 1: Just Lower Third
        print("Testing Lower Third creation...")
        # UPDATED METHOD NAME
        l3 = anim_agent._create_lower_third("HEADLINE", "TOPIC", 5)
        print(f"Lower Third clips: {[c.size for c in l3]}")
        
        # Try writing just the headline clip
        print("Writing separate headline clip...")
        l3[1].write_videofile("temp_verify/headline.mp4", fps=24, codec="libx264")
        
        # Test 2: Full Scene
        print("Testing Full Scene...")
        state = anim_agent.execute(state)
        
        clip_path = state.scene_clips[0]
        print(f"Clip Path: {clip_path}")
        
        if clip_path and Path(clip_path).exists():
            size = Path(clip_path).stat().st_size
            print(f"Clip Size: {size} bytes")
            if size > 10000:
                print("SUCCESS: Animation Clip Generated!")
            else:
                print("FAIL: Clip too small (empty?)")
        else:
            print("FAIL: Clip not created")

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
